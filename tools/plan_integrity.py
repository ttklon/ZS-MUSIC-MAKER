#!/usr/bin/env python3
"""Measure and validate the primary PLAN_v39 text without modifying it."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = ROOT / "docs" / "PLAN_v39_AI_MEGA.txt"
PRIMARY_STEP_PATTERN = re.compile(r"(?m)^ШАГ\s+(\d{3})\s+—\s+(.+?)\s*$")


def measure_plan(path: Path = DEFAULT_PLAN) -> dict[str, Any]:
    """Return reproducible text integrity evidence without altering the plan."""
    try:
        raw = Path(path).read_bytes()
        text = raw.decode("utf-8", errors="strict")
    except (OSError, UnicodeDecodeError) as exc:
        return {"ok": False, "path": str(path), "reason": str(exc)}

    steps = [int(number) for number, _title in PRIMARY_STEP_PATTERN.findall(text)]
    expected = list(range(1, 101))
    checks = {
        "utf8_strict": True,
        "newline_at_eof": text.endswith("\n"),
        "primary_steps_exact_001_to_100": steps == expected,
    }
    return {
        "ok": all(checks.values()),
        "path": str(path),
        "byte_size": len(raw),
        "character_count": len(text),
        "line_count": text.count("\n") + (1 if text and not text.endswith("\n") else 0),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "primary_step_count": len(steps),
        "first_step": steps[0] if steps else None,
        "last_step": steps[-1] if steps else None,
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate PLAN_v39 UTF-8 and primary step integrity")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN, help="Plan file to inspect")
    parser.add_argument("--json", action="store_true", help="Print structured evidence")
    args = parser.parse_args(argv)
    report = measure_plan(args.plan)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(
            f"plan integrity: steps={report.get('primary_step_count')} "
            f"bytes={report.get('byte_size')} sha256={report.get('sha256')}"
        )
        for name, passed in report.get("checks", {}).items():
            print(f"  {'PASS' if passed else 'FAIL'} {name}")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
