# -*- coding: utf-8 -*-
"""Electron-оболочка: её тесты запускаются из общего прогона pytest.

Зачем: `pytest tests/` — единственная точка, которую запускают и CI, и
человек. Если JS-тесты живут отдельно, они тихо перестают запускаться.
Здесь они вызываются через `node --test`; отсутствие Node — не провал, но и
не «успех»: тест помечается пропущенным с причиной.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DESKTOP = ROOT / "desktop"

NODE = shutil.which("node")


def _run_node(args: list[str], timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(
        [NODE, *args],
        cwd=DESKTOP,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


@pytest.mark.skipif(NODE is None, reason="Node.js не установлен в окружении")
def test_shell_sources_parse() -> None:
    files = [
        "electron/main.js",
        "electron/preload.js",
        "electron/tasks.js",
        "electron/runtime.js",
        "electron/pipeline.js",
        "electron/render-host.js",
        "electron/render-worker.js",
        "electron/beat-service.js",
        "electron/settings.js",
        "src/app.js",
        "src/sections/overview.js",
        "src/sections/genres.js",
        "src/sections/beat.js",
        "src/sections/dossiers.js",
        "src/sections/run.js",
        "src/sections/health.js",
        "src/core/project.js",
        "src/core/catalog.js",
        "src/core/readiness.js",
        "src/core/fs-node.js",
        "scripts/snapshot-readiness.js",
    ]
    for name in files:
        assert (DESKTOP / name).is_file(), f"нет файла оболочки: {name}"
        result = _run_node(["--check", name], timeout=60)
        assert result.returncode == 0, f"{name}: {result.stderr[-800:]}"


@pytest.mark.skipif(NODE is None, reason="Node.js не установлен в окружении")
def test_shell_suite_passes() -> None:
    files = sorted(f"test/{p.name}" for p in (DESKTOP / "test").glob("*.test.js"))
    assert files, "в desktop/test нет ни одного файла *.test.js"
    run = _run_node(["--test", *files])
    assert run.returncode == 0, (
        "JS-тесты оболочки упали:\n" + run.stdout[-3000:] + run.stderr[-2000:]
    )
    assert "# fail 0" in run.stdout, run.stdout[-1500:]


@pytest.mark.skipif(NODE is None, reason="Node.js не установлен в окружении")
def test_snapshot_files_are_committed_and_fresh() -> None:
    readiness = ROOT / "data" / "desktop" / "readiness.json"
    inventory = ROOT / "data" / "desktop" / "inventory.md"
    assert readiness.is_file() and inventory.is_file(), (
        "снимок не сгенерирован: node desktop/scripts/snapshot-readiness.js"
    )

    payload = json.loads(readiness.read_text(encoding="utf-8"))
    assert isinstance(payload.get("percent"), (int, float))
    assert payload.get("generated_at"), "у снимка нет даты — окно не заметит устаревание"
    assert payload.get("module_inventory", {}).get("tracked_modules", 0) > 0
    assert payload.get("caps_triggered"), "потолки обязаны быть перечислены"

    rows = [line for line in inventory.read_text(encoding="utf-8").splitlines() if line.startswith("| ")]
    assert len(rows) > 100, f"в inventory всего {len(rows)} строк"


@pytest.mark.skipif(NODE is None, reason="Node.js не установлен в окружении")
def test_readiness_js_matches_python_snapshot() -> None:
    """Сверка расчёта: JS-окно и Python-эталон должны давать одно число."""
    readiness = ROOT / "data" / "desktop" / "readiness.json"
    if not readiness.is_file():
        pytest.skip("снимок не сгенерирован")

    script = (
        "const {computeReadiness}=require('./src/core/readiness');"
        "const s=require('../data/desktop/readiness.json');"
        "const r=computeReadiness({probes:s.raw_probes,inventory:s.module_inventory});"
        "console.log(JSON.stringify({percent:r.percent,blocks:r.blockScores,caps:r.capsTriggered}));"
    )
    result = _run_node(["-e", script], timeout=60)
    assert result.returncode == 0, result.stderr[-800:]

    js = json.loads(result.stdout)
    snapshot = json.loads(readiness.read_text(encoding="utf-8"))

    assert js["percent"] == snapshot["percent"], (
        f"JS={js['percent']}%, Python={snapshot['percent']}% — формулы разошлись"
    )
    for block, value in snapshot["block_scores"].items():
        assert js["blocks"][block] == value, f"блок {block}: JS={js['blocks'][block]} Python={value}"


def test_snapshot_freshness_tool_detects_stale_snapshot(tmp_path, monkeypatch) -> None:
    """Инструмент сверки снимка обязан ругаться на устаревшие данные.

    Он стоит в CI, поэтому «зелёный» на любом входе был бы хуже, чем его
    отсутствие: оба случая — испорченный снимок и совпадающий — проверяются
    на копии файла, настоящий репозиторий не трогается.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "check_snapshot_freshness", ROOT / "tools" / "check_snapshot_freshness.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    monkeypatch.setattr(module, "ROOT", tmp_path)
    (tmp_path / "data" / "desktop").mkdir(parents=True)
    snapshot = tmp_path / "data" / "desktop" / "readiness.json"
    inventory = tmp_path / "data" / "desktop" / "inventory.md"
    # Проценты могут законно отличаться (разные пакеты в окружении), а состав
    # модулей и потолки — нет: именно они и должны ловить устаревший снимок.
    snapshot.write_text(
        json.dumps(
            {
                "percent": 65,
                "generated_at": "2026-01-01T00:00:00Z",
                "module_inventory": {"tracked_modules": 300},
                "caps_triggered": [["65", "heavy engines unavailable"]],
            }
        ),
        encoding="utf-8",
    )
    inventory.write_text("| header |\n", encoding="utf-8")
    monkeypatch.setattr(module, "SNAPSHOT", snapshot)
    monkeypatch.setattr(module, "INVENTORY", inventory)
    monkeypatch.setattr(
        module,
        "committed",
        lambda path: json.dumps(
            {
                "percent": 42,
                "generated_at": "2025-01-01T00:00:00Z",
                "module_inventory": {"tracked_modules": 299},
                "caps_triggered": [["65", "heavy engines unavailable"]],
            }
        )
        if path.name == "readiness.json"
        else "| header |\n",
    )

    assert module.main() == 1, "расхождение состава модулей должно быть замечено"
