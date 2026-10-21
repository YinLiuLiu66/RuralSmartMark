#!/usr/bin/env python3
"""Refuse a description change that makes routing worse.

Why: an improver loop without a fixed case set is an optimizer fitting noise.
This script compares the old and new trigger description against labeled cases
and reports what regressed. It needs cases; with none it refuses (exit 2)
instead of pretending the change is safe.

The scorer is deliberately simple: vocabulary overlap with negation awareness.
Read a regression as "this edit weakened a known trigger or leaked into an
excluded one" -- not as proof of how a model will route.

Stdlib only. Accepted description forms: single-line (plain or quoted) and
block scalars (`>`, `|`, with optional `-`/`+`). Other YAML forms are rejected
rather than guessed. --cases accepts a JSON array or JSONL.

Exit codes: 0 no regression, 1 regression found, 2 cannot evaluate.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

WORD_RE = re.compile(r"[a-z0-9]+")
CJK_RE = re.compile(r"[\u4e00-\u9fff]+")
NEG_RE = re.compile(r"(?:不用于|不适用于|不接|不做|不生成|排除|except|exclude[sd]?|not for)\s*([^。；;\n]{0,60})")

TOLERANCE = 0.05

STOP = frozenset(
    """
    the and for with from that this you your use used when into only are not but can
    will they them their has have was were its our out all any per via skill skills
    这个 那个 一个 我们 可以 什么 怎么 时候 一下 帮我
    """.split()
)


class InputError(Exception):
    """The inputs cannot be evaluated; report it instead of guessing."""


def tokens(text: str) -> set:
    """Latin words plus CJK bigrams. Bigrams keep Chinese matching local."""
    lowered = text.lower()
    latin = {w for w in WORD_RE.findall(lowered) if len(w) > 1 and w not in STOP}
    grams = set()
    for run in CJK_RE.findall(lowered):
        if len(run) == 1:
            grams.add(run)
            continue
        for i in range(len(run) - 1):
            grams.add(run[i : i + 2])
    return {t for t in latin | grams if t not in STOP}


def split_description(description: str) -> tuple:
    """Separate claimed vocabulary from explicitly excluded vocabulary.

    Exclusions matter: writing "not for translation" must not make translation
    requests look like a match.
    """
    excluded = set()
    for match in NEG_RE.finditer(description):
        excluded |= tokens(match.group(1))
    return tokens(description) - excluded, excluded


def score(case_text: str, description: str) -> float:
    case_tokens = tokens(case_text)
    if not case_tokens:
        return 0.0
    claimed, excluded = split_description(description)
    if not claimed and not excluded:
        return 0.0
    claimed_cover = len(case_tokens & claimed) / len(case_tokens)
    excluded_cover = len(case_tokens & excluded) / len(case_tokens)
    return round(max(0.0, claimed_cover - 0.6 * excluded_cover), 4)


def block_scalar(lines: list[str], key_indent: int, folded: bool) -> str:
    block: list[str] = []
    for line in lines:
        if not line.strip():
            block.append("")
            continue
        indent = len(line) - len(line.lstrip())
        if indent <= key_indent:
            break
        block.append(line.strip())
    while block and not block[0]:
        block.pop(0)
    while block and not block[-1]:
        block.pop()
    if not block:
        return ""
    if not folded:
        return "\n".join(block)
    paragraphs: list[str] = []
    current: list[str] = []
    for line in block:
        if line:
            current.append(line)
        elif current:
            paragraphs.append(" ".join(current))
            current = []
    if current:
        paragraphs.append(" ".join(current))
    return "\n".join(paragraphs)


def read_description(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return text.strip()
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise InputError(f"{path.name}: frontmatter is not closed with ---")
    lines = parts[1].splitlines()
    for index, line in enumerate(lines):
        if not line.lstrip().startswith("description:"):
            continue
        key_indent = len(line) - len(line.lstrip())
        value = line.split(":", 1)[1].strip()
        if value in {"", ">", "|", ">-", "|-", ">+", "|+"}:
            block = block_scalar(lines[index + 1 :], key_indent, folded=not value.startswith("|"))
            if not block.strip():
                raise InputError(f"{path.name}: description is empty")
            return block
        if value[0] in "'\"":
            return value.strip("'\"")
        if value.startswith(("&", "*", "[", "{")) or value.count('"') % 2 or value.count("'") % 2:
            raise InputError(f"{path.name}: unsupported description form: {value[:40]!r}")
        return value
    raise InputError(f"{path.name}: frontmatter has no description")


def load_cases(path: Path) -> list:
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return []
    if raw.startswith("["):
        try:
            items = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise InputError(
                f"{path}: invalid JSON array ({exc.msg} at line {exc.lineno} column {exc.colno})"
            )
        if not isinstance(items, list):
            raise InputError(f"{path}: top-level JSON must be an array or JSONL")
    else:
        items = []
        for lineno, line in enumerate(raw.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise InputError(f"{path}: line {lineno}: {exc.msg} at column {exc.colno}")
    cases = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict) or not item.get("text"):
            raise InputError(f"{path}: case {index} needs a non-empty 'text' field")
        should = item.get("should")
        if should is None and item.get("expect") in ("trigger", "no_trigger"):
            should = item["expect"] == "trigger"
        if not isinstance(should, bool):
            raise InputError(f"{path}: case {index} needs a boolean 'should' (true = must trigger)")
        cases.append({"text": item["text"], "should": should, "family": item.get("family", "")})
    return cases


def score_all(cases: list, description: str) -> list:
    return [
        {
            "text": case["text"],
            "family": case["family"],
            "should": case["should"],
            "score": score(case["text"], description),
        }
        for case in cases
    ]


def fail(message: str, **extra: object) -> None:
    payload: dict = {"ok": False, "failures": [message]}
    payload.update(extra)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(2)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare an old and new trigger description against labeled cases."
    )
    parser.add_argument("skill_dir")
    parser.add_argument("--baseline", required=True, help="previous SKILL.md or description file")
    parser.add_argument("--current", help="proposed description file (default: <skill>/SKILL.md)")
    parser.add_argument("--cases", help="cases file (default: <skill>/evals/trigger-cases.jsonl)")
    parser.add_argument("--tolerance", type=float, default=TOLERANCE)
    args = parser.parse_args()

    root = Path(args.skill_dir).resolve()
    skill_md = root / "SKILL.md"
    if not skill_md.exists():
        fail("Missing SKILL.md")

    baseline_path = Path(args.baseline).resolve()
    if not baseline_path.exists():
        fail(f"baseline not found: {baseline_path}")
    current_path = Path(args.current).resolve() if args.current else skill_md
    if not current_path.exists():
        fail(f"current description not found: {current_path}")

    cases_path = Path(args.cases) if args.cases else root / "evals" / "trigger-cases.jsonl"
    if not cases_path.exists():
        fail(
            f"No cases: {cases_path}",
            hint="先写 3-5 条真实请求（该触发/不该触发各若干），再做自动改进。没有用例就没有回归基线。",
        )

    try:
        cases = load_cases(cases_path)
    except InputError as exc:
        fail(str(exc), hint="修好用例文件再跑；没有解析成功的用例就不算验过。")
    if not cases:
        fail("Cases file is empty", hint="至少要有 3 条正例和负例。")

    try:
        before = score_all(cases, read_description(baseline_path))
        after = score_all(cases, read_description(current_path))
    except InputError as exc:
        fail(str(exc), hint="只接受单行 description 或块标量（>、|）；其他 YAML 形式不猜。")

    regressions = []
    improvements = []
    for old, new in zip(before, after):
        delta = round(new["score"] - old["score"], 4)
        entry = {
            "text": new["text"],
            "family": new["family"],
            "should": new["should"],
            "baseline_score": old["score"],
            "current_score": new["score"],
            "delta": delta,
        }
        # A should-trigger case must not weaken; an excluded case must not leak in.
        if (new["should"] and delta < -args.tolerance) or (not new["should"] and delta > args.tolerance):
            regressions.append(entry)
        elif new["should"] and delta > args.tolerance:
            improvements.append(entry)

    weak = [item["text"] for item in before if item["should"] and item["score"] < 0.12]

    report = {
        "ok": not regressions,
        "skill": skill_md.parent.name,
        "cases": len(cases),
        "tolerance": args.tolerance,
        "regressions": regressions,
        "improvements": improvements,
        "weak_baseline_cases": weak,
        "note": "词面重叠的回归探针，不是路由判定器；它只能回答「这次改动有没有让已知用例变差」。",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if regressions:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
