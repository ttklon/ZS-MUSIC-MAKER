# -*- coding: utf-8 -*-
"""
tools/gitignore_guard.py — не даёт .gitignore «съесть» код проекта.

Исторический инцидент: правило `release/` (артефакты рендера в корне)
молча игнорировало пакет `modules/release/`, и модуль выпадал из репозитория
целиком. Этот сторож видит такие случаи сразу:

    python tools/gitignore_guard.py           # человекочитаемый отчёт
    python tools/gitignore_guard.py --json    # машиночитаемо (exit 1 при находках)
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Каталоги, внутри которых живёт только код и данные проекта.
PROTECTED_ROOTS = (
    "app/",
    "agents/",
    "modules/",
    "tools/",
    "tests/",
    "ui/",
    "updater/",
    "config/",
    "docs/",
    "scripts/",
)


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    )
    return result.stdout if result.returncode == 0 else ""


def ignored_protected_paths() -> list[str]:
    """Пути внутри PROTECTED_ROOTS, которые git реально игнорирует (`!!`).

    Неотслеживаемые (`??`) файлы намеренно не считаются проблемой: их просто
    ещё не добавили в индекс.
    """
    output = _git("status", "--ignored", "--porcelain", "--untracked-files=all")
    hits: list[str] = []
    for line in output.splitlines():
        if not line.startswith("!! "):
            continue
        path = line[3:].strip()
        if path.startswith(PROTECTED_ROOTS) and not path.endswith("/__pycache__"):
            if "__pycache__" in path or path.endswith(".pyc"):
                continue
            hits.append(path)
    return sorted(hits)


def audit() -> dict[str, object]:
    hits = ignored_protected_paths()
    return {
        "ok": not hits,
        "ignored_protected_paths": hits,
        "protected_roots": list(PROTECTED_ROOTS),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Detect .gitignore rules that would silently hide project code"
    )
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    report = audit()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif report["ok"]:
        print("gitignore guard: CLEAN — ни один каталог с кодом не игнорируется")
    else:
        print("gitignore guard: FOUND — эти пути спрятаны .gitignore:")
        for path in report["ignored_protected_paths"]:
            print(f"  {path}")
        print("Исправьте шаблон на якорный (`/release/` вместо `release/`).")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
