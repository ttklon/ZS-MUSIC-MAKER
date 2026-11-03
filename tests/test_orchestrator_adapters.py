# -*- coding: utf-8 -*-
"""God/async-входы — адаптеры над общим пайплайном, а не вторые пайплайны.

Исторически в проекте жили три независимых конвейера (classic / god / async):
свои порядки стадий, свои цели громкости и свои «бит-движки». Правки качества
до них не доезжали. Тесты ниже держат инвариант: оба входа обязаны вызывать
`run_full_pipeline`, а не собирать музыку сами.
"""

from __future__ import annotations

import ast
import asyncio
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
GOD = ROOT / "app" / "core" / "orchestrator_god.py"
ASYNC = ROOT / "app" / "core" / "orchestrator_async.py"

LEGACY_ENGINES = ("beat_constructor", "cyber_synth", "chanson_engine", "phonk_engine", "mastering_chain")


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            names.update(alias.name for alias in node.names)
            if node.module:
                names.add(node.module)
        elif isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
    return names


@pytest.mark.parametrize("path", [GOD, ASYNC])
def test_entrypoints_do_not_rebuild_their_own_pipeline(path: Path) -> None:
    imports = _imports(path)
    left = sorted(name for name in LEGACY_ENGINES if any(name in item for item in imports))
    assert not left, f"{path.name} снова собирает свой конвейер: {left}"


@pytest.mark.parametrize("path", [GOD, ASYNC])
def test_entrypoints_call_shared_pipeline(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    assert "run_full_pipeline(" in source
    # импорт должен быть локальным: иначе тест не может подменить пайплайн,
    # а собранный exe получает жёсткую связку на импорте конкретного модуля
    tree = ast.parse(source)
    module_level = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "app.core.orchestrator"
        for alias in node.names
    }
    assert "run_full_pipeline" not in module_level


def test_god_pipeline_sets_full_track_duration_and_maps_report(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """`--god` = общий пайплайн на 120 с + отчёт в старой форме."""
    from app.core import orchestrator, orchestrator_god

    captured: dict[str, Any] = {}

    def fake_pipeline(project_id, state, dry_run=False, out_root=None, **kwargs):
        captured.update({"state": dict(state), "out_root": out_root})
        return {
            "verdict": "PASS_WITH_FALLBACK",
            "percent": 88.0,
            "duration_sec": 12.5,
            "master_path": str(tmp_path / "master.wav"),
            "warnings": ["texture blocked"],
            "stages": [
                {"name": "_stage_voice_synth", "status": "BLOCKED", "reason": "no TTS"},
                {"name": "_stage_mastering", "status": "OK", "duration_sec": 1.0},
            ],
        }

    monkeypatch.setattr(orchestrator, "run_full_pipeline", fake_pipeline)
    result = orchestrator_god.run_god_pipeline("probe", None, out_root=tmp_path)

    assert captured["state"]["duration_sec"] == orchestrator_god.GOD_DURATION_SEC
    assert captured["state"]["genre"] == "drift_phonk"
    assert result["status"] == "completed"
    assert result["master_path"] == str(tmp_path / "master.wav")
    assert result["vocal_status"] == "BLOCKED"
    assert result["vocal_reason"] == "no TTS"
    assert result["stages"][0]["ok"] is True  # ok = «не FAILED», как раньше
    assert (tmp_path / "project_meta.json").exists()


def test_god_pipeline_failure_is_not_reported_as_completed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from app.core import orchestrator, orchestrator_god

    monkeypatch.setattr(
        orchestrator,
        "run_full_pipeline",
        lambda *a, **k: {"verdict": "PARTIAL", "stages": [], "master_path": None},
    )
    result = orchestrator_god.run_god_pipeline("probe", {"genre": "trap"}, out_root=tmp_path)
    assert result["status"] == "partial"
    assert result["master_path"] is None


def test_async_orchestrator_runs_shared_pipeline(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from app.core import orchestrator, orchestrator_async

    def fake_pipeline(project_id, state, dry_run=False, out_root=None, on_stage=None, **kwargs):
        for index, name in enumerate(("_stage_beat", "_stage_mastering"), start=1):
            on_stage(name, "OK", index, 2)
        return {"verdict": "PASS", "master_path": str(tmp_path / "master.wav")}

    monkeypatch.setattr(orchestrator, "run_full_pipeline", fake_pipeline)
    orch = orchestrator_async.AsyncOrchestrator("probe", tmp_path)
    result = asyncio.run(orch.run_pipeline({"genre": "phonk"}))

    assert result["status"] == "completed"
    assert [stage["name"] for stage in result["stages"]] == ["_stage_beat", "_stage_mastering"]
    assert result["master_path"] == str(tmp_path / "master.wav")
    assert (tmp_path / "async_meta.json").exists()


def test_async_orchestrator_reports_error_instead_of_lying(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from app.core import orchestrator, orchestrator_async

    def boom(*_a: Any, **_k: Any) -> dict[str, Any]:
        raise RuntimeError("disk full")

    monkeypatch.setattr(orchestrator, "run_full_pipeline", boom)
    result = asyncio.run(orchestrator_async.AsyncOrchestrator("probe", tmp_path).run_pipeline({}))
    assert result["status"] == "partial"
    assert "disk full" in (result["error"] or "")
