"""Инструмент сверки снимка обязан ловить устаревание локально, а не в CI.

Два релиза подряд (42.0.17 и 42.0.18) красным в CI становился ровно один шаг —
«Regenerate readiness snapshot». Причина одна и та же: сверка шла только с
`HEAD`, поэтому после правки кода локально старый снимок и старый код в `HEAD`
совпадали, pytest был зелёным, а провал всплывал уже после пуша и тега.

Поэтому у инструмента два режима:
* `--tree` — снимок на диске против пересчёта по рабочему
  дереву. Именно это ловит забытый пересчёт ДО пуша;
* `--head` (по умолчанию) — снимок против закоммиченного. Это делает CI после пересчёта.

Здесь проверяется, что `--tree` реально сравнивает содержимое, а не
возвращает 0 всегда: испорченный снимок обязан дать код 1.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "check_snapshot_freshness.py"
READINESS = ROOT / "data" / "desktop" / "readiness.json"

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None, reason="пересчёт снимка требует Node.js"
)


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TOOL), *args], cwd=ROOT, capture_output=True, text=True
    )


def test_tree_mode_reports_fresh_snapshot():
    result = _run("--tree")
    assert result.returncode == 0, result.stdout + result.stderr


def test_tree_mode_detects_tampered_snapshot():
    """Ключевая проверка: инструмент не «всегда зелёный»."""
    backup = READINESS.read_bytes()
    try:
        data = json.loads(backup.decode("utf-8"))
        inventory = data.get("module_inventory") or {}
        inventory["tracked_modules"] = int(inventory.get("tracked_modules", 0)) + 777
        data["module_inventory"] = inventory
        READINESS.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        result = _run("--tree")
        assert result.returncode == 1, "испорченный снимок обязан считаться устаревшим"
        assert "module_inventory" in result.stdout
    finally:
        READINESS.write_bytes(backup)


def test_head_mode_is_available():
    """Режим сверки с коммитом остаётся для CI."""
    result = _run("--head")
    # 0 — снимок в коммите, 2 — нет git-истории, 1 — расхождение (допустимо
    # до коммита). Инструмент не должен падать.
    assert result.returncode in (0, 1, 2), result.stdout + result.stderr
