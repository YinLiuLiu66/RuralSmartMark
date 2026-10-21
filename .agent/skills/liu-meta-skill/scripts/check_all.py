#!/usr/bin/env python3
"""Run the mechanical checks for a DSH skill.

Pass a skill directory (default: this one). The checker scripts are taken from
this package, so the target does not need its own scripts/.

Directory-bundle skills only (`<name>/SKILL.md`); flat `<name>.md` is not
supported.

Each check reports `pass` or `fail`; `ok` is true when none failed. It does not
judge whether the skill is useful. That needs real tasks.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent


def run_json(script: Path, target: Path) -> dict:
    proc = subprocess.run([sys.executable, str(script), str(target)], capture_output=True, text=True)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {
            "ok": False,
            "failures": [f"{script.name}: non-JSON output (exit {proc.returncode})"],
            "warnings": [],
        }


def main() -> None:
    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if target.is_file():
        problem = f"flat skill files are not supported: {target.name}; wrap it as <name>/SKILL.md"
    elif not (target / "SKILL.md").exists():
        problem = "Missing SKILL.md"
    else:
        problem = None
    if problem is not None:
        print(
            json.dumps(
                {
                    "ok": False,
                    "skill": target.name,
                    "summary": {"ran": 0, "failed": 1},
                    "checks": [],
                    "failures": [problem],
                    "warnings": [],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        raise SystemExit(2)

    failures: list[str] = []
    warnings: list[str] = []
    checks: list[dict] = []

    def add(
        name: str,
        status: str,
        *,
        failures: list[str] | None = None,
        warnings: list[str] | None = None,
        **extra: object,
    ) -> None:
        entry: dict = {"name": name, "status": status}
        if failures:
            entry["failures"] = failures
        if warnings:
            entry["warnings"] = warnings
        entry.update(extra)
        checks.append(entry)

    for name in ("check_skill.py", "lint_skill.py"):
        data = run_json(SCRIPTS / name, target)
        item_failures = list(data.get("failures", []))
        item_warnings = list(data.get("warnings", []))
        add(name, "pass" if data.get("ok") else "fail", failures=item_failures, warnings=item_warnings)
        failures.extend(f"{name}: {item}" for item in item_failures)
        warnings.extend(f"{name}: {item}" for item in item_warnings)

    size_proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "context_sizer.py"), str(target), "--json"],
        capture_output=True,
        text=True,
    )
    try:
        size = json.loads(size_proc.stdout)
    except json.JSONDecodeError:
        size = None
        message = f"context_sizer.py: non-JSON output (exit {size_proc.returncode})"
        add("context_sizer.py", "fail", failures=[message])
        failures.append(message)

    initial = None
    if size is not None:
        initial = size.get("estimated_initial_load_tokens")
        size_warnings: list[str] = []
        if size.get("warning"):
            size_warnings.append(f"initial load is {initial} tokens (> 2000)")
        non_english = size.get("non_english") or {}
        if non_english.get("warning"):
            size_warnings.append(
                f"non-English content: {non_english.get('cjk_ratio', 0):.0%} CJK;"
                " the token estimate assumes English and may undercount 2-4x"
            )
        add(
            "context_sizer.py",
            "pass",
            warnings=size_warnings,
            initial_load_tokens=initial,
            tiers=size.get("tiers"),
            non_english=size.get("non_english"),
            platform=size.get("platform"),
        )
        warnings.extend(size_warnings)

    failed = [c["name"] for c in checks if c["status"] == "fail"]
    report = {
        "ok": not failures,
        "summary": {"ran": len(checks), "failed": len(failed)},
        "failed": failed,
        "skill": target.name,
        "path": str(target),
        "initial_load_tokens": initial,
        "checks": checks,
        "failures": failures,
        "warnings": warnings,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if not failures else 2)


if __name__ == "__main__":
    main()
