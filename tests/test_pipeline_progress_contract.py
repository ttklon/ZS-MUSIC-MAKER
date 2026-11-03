# -*- coding: utf-8 -*-
"""Контракт прогресса: колбэк получает каждую стадию по порядку.

GUI не должен показывать фальшивую полоску «0.1 → 0.92». Проверяем на
заглушках стадий (без аудио), что `on_stage` вызывается ровно столько раз,
сколько записей в пайплайне, индексы растут, а `total` не меняется.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from app.core import orchestrator
from app.pipeline import StageResult, StageStatus


def _ok(name: str, payload: dict[str, Any] | None = None) -> StageResult:
    return StageResult(name=name, status=StageStatus.OK, output=payload or {})


@pytest.fixture()
def stubbed_pipeline(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Подменяем тяжёлые стадии на мгновенные заглушки."""
    out_dir = tmp_path / "run"
    out_dir.mkdir()

    monkeypatch.setattr(orchestrator, "_stage_analyze", lambda *a, **k: {"bpm": 120})
    monkeypatch.setattr(orchestrator, "_stage_groove", lambda *a, **k: {"swing": 0.1})
    monkeypatch.setattr(orchestrator, "_stage_arrangement", lambda *a, **k: {"sections": []})
    monkeypatch.setattr(orchestrator, "_stage_beat", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(orchestrator, "_stage_texture", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(
        orchestrator,
        "_run_lyrics_stage",
        lambda recipe: (_ok("_stage_lyrics"), {"text": "a\nb"}, "a\nb"),
    )
    monkeypatch.setattr(
        orchestrator,
        "_run_vocal_chain",
        lambda *a, **k: (
            [_ok("_stage_voice_synth"), _ok("_stage_rvc"), _ok("_stage_vocal_fx")],
            {"vocals": None},
            ["voice: BLOCKED (stub)"],
        ),
    )
    monkeypatch.setattr(orchestrator, "_stage_mix_and_sidechain", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(orchestrator, "_stage_mastering", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(orchestrator, "_stage_polish", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(orchestrator, "_stage_stems", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(orchestrator, "_stage_hit_score", lambda *a, **k: {"score": 80})
    monkeypatch.setattr(orchestrator, "_stage_release_pack", lambda *a, **k: {"ok": True})
    return out_dir


def test_on_stage_reports_every_record_exactly_once(stubbed_pipeline: Path) -> None:
    events: list[tuple[str, str, int, int]] = []
    orchestrator.run_full_pipeline(
        "progress_probe",
        {"genre": "drift_phonk", "theme": "тест", "duration_sec": 4},
        dry_run=True,
        out_root=stubbed_pipeline,
        on_stage=lambda *a: events.append(a),
    )
    assert [e[0] for e in events] == list(orchestrator.STAGE_RECORDS)
    assert [e[2] for e in events] == list(range(1, len(events) + 1))
    assert len({e[3] for e in events}) == 1, "total должен быть постоянным"
    assert events[-1][3] == len(orchestrator.STAGE_RECORDS)


def test_stage_records_are_unique(stubbed_pipeline: Path) -> None:
    assert len(set(orchestrator.STAGE_RECORDS)) == len(orchestrator.STAGE_RECORDS)


def test_progress_callback_errors_do_not_break_run(stubbed_pipeline: Path) -> None:
    """Упавший колбэк GUI не должен ронять рендер трека."""
    def boom(*_a: Any) -> None:
        raise RuntimeError("gui gone")

    result = orchestrator.run_full_pipeline(
        "progress_probe_bad_cb",
        {"genre": "drift_phonk", "theme": "тест"},
        dry_run=True,
        out_root=stubbed_pipeline,
        on_stage=boom,
    )
    assert result.get("verdict") in {"PASS", "FALLBACK", "PARTIAL"}
    assert any("progress callback failed" in w for w in result.get("warnings", []))


def test_recipe_only_is_honoured(stubbed_pipeline: Path) -> None:
    """`only` из рецепта превращается в BLOCKED для остальных стадий."""
    calls: list[str] = []
    orchestrator_analyze = orchestrator._stage_analyze
    orchestrator._stage_analyze = lambda *a, **k: calls.append("analysis") or {"bpm": 120}  # type: ignore[assignment]
    try:
        result = orchestrator.run_full_pipeline(
            "only_probe",
            {"genre": "drift_phonk", "theme": "тест", "only": ["master", "mix"]},
            dry_run=True,
            out_root=stubbed_pipeline,
        )
    finally:
        orchestrator._stage_analyze = orchestrator_analyze  # type: ignore[assignment]

    assert calls == [], "analysis не запрашивался — стадия должна быть BLOCKED"
    names = {s["name"]: s["status"] for s in result["stages"]}
    assert names["_stage_analyze"] == "BLOCKED"
