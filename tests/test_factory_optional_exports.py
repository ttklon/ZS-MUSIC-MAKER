"""Disabled exports must not cause repeated generation; missing models still do."""
import copy

import pytest

from app.core.pipeline_runtime import _blocked
from modules.hit_factory.readiness import attempt_readiness


@pytest.fixture
def attempt(tmp_path):
    from modules.dsp.wavio import write_wav
    import numpy as np

    master = tmp_path / "master.wav"
    write_wav(master, np.sin(np.arange(8000) * 0.1).astype("float32") * 0.2, 8000)
    skip = _blocked("_stage_stems", "stems disabled by user (export_stems=false)",
                    output={"requested": False, "skip_kind": "user_disabled"})
    return {
        "master_path": str(master), "hit_score": 72, "verdict": "solid",
        "hit": {"hit_score": 72, "verdict": "solid"},
        "report": {"verdict": "PASS_BLOCKED", "status_summary": {"blocked": ["_stage_stems"]},
                   "stages": [skip.to_dict()]},
    }


def test_explicit_stem_opt_out_is_not_a_readiness_failure(attempt):
    assert attempt_readiness(attempt) == {"ready": True, "reasons": []}
    assert attempt["report"]["verdict"] == "PASS_BLOCKED"
    assert attempt["report"]["stages"][0]["status"] == "BLOCKED"


@pytest.mark.parametrize("output", [None, {}, {"requested": False},
    {"requested": "false", "skip_kind": "user_disabled"},
    {"requested": False, "skip_kind": "missing_model"}])
def test_no_opt_out_inferred_from_reason_alone(attempt, output):
    attempt["report"]["stages"][0]["output"] = output
    assert not attempt_readiness(attempt)["ready"]


@pytest.mark.parametrize("name", ["_stage_voice_synth", "_stage_lyrics", "_stage_mix_and_sidechain", "_stage_auto_qa"])
def test_essential_stage_cannot_opt_out(attempt, name):
    row = copy.deepcopy(attempt["report"]["stages"][0])
    row["name"] = name
    attempt["report"]["stages"].append(row)
    attempt["report"]["status_summary"]["blocked"].append(name)
    assert not attempt_readiness(attempt)["ready"]


@pytest.mark.parametrize("field,value", [("only", ["hit_score"]), ("dry_run", True),
    ("quality_gate_failures", ["crest"]), ("verdict", "PARTIAL")])
def test_disabled_stems_do_not_hide_other_failures(attempt, field, value):
    attempt["report"][field] = value
    assert not attempt_readiness(attempt)["ready"]


def test_blocked_row_is_detected_even_if_summary_omits_it(attempt):
    attempt["report"]["stages"].append(_blocked("_stage_lyrics", "LLM unavailable").to_dict())
    assert not attempt_readiness(attempt)["ready"]


def test_failed_stem_export_is_not_an_opt_out(attempt):
    attempt["report"]["stages"][0]["status"] = "FAILED"
    assert not attempt_readiness(attempt)["ready"]


def test_post_master_marks_only_explicit_disabled_export(tmp_path, monkeypatch):
    from app.core import pipeline_blocks as blocks

    monkeypatch.setattr(blocks, "_stage_polish", lambda *a, **kw: {"ok": True})
    monkeypatch.setattr(blocks, "_stage_auto_qa", lambda *a: {"ok": True})
    monkeypatch.setattr(blocks, "_stage_hit_score", lambda *a: {"ok": True})
    monkeypatch.setattr(blocks, "_stage_stems", lambda *a: pytest.fail("export disabled"))
    stages = blocks._run_post_master_stages("master.wav", {"export_stems": False}, tmp_path, None)
    stems = next(stage for stage in stages if stage.name == "_stage_stems")
    assert stems.output == {"requested": False, "skip_kind": "user_disabled"}
    partial = blocks._run_post_master_stages("master.wav", {"export_stems": False}, tmp_path, {"hit_score"})
    assert next(stage for stage in partial if stage.name == "_stage_stems").output is None


def test_factory_does_not_repeat_render_for_disabled_stems(attempt, tmp_path, monkeypatch):
    from modules.hit_factory import generator

    monkeypatch.setattr(generator, "_maybe_auto_genre", lambda genre, theme: genre)
    monkeypatch.setattr("modules.hit_factory.kpi.build_kpi", lambda *a, **kw: {})
    factory = generator.HitFactory(output_root=tmp_path, adaptive=False, max_attempts=3, verbose=False)
    monkeypatch.setattr(factory, "_build_wizard_state", lambda **kw: {
        "genre": "trap", "theme": "test", "seed": 42, "bpm_override": 140,
        "aggression": 0.7, "duration_sec": 5,
    })
    calls = []

    def render(project_id, state, rng):
        calls.append(project_id)
        return {**attempt, "project_id": project_id, "out_root": str(tmp_path)}

    monkeypatch.setattr(factory, "_run_pipeline_once", render)
    result = factory.make_one(genre="trap", theme="test", seed=42)
    assert result["readiness"]["ready"]
    assert len(calls) == 1


def test_disabled_export_render_beats_higher_score_missing_lyrics(attempt):
    from modules.hit_factory.evolver import select_best

    missing_lyrics = copy.deepcopy(attempt)
    missing_lyrics["hit_score"] = 99
    missing_lyrics["report"]["stages"].append(_blocked("_stage_lyrics", "no model").to_dict())
    assert select_best([missing_lyrics, attempt]) is attempt


@pytest.mark.parametrize("name", ["_stage_rvc", "_stage_vocal_fx"])
def test_optional_vocal_processing_needs_real_retained_audio(attempt, name):
    row = _blocked(name, "disabled by user", output={
        "requested": False, "skip_kind": "user_disabled", "retained_path": attempt["master_path"],
    }).to_dict()
    attempt["report"]["stages"].append(row)
    attempt["report"]["status_summary"]["blocked"].append(name)
    assert attempt_readiness(attempt)["ready"]
    row["output"]["retained_path"] = "missing.wav"
    assert not attempt_readiness(attempt)["ready"]


def test_synthetic_retained_vocal_is_not_an_optional_bypass(attempt):
    row = _blocked("_stage_rvc", "disabled by user", output={
        "requested": False, "skip_kind": "user_disabled", "retained_path": attempt["master_path"],
        "synthetic": True,
    }).to_dict()
    attempt["report"]["stages"].append(row)
    assert not attempt_readiness(attempt)["ready"]


def test_real_vocal_chain_opt_out_metadata_reaches_readiness(attempt, tmp_path):
    from app.core.stages.vocal_chain import _run_vocal_chain

    stages, path, warnings = _run_vocal_chain({
        "voice_mode": "pro", "own_vocal_wav": attempt["master_path"],
        "use_rvc": False, "use_vocal_fx": False,
    }, "Текст", tmp_path)
    assert path
    attempt["report"]["stages"].extend(stage.to_dict() for stage in stages)
    attempt["report"]["status_summary"]["blocked"].extend(["_stage_rvc", "_stage_vocal_fx"])
    assert attempt_readiness(attempt)["ready"]
