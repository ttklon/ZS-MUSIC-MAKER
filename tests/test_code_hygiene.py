# -*- coding: utf-8 -*-
"""Гигиена кода: размеры файлов и отсутствие legacy-имён.

План §5.1 требует держать файлы читаемыми (≤ 400 строк) и не возвращать
`*_vN`-модули. Правило легко нарушить незаметно — этот тест его держит.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_LINES = 400
PRODUCTION_DIRS = ("app", "modules", "agents", "tools", "updater", "ui")
ROOT_FILES = ("main.py", "install.py")


def _tracked_python() -> list[str]:
    try:
        out = subprocess.run(
            ["git", "ls-files", "*.py"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        )
        files = [line.strip() for line in out.stdout.splitlines() if line.strip()]
    except (OSError, subprocess.CalledProcessError):  # pragma: no cover - git отсутствует
        files = [str(p.relative_to(ROOT)) for p in ROOT.rglob("*.py")]
    return [f for f in files if (ROOT / f).is_file()]


def _is_production(path: str) -> bool:
    return path in ROOT_FILES or path.split("/", 1)[0] in PRODUCTION_DIRS


def test_production_files_stay_readable() -> None:
    too_long = []
    for path in _tracked_python():
        if not _is_production(path):
            continue
        lines = len((ROOT / path).read_text(encoding="utf-8", errors="replace").splitlines())
        if lines > MAX_LINES:
            too_long.append(f"{path}: {lines}")
    assert not too_long, "файлы длиннее {} строк: {}".format(MAX_LINES, ", ".join(too_long))


def test_no_versioned_legacy_modules() -> None:
    suspicious = [
        path for path in _tracked_python()
        if any(part.startswith(("_v", "patch_")) and part[:3] in {"_v1", "_v2", "_v3", "_v4", "_v5", "_v6", "_v7", "_v8", "_v9"}
               for part in Path(path).stem.split("_"))
        or "_v8" in Path(path).stem or "_v9" in Path(path).stem
    ]
    assert not suspicious, f"legacy-модули вернулись: {suspicious}"


def test_single_mastering_implementation() -> None:
    """Мастеринг живёт в одном месте: пакет `modules/mastering`."""
    assert (ROOT / "modules" / "mastering" / "__init__.py").exists()
    assert not (ROOT / "modules" / "mastering.py").exists()
