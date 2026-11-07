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


def test_reference_match_rejects_candidate_that_breaks_mix_gates(monkeypatch, tmp_path):
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
        "ok": True, "out_wav": str(matched),
        "gates": {"profile_deviation": False, "bandwidth_coverage": True, "true_peak": True, "no_clipping": True},
        "bands": {"max_deviation_before_db": 10, "max_deviation_after_db": 9}})
    result = _stage_mix_and_sidechain("beat.wav", None, tmp_path, "ref.wav")
    assert result["ok"]
    assert result["out_wav"] == str(original)
    assert result["metrics"]["rms_dbfs"] == -40.0
    assert result["reference"]["candidate_mix_metrics"]["rms_dbfs"] > -20
    assert result["reference"]["candidate_out_wav"] == str(matched)
    assert result["reference"]["applied"] is False
    assert result["reference"]["gates"]["mix_safety"] is False
    assert "bus_rms" in result["reference"]["rejection_reason"]
    assert result["fallback_used"] is True


def test_quality_failures_are_not_hidden_by_successful_execution():
    from app.core.orchestrator import _quality_gate_failures
    from app.pipeline import StageResult, StageStatus

    # Стадии OK обязаны нести свой результат (контракт T1), иначе к прод-гейтам
    # примешиваются нарушения контракта и счёт перестаёт быть про качество.
    stages = [
        StageResult(name="_stage_mix_and_sidechain", status=StageStatus.OK,
                    output={"out_wav": "mix.wav",
                            "gates_passed": False, "gates": {"bus_rms": False},
                            "reference": {"gates_passed": False, "gates": {"profile": False}}}),
        StageResult(name="_stage_mastering", status=StageStatus.OK,
                    output={"masters": {"streaming": "master_streaming.wav"},
                            "summary": {"gates_passed": False, "failed_gates": {"streaming": ["crest"]}}}),
    ]
    failures = _quality_gate_failures(stages)
    assert len(failures) == 3
    assert "bus_rms" in failures[0] and "profile" in failures[1] and "crest" in failures[2]


def test_user_can_disable_rvc_and_keep_the_recorded_voice(monkeypatch, tmp_path):
    from app.core.stages import vocal_chain
    voice = tmp_path / "voice.wav"
    sf.write(voice, 0.1 * np.sin(np.arange(8000) * .1), 8000)
    monkeypatch.setattr(vocal_chain, "_stage_rvc", lambda *a, **k: (_ for _ in ()).throw(AssertionError("RVC disabled")))
    monkeypatch.setattr(vocal_chain, "_stage_vocal_fx", lambda path, *a, **k: {"ok": True, "path": path})
    recipe = build_recipe({"own_vocal_wav": str(voice), "use_rvc": False, "rvc_pitch_shift": 99})
    stages, vocal, _ = vocal_chain._run_vocal_chain(recipe, "слова", tmp_path)
    assert recipe["rvc_pitch_shift"] == 12
    assert stages[1].status.value == "BLOCKED" and "disabled by user" in stages[1].reason
    assert vocal == str(voice)


def test_rvc_pitch_parameter_is_forwarded_to_backend(monkeypatch, tmp_path):
    from app.core.stages import vocal
    from modules import rvc_manager
    model = tmp_path / "models/rvc/my_voice/my_voice.pth"
    model.parent.mkdir(parents=True)
    model.write_bytes(b"test model")
    monkeypatch.setattr(vocal, "ROOT", tmp_path)
    calls = {}
    monkeypatch.setattr(rvc_manager, "infer", lambda *args, **kwargs: calls.update(kwargs) or "converted.wav")
    result = vocal._stage_rvc("voice.wav", tmp_path, pitch_shift=-3)
    assert result["ok"] and calls["pitch_shift"] == -3


def test_reference_candidate_is_measured_when_accepted(monkeypatch, tmp_path):
    from app.core.stages.mix import _stage_mix_and_sidechain
    from modules.mix import bus, reference
    sr = 8000
    original, matched = tmp_path / "mix.wav", tmp_path / "candidate.wav"
    t = np.arange(sr * 2) / sr
    sf.write(original, np.column_stack([0.01 * np.sin(2*np.pi*220*t)] * 2), sr)
    sf.write(matched, np.column_stack([0.4 * np.sin(2*np.pi*220*t)] * 2), sr)
    monkeypatch.setattr(bus, "prepare_mix", lambda *a, **k: {
        "ok": True, "out_wav": str(original), "report": {"rms_dbfs": -40.0},
        "gates": {"bus_rms": False}, "gates_passed": False})
    monkeypatch.setattr(reference, "match_to_reference", lambda *a, **k: {
        "ok": True, "out_wav": str(matched),
        "gates": {"profile_deviation": True, "bandwidth_coverage": True, "true_peak": True, "no_clipping": True},
        "bands": {"max_deviation_before_db": 10, "max_deviation_after_db": 9}})
    result = _stage_mix_and_sidechain("beat.wav", None, tmp_path, ["ref.wav"])
    assert result["out_wav"] == str(matched)
    assert result["metrics"]["rms_dbfs"] > -20
    assert result["reference"]["applied"] is True
    assert not result["gates_passed"]


def test_missing_requested_reference_is_observable_failure(monkeypatch, tmp_path):
    from app.core.stages.mix import _stage_mix_and_sidechain
    from app.core.pipeline_runtime import _quality_gate_failures
    from modules.mix import bus
    from app.pipeline import classify
    path = tmp_path / "mix.wav"
    sf.write(path, np.zeros((8000, 2)), 8000)
    monkeypatch.setattr(bus, "prepare_mix", lambda *a, **k: {
        "ok": True, "out_wav": str(path), "report": {}, "gates": {"bus_rms": True}})
    result = _stage_mix_and_sidechain("beat.wav", None, tmp_path, ["missing.wav"])
    assert result["out_wav"] == str(path)
    assert result["reference"]["gates_passed"] is False and result["fallback_used"]
    assert _quality_gate_failures([classify(result, name="_stage_mix_and_sidechain")]) == ["reference match: reference_available"]


def test_reference_uses_strongest_safe_candidate(monkeypatch, tmp_path):
    from app.core.stages.mix import _stage_mix_and_sidechain
    from modules.mix import bus, reference
    original = tmp_path / "mix.wav"
    sf.write(original, np.zeros((8000, 2)), 8000)
    monkeypatch.setattr(bus, "prepare_mix", lambda *a, **k: {
        "ok": True, "out_wav": str(original), "report": {"rms_dbfs": -18.0},
        "gates": {"bus_rms": True}, "gates_passed": True})
    strengths = []
    def candidate(*args, strength, **kwargs):
        strengths.append(strength)
        path = tmp_path / "candidate.wav"
        sf.write(path, np.full((8000, 2), strength / 2), 8000)
        return {"ok": True, "out_wav": str(path), "gates": {"profile_deviation": False,
                "bandwidth_coverage": True, "true_peak": True, "no_clipping": True},
                "bands": {"max_deviation_before_db": 10, "max_deviation_after_db": 9}}
    monkeypatch.setattr(reference, "match_to_reference", candidate)
    monkeypatch.setattr(bus, "evaluate_mix", lambda audio, sr: (
        {"rms_dbfs": -18}, {"bus_rms": bool(np.max(audio) < .2)}))
    result = _stage_mix_and_sidechain("beat.wav", None, tmp_path, ["ref.wav"])
    assert strengths == [1.0, 0.5, 0.25]
    assert result["reference"]["applied"] is True
    assert result["reference"]["gates_passed"] is False  # reference profile still failed
    assert result["fallback_used"] and "0.250" in result["reason"]
    assert result["reference"]["attempts"][0]["rejected"] == ["bus_rms"]
    assert result["reference"]["attempts"][-1]["rejected"] == []
    import json
    recorded = json.loads(Path(result["report_path"]).read_text(encoding="utf-8"))
    assert recorded["out_wav"] == result["out_wav"]
    assert recorded["reference"]["applied"] is True


def test_incomplete_reference_report_is_not_a_success(monkeypatch, tmp_path):
    from app.core.stages.mix import _stage_mix_and_sidechain
    from modules.mix import bus, reference
    path = tmp_path / "mix.wav"
    sf.write(path, np.zeros((8000, 2)), 8000)
    monkeypatch.setattr(bus, "prepare_mix", lambda *a, **k: {
        "ok": True, "out_wav": str(path), "report": {}, "gates": {"bus_rms": True}})
    monkeypatch.setattr(reference, "match_to_reference", lambda *a, **k: {"ok": True, "out_wav": str(path)})
    result = _stage_mix_and_sidechain("beat.wav", None, tmp_path, ["ref.wav"])
    assert result["fallback_used"] and not result["reference"]["gates_passed"]
    assert "incomplete report" in result["reason"]


def test_malformed_reference_match_result_is_explicit_fallback(monkeypatch, tmp_path):
    from app.core.stages.mix import _stage_mix_and_sidechain
    from modules.mix import bus, reference
    path = tmp_path / "mix.wav"
    sf.write(path, np.zeros((8000, 2)), 8000)
    monkeypatch.setattr(bus, "prepare_mix", lambda *a, **k: {
        "ok": True, "out_wav": str(path), "report": {}, "gates": {"bus_rms": True}})
    monkeypatch.setattr(reference, "match_to_reference", lambda *a, **k: None)
    result = _stage_mix_and_sidechain("beat.wav", None, tmp_path, ["ref.wav"])
    assert result["out_wav"] == str(path)
    assert result["fallback_used"] and not result["reference"]["gates_passed"]
    assert "invalid result" in result["reason"]
