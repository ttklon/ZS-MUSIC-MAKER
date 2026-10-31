"""Детерминизм по seed, частичный прогон (`only`) и возобновление (`resume`).

Гейт из плана: «seed → идентичный SHA-256 артефакта». Проверяем на самой
дорогой и самой чувствительной к ГПСЧ стадии — бите.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from app.core.orchestrator import run_full_pipeline


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _beat_run(tmp_path: Path, project: str, seed: int) -> dict:
    return run_full_pipeline(
        project,
        {"genre": "drift_phonk", "theme": "night drive", "seed": seed, "duration_sec": 12},
        out_root=tmp_path / project,
        only={"arrangement", "beat"},
    )


def test_same_seed_produces_identical_beat_artefact(tmp_path: Path) -> None:
    first = _beat_run(tmp_path, "seed_a", 4242)
    second = _beat_run(tmp_path, "seed_b", 4242)

    assert first["seed"] == second["seed"] == 4242
    first_beat = tmp_path / "seed_a" / "beat.wav"
    second_beat = tmp_path / "seed_b" / "beat.wav"
    assert first_beat.exists() and second_beat.exists()
    assert _sha256(first_beat) == _sha256(second_beat)


def test_different_seed_produces_different_beat(tmp_path: Path) -> None:
    _beat_run(tmp_path, "seed_c", 1)
    _beat_run(tmp_path, "seed_d", 2)

    assert _sha256(tmp_path / "seed_c" / "beat.wav") != _sha256(
        tmp_path / "seed_d" / "beat.wav"
    )


def test_only_blocks_unselected_stages_explicitly(tmp_path: Path) -> None:
    report = run_full_pipeline(
        "only_lyrics",
        {"genre": "drift_phonk", "theme": "night", "seed": 7},
        out_root=tmp_path / "only_lyrics",
        only={"lyrics"},
    )

    by_name = {stage["name"]: stage for stage in report["stages"]}
    assert by_name["_stage_lyrics"]["status"] != "BLOCKED"
    assert by_name["_stage_beat"]["status"] == "BLOCKED"
    assert "skipped by --only" in by_name["_stage_beat"]["reason"]
    assert by_name["_stage_mastering"]["status"] == "BLOCKED"
    assert not (tmp_path / "only_lyrics" / "beat.wav").exists()
    assert report["only"] == ["lyrics"]


def test_unknown_only_stage_is_rejected_before_any_work(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown stage keys for --only"):
        run_full_pipeline(
            "bad_only",
            {"genre": "drift_phonk", "theme": "night"},
            out_root=tmp_path / "bad_only",
            only={"beat", "nonsense"},
        )
    assert not (tmp_path / "bad_only" / "report.json").exists()


def test_resume_reuses_previous_beat_and_marks_it(tmp_path: Path) -> None:
    out_root = tmp_path / "resume"
    _beat_run(tmp_path, "resume", 99)
    before = _sha256(out_root / "beat.wav")

    report = run_full_pipeline(
        "resume",
        {"genre": "drift_phonk", "theme": "night drive", "seed": 99, "duration_sec": 12},
        out_root=out_root,
        only={"arrangement", "beat"},
        resume=True,
    )

    beat_stage = next(s for s in report["stages"] if s["name"] == "_stage_beat")
    assert beat_stage["status"] == "OK"
    assert beat_stage["output"]["resumed"] is True
    assert report["resume"] is True
    assert _sha256(out_root / "beat.wav") == before


def test_report_json_is_written_next_to_artefacts(tmp_path: Path) -> None:
    report = _beat_run(tmp_path, "report", 5)

    written = (tmp_path / "report" / "report.json").read_text(encoding="utf-8")
    assert '"project_id": "report"' in written
    assert report["verdict"].endswith(("PASS", "PASS_BLOCKED", "PARTIAL"))
