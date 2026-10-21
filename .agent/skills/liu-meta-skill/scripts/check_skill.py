#!/usr/bin/env python3
"""Check a single-target skill package for the failures that actually happen.

Stdlib only. Validates frontmatter shape, kebab-case name, description quality,
referenced paths, and body budget.

Directory-bundle skills only (`<name>/SKILL.md`); flat `<name>.md` is not
supported.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from limits import BODY_LIMIT, BODY_WARN, DESCRIPTION_MAX, DESCRIPTION_WARN

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REF_RE = re.compile(r"`((?:references|scripts|assets)/[^`\s]+)`")
DESC_MIN = 20
DESC_WARN = DESCRIPTION_WARN
DESC_MAX = DESCRIPTION_MAX


def parse_frontmatter(text: str) -> tuple[dict[str, str] | None, str | None]:
    if not text.startswith("---"):
        return None, "SKILL.md must start with YAML frontmatter"
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, "frontmatter is not closed with ---"
    data: dict[str, str] = {}
    for line in parts[1].splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        data[key] = value
    return data, None


def main() -> None:
    parser = argparse.ArgumentParser(description="Check a skill package.")
    parser.add_argument("skill_dir")
    args = parser.parse_args()

    root = Path(args.skill_dir).resolve()
    failures: list[str] = []
    warnings: list[str] = []
    skill_md = root / "SKILL.md"

    if root.is_file():
        print(
            json.dumps(
                {
                    "ok": False,
                    "failures": [
                        f"flat skill files are not supported: {root.name}; wrap it as <name>/SKILL.md"
                    ],
                    "warnings": [],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        raise SystemExit(2)

    if not skill_md.exists():
        print(json.dumps({"ok": False, "failures": ["Missing SKILL.md"], "warnings": []}, ensure_ascii=False, indent=2))
        raise SystemExit(2)

    text = skill_md.read_text(encoding="utf-8")
    data, error = parse_frontmatter(text)
    if error:
        failures.append(error)
    else:
        assert data is not None
        name = data.get("name", "")
        description = data.get("description", "")
        if not name:
            failures.append("Missing frontmatter field: name")
        elif not NAME_RE.match(name):
            failures.append(f"name must be kebab-case: {name!r}")
        elif name != root.name:
            warnings.append(f"name {name!r} differs from directory {root.name!r}")
        if not description:
            failures.append("Missing frontmatter field: description")
        else:
            if len(description) < DESC_MIN:
                warnings.append("description is very short; trigger surface may be weak")
            if len(description) > DESC_MAX:
                failures.append(
                    f"description is {len(description)} chars (> {DESC_MAX}); DSH truncates the catalog"
                    f" entry to {DESC_MAX - 3} chars + '...', and the tail is where exclusions usually live"
                )
            elif len(description) > DESC_WARN:
                warnings.append(
                    f"description is {len(description)} chars; keep <= {DESC_WARN} for margin"
                )

    body = text.split("---", 2)[2] if text.count("---") >= 2 else text
    if len(body) > BODY_LIMIT:
        failures.append(
            f"body is {len(body)} chars (> {BODY_LIMIT}); the rendered skill result would exceed the"
            f" 8192-char tool-result pruner threshold and lose its middle"
        )
    elif len(body) > BODY_WARN:
        warnings.append(
            f"body is {len(body)} chars (> {BODY_WARN}); the rendered result is close to the 8192-char"
            " pruner threshold"
        )

    for ref in sorted(set(REF_RE.findall(text))):
        if not (root / ref).exists():
            failures.append(f"referenced path does not exist: {ref}")

    print(json.dumps({"ok": not failures, "failures": failures, "warnings": warnings}, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
