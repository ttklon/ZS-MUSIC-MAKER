"""Own-vocal validation and audible-placement contracts (CPU, no live mic)."""
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from app.core.recipe import build_recipe
from app.core.stages import vocal_chain
from app.core.stages.mix import _stage_mix_and_sidechain
from app.core.user_vocal import inspect_user_vocal


def write_audio(path: Path, data, sr=8000):
    sf.write(path, np.asarray(data, dtype="float32"), sr, subtype="FLOAT")


@pytest.mark.parametrize("data", [np.zeros(8000), np.r_[np.full(7999, 0.1), np.nan]])
def test_silent_or_nonfinite_user_voice_is_rejected_without_modification(tmp_path, monkeypatch, data):
    path = tmp_path / "voice.wav"
    write_audio(path, data)
    before = path.read_bytes()
    monkeypatch.setattr(vocal_chain, "_stage_voice_synth", lambda *a, **k: pytest.fail("must not silently substitute TTS"))
    stages, vocal, warnings = vocal_chain._run_vocal_chain(build_recipe({"own_vocal_wav": str(path)}), "text", tmp_path)
    assert stages[0].status.value == "FAILED" and vocal is None and warnings
    assert path.read_bytes() == before


def test_valid_vocal_has_measured_quality_and_warns_if_near_clipping(tmp_path, monkeypatch):
    path = tmp_path / "voice.wav"
    audio = 0.1 * np.sin(np.arange(8000) / 10)
    audio[100] = 0.99
    write_audio(path, audio)
    monkeypatch.setattr(vocal_chain, "_stage_vocal_fx", lambda source, *a, **k: {"ok": True, "path": source})
    stages, vocal, warnings = vocal_chain._run_vocal_chain(build_recipe({"own_vocal_wav": str(path)}), "text", tmp_path)
    assert stages[0].status.value == "OK" and vocal == str(path)
    info = stages[0].output["recording_quality"]
    assert info["near_clipping_warning"] and info["near_clip_samples"] == 1 and warnings
    assert stages[1].status.value == "BLOCKED" and "disabled" in stages[1].reason
    assert build_recipe({})["use_rvc"] is False


def test_vocal_channel_and_duration_limits(tmp_path):
    path = tmp_path / "three.wav"
    write_audio(path, np.full((8000, 3), 0.1))
    with pytest.raises(ValueError, match="mono/stereo"):
        inspect_user_vocal(str(path))
    long_path = tmp_path / "long.wav"
    with sf.SoundFile(long_path, mode="w", samplerate=8000, channels=1, subtype="PCM_16") as audio:
        block = np.full(8000, 0.1, dtype="float32")
        for _ in range(601):
            audio.write(block)
    with pytest.raises(ValueError, match="600 seconds"):
        inspect_user_vocal(str(long_path))


def test_offset_that_removes_entire_vocal_cannot_succeed_as_instrumental(tmp_path):
    sr = 8000
    beat, vocal = tmp_path / "beat.wav", tmp_path / "voice.wav"
    t = np.arange(sr) / sr
    write_audio(beat, 0.1 * np.sin(2*np.pi*220*t), sr)
    write_audio(vocal, 0.1 * np.sin(2*np.pi*440*t), sr)
    output = tmp_path / "project"
    result = _stage_mix_and_sidechain(str(beat), str(vocal), output, vocal_offset_ms=5000)
    assert not result["ok"] and "outside the beat" in result["reason"]
    assert not (output / "mix.wav").exists()


def test_invalid_requested_recording_blocks_mix_in_pipeline(tmp_path, monkeypatch):
    from app.core import orchestrator
    from app.pipeline import StageResult, StageStatus
    # A beat exists, but a missing explicitly requested voice must not be silently ignored.
    monkeypatch.setattr(orchestrator, "_stage_beat", lambda *a, **k: {"ok": True, "path": str(tmp_path / "beat.wav")})
    monkeypatch.setattr(orchestrator, "_run_vocal_chain", lambda *a, **k: (
        [StageResult("_stage_voice_synth", StageStatus.FAILED, reason="missing"),
         StageResult("_stage_rvc", StageStatus.BLOCKED), StageResult("_stage_vocal_fx", StageStatus.BLOCKED)], None, ["missing voice"]))
    monkeypatch.setattr(orchestrator, "_stage_mix_and_sidechain", lambda *a, **k: pytest.fail("must not render instrumental instead"))
    result = orchestrator.run_full_pipeline("voice-missing", {"own_vocal_wav": "missing.wav"},
                                            out_root=tmp_path / "run", only={"beat", "vocal", "mix"})
    stage = next(s for s in result["stages"] if s["name"] == "_stage_mix_and_sidechain")
    assert stage["status"] == "BLOCKED" and "refusing instrumental" in stage["reason"]
    assert any("requested recording unavailable" in warning for warning in result["warnings"])


def test_effects_can_be_disabled_without_touching_recording(tmp_path, monkeypatch):
    path = tmp_path / "voice.wav"
    write_audio(path, 0.1 * np.sin(np.arange(8000) / 10))
    monkeypatch.setattr(vocal_chain, "_stage_vocal_fx", lambda *a, **k: pytest.fail("effects disabled"))
    recipe = build_recipe({"own_vocal_wav": str(path), "use_vocal_fx": False})
    stages, vocal, _ = vocal_chain._run_vocal_chain(recipe, "", tmp_path)
    assert recipe["tune"] is False and stages[2].status.value == "BLOCKED"
    assert "disabled" in stages[2].reason and vocal == str(path)


def test_pitch_correction_is_explicitly_forwarded(tmp_path, monkeypatch):
    path = tmp_path / "voice.wav"
    write_audio(path, 0.1 * np.sin(np.arange(8000) / 10))
    kwargs = []
    monkeypatch.setattr(vocal_chain, "_stage_vocal_fx", lambda path, *a, **kw: kwargs.append(kw) or {"ok": True, "path": path})
    for tune in (False, True):
        recipe = build_recipe({"own_vocal_wav": str(path), "tune": tune})
        vocal_chain._run_vocal_chain(recipe, "", tmp_path)
    assert [call["tune"] for call in kwargs] == [False, True]
