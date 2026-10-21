#!/usr/bin/env python3
"""Estimate context size for a skill package.

Initial load is what the `skill` tool actually injects: the SKILL.md body
(frontmatter is not injected), regardless of SKILL.example.md.
Budgets are estimated tokens; the report also states where the estimate sits
relative to each tier and whether the package is non-English.

Directory-bundle skills only (`<name>/SKILL.md`); flat `<name>.md` is not
supported.
"""
import argparse
import json
import re
from pathlib import Path

from limits import BODY_LIMIT, INITIAL_LOAD_WARN, TIERS


TEXT_EXTS = {".css", ".md", ".txt", ".yaml", ".yml", ".json", ".py", ".sh", ".js", ".ts"}
CJK_RE = re.compile(r"[\u4e00-\u9fff]")
CJK_RATIO_WARN = 0.2
# Only the directories this edition actually produces. Upstream's reports/,
# tests/, input/, outputs/, agents/ and manifest.json are gone.
PACKAGE_PATHS = (
    "SKILL.md",
    "SKILL.example.md",
    "references",
    "scripts",
    "assets",
    "evals",
    "templates",
)


def estimate_tokens(text: str) -> int:
    # Fast heuristic suitable for local gating. English-calibrated: ~4 chars
    # per token. CJK content is reported separately instead of rescaling.
    return max(1, len(text) // 4)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def body_text(path: Path) -> str:
    """Return the part the skill tool injects: everything after the frontmatter."""
    text = read_text(path)
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            return parts[2]
    return text


def classify(path: Path) -> str:
    parts = set(path.parts)
    if path.name == "SKILL.md":
        return "skill_body"
    if "references" in parts:
        return "reference"
    if "scripts" in parts:
        return "script"
    if "assets" in parts:
        return "asset"
    if path.suffix in TEXT_EXTS:
        return "other_text"
    return "binary_or_other"


def summarize(skill_dir: Path) -> dict:
    files: list[dict] = []
    total_tokens = 0
    initial_tokens = 0
    body_chars = 0
    cjk_ratio = 0.0
    skill_md = skill_dir / "SKILL.md"

    candidate_files: list[Path] = []
    for entry in PACKAGE_PATHS:
        path = skill_dir / entry
        if path.is_file():
            candidate_files.append(path)
        elif path.is_dir():
            candidate_files.extend(sorted(file for file in path.rglob("*") if file.is_file()))

    for path in candidate_files:
        if path == skill_md:
            body = body_text(path)
            tokens = estimate_tokens(body)
            body_chars = len(body)
            cjk = len(CJK_RE.findall(body))
            cjk_ratio = round(cjk / body_chars, 3) if body_chars else 0.0
            files.append(
                {
                    "path": "SKILL.md",
                    "kind": "skill_body",
                    "chars": body_chars,
                    "estimated_tokens": tokens,
                    "cjk_ratio": cjk_ratio,
                }
            )
            total_tokens += tokens
            initial_tokens += tokens
            continue

        rel = path.relative_to(skill_dir)
        if path.suffix not in TEXT_EXTS:
            files.append({"path": str(rel), "kind": "binary_or_other", "bytes": path.stat().st_size})
            continue

        text = read_text(path)
        tokens = estimate_tokens(text)
        files.append({"path": str(rel), "kind": classify(rel), "chars": len(text), "estimated_tokens": tokens})
        total_tokens += tokens

    return {
        "skill_dir": str(skill_dir),
        "estimated_initial_load_tokens": initial_tokens,
        "estimated_total_text_tokens": total_tokens,
        "warning": initial_tokens > INITIAL_LOAD_WARN,
        "tiers": {
            name: {"budget": budget, "status": "over" if initial_tokens > budget else "within"}
            for name, budget in TIERS.items()
        },
        "non_english": {"cjk_ratio": cjk_ratio, "warning": cjk_ratio >= CJK_RATIO_WARN},
        "platform": {"body_chars": body_chars, "body_limit": BODY_LIMIT},
        "files": files,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Estimate context size for a skill package.")
    parser.add_argument("skill_dir", help="Path to the skill directory")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    report = summarize(Path(args.skill_dir).resolve())
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    print(f"Skill: {report['skill_dir']}")
    print(f"Estimated initial-load tokens: {report['estimated_initial_load_tokens']}")
    for name, tier in report["tiers"].items():
        print(f"  {name:10} {tier['budget']:5}  {tier['status']}")
    if report["non_english"]["warning"]:
        print(
            "Non-English content: "
            f"{report['non_english']['cjk_ratio']:.0%} CJK; the estimate assumes ~4 chars/token"
            " and may undercount 2-4x"
        )
    print(
        f"Body: {report['platform']['body_chars']} chars (limit {report['platform']['body_limit']};"
        " the rendered result must stay under 8192)"
    )
    print(f"Estimated total text tokens: {report['estimated_total_text_tokens']}")
    print("")
    for file in report["files"]:
        if "estimated_tokens" in file:
            print(f"{file['kind']:12} {file['estimated_tokens']:6}t  {file['path']}")
        else:
            print(f"{file['kind']:12} {file['bytes']:6}b  {file['path']}")


if __name__ == "__main__":
    main()
