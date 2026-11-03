"""Contract regressions found while exercising the reference-to-master journey."""
from pathlib import Path

import numpy as np
import soundfile as sf

from app.core.recipe import build_recipe, resolve_style_vector
from app.core.stages.prep import _stage_groove


def test_multireference_style_reaches_beat_and_preserves_user_override():
    recipe = build_recipe({"genre": "house", "seed": 42})
    analysis = {"target_bpm": 137, "target_mode": "major", "individual": [{"key_root": "F#"}]}
    style = resolve_style_vector(recipe, analysis)
    assert (style["genre"], style["target_bpm"], style["target_mode"]) == ("house", 137, "major")
    assert style["individual"][0]["key_root"] == "F#"
    recipe["bpm_override"] = 115
    assert resolve_style_vector(recipe, analysis)["target_bpm"] == 115


def test_single_reference_root_reaches_beat():
    recipe = build_recipe({"genre": "trap"})
    style = resolve_style_vector(recipe, {"bpm": 80, "mode": "minor", "key_root": "D"})
    assert style["key_root"] == "D"


def test_genre_changes_groove_without_references():
    house = _stage_groove([], "house")["groove"]["kick_pattern"]
    trap = _stage_groove([], "trap")["groove"]["kick_pattern"]
    assert house == [1, 0, 0, 0] * 4
    assert house != trap


def test_partial_run_does_not_execute_unselected_lyrics(monkeypatch, tmp_path):
    from app.core import orchestrator

    def fail(*args, **kwargs):
        raise AssertionError("unselected lyrics stage was executed")
    monkeypatch.setattr(orchestrator, "_run_lyrics_stage", fail)
    result = orchestrator.run_full_pipeline("partial", {}, out_root=tmp_path, only={"analysis"})
    stage = next(s for s in result["stages"] if s["name"] == "_stage_lyrics")
    assert stage["status"] == "BLOCKED"


def test_invalid_explicit_vocal_does_not_silently_fall_back_to_tts(monkeypatch, tmp_path):
    from app.core.stages import vocal_chain

    def fail(*args, **kwargs):
        raise AssertionError("TTS should not replace a missing explicit recording")
    monkeypatch.setattr(vocal_chain, "_stage_voice_synth", fail)
    recipe = build_recipe({"own_vocal_wav": str(tmp_path / "missing.wav")})
    stages, vocal, warnings = vocal_chain._run_vocal_chain(recipe, "слова", tmp_path)
    assert stages[0].status.value == "FAILED"
    assert vocal is None and warnings


def test_reference_match_reports_measured_output_not_original_bus(monkeypatch, tmp_path):
    from app.core.stages.mix import _stage_mix_and_sidechain
    from modules.mix import bus, reference

    sr = 8000
    original = tmp_path / "mix.wav"
    matched = tmp_path / "mix_matched.wav"
    t = np.arange(sr * 2) / sr
    sf.write(original, np.column_stack([0.01 * np.sin(2*np.pi*220*t)] * 2), sr)
    sf.write(matched, np.column_stack([0.4 * np.sin(2*np.pi*220*t)] * 2), sr)
    monkeypatch.setattr(bus, "prepare_mix", lambda *a, **k: {
        "ok": True, "out_wav": str(original), "report": {"rms_dbfs": -40.0},
        "gates": {"bus_rms": True}, "gates_passed": True})
    monkeypatch.setattr(reference, "match_to_reference", lambda *a, **k: {
        "ok": True, "out_wav": str(matched)})
    result = _stage_mix_and_sidechain("beat.wav", None, tmp_path, "ref.wav")
    assert result["ok"]
    assert result["out_wav"] == str(matched)
    assert result["metrics"]["rms_dbfs"] > -20
    assert result["pre_reference"]["metrics"]["rms_dbfs"] == -40.0
    assert not result["gates_passed"]


def test_quality_failures_are_not_hidden_by_successful_execution():
    from app.core.orchestrator import _quality_gate_failures
    from app.pipeline import StageResult, StageStatus

    stages = [
        StageResult(name="_stage_mix_and_sidechain", status=StageStatus.OK,
                    output={"gates_passed": False, "gates": {"bus_rms": False},
                            "reference": {"gates_passed": False, "gates": {"profile": False}}}),
        StageResult(name="_stage_mastering", status=StageStatus.OK,
                    output={"summary": {"gates_passed": False, "failed_gates": {"streaming": ["crest"]}}}),
    ]
    failures = _quality_gate_failures(stages)
    assert len(failures) == 3
    assert "bus_rms" in failures[0] and "profile" in failures[1] and "crest" in failures[2]
