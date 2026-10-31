# -*- coding: utf-8 -*-
"""
tools/readiness/cli.py — отчёт для человека, JSON-режим и матрица модулей.
"""

from __future__ import annotations

import argparse
import json
from importlib import metadata

from tools.readiness.inventory import inventory_markdown, module_inventory
from tools.readiness.paths import ROOT
from tools.readiness.scoring import compute


def dependency_requirements() -> list[dict[str, str]]:
    """Разбирает манифесты зависимостей без их резолва (для отчётов)."""
    groups = (
        ("base", ROOT / "requirements.txt"),
        ("optional-ai", ROOT / "requirements_ai.txt"),
    )
    entries: dict[str, dict[str, str]] = {}
    for group, path in groups:
        if not path.exists():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("git+"):
                name = "bark" if "suno-ai/bark" in line.lower() else line.rsplit("/", 1)[-1]
            else:
                name = line.split(";")[0].split(">=")[0].split("==")[0].split("<")[0].strip()
            entries[name] = {"group": group, "spec": line}
    return [{"name": name, **spec} for name, spec in sorted(entries.items())]


def installed_version(package: str) -> str:
    try:
        return metadata.version(package)
    except Exception:
        return ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compute factual ZS Music Maker readiness")
    parser.add_argument(
        "--inventory-markdown",
        action="store_true",
        help="render the tracked Python module matrix as Markdown",
    )
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    if args.inventory_markdown:
        print(inventory_markdown())
        return 0

    percent, details = compute()
    if args.json:
        print(json.dumps({"percent": percent, **details}, ensure_ascii=False, indent=2))
        return 0

    print(f"readiness: {percent:.0f}%")
    for block, value in details["block_scores"].items():
        print(f"  {block:18s} {value:6.2f}%")
    for cap_value, reason in details["caps_triggered"]:
        print(f"  cap <= {cap_value:.0f}%: {reason}")
    missing = [row["path"] for row in module_inventory() if row["status"] != "REAL_PASS"]
    if missing:
        print("  modules without static signal: " + ", ".join(missing))
    return 0
