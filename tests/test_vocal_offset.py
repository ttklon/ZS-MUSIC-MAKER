"""Sample-accurate, deterministic vocal placement; not hardware calibration."""
import numpy as np
import soundfile as sf

from app.core.recipe import build_recipe
from app.core.stages.mix import _stage_mix_and_sidechain
from modules.mix.bus import _place_vocal


def test_sample_placement_advance_delay_and_clipping():
    source = np.arange(1, 6, dtype=float)[:, None]
    assert _place_vocal(source, 6, 2)[:, 0].tolist() == [0, 0, 1, 2, 3, 4]
    assert _place_vocal(source, 6, -2)[:, 0].tolist() == [3, 4, 5, 0, 0, 0]
    assert not _place_vocal(source, 6, 50).any()
    assert not _place_vocal(source, 6, -50).any()
    assert _place_vocal(source, 6, 0)[:, 0].tolist() == [1, 2, 3, 4, 5, 0]


def test_real_mix_receives_vocal_offset(tmp_path, monkeypatch):
    from modules.mix import bus
    sr = 8000
    time = np.arange(sr) / sr
    beat = tmp_path / "beat.wav"
    vocal = tmp_path / "voice.wav"
    sf.write(beat, 0.1 * np.sin(time * 440), sr)
    sf.write(vocal, 0.1 * np.sin(time * 880), sr)
    captured = {}
    original = bus._place_vocal
    def record(audio, length, offset_samples):
        captured["samples"] = offset_samples
        return original(audio, length, offset_samples)
    monkeypatch.setattr(bus, "_place_vocal", record)
    result = _stage_mix_and_sidechain(str(beat), str(vocal), tmp_path, vocal_offset_ms=-125)
    assert result["ok"] and result["vocal_used"]
    assert result["vocal_offset_ms"] == -125 and captured["samples"] == -1000
    assert sf.info(result["out_wav"]).frames == sr
    assert build_recipe({"vocal_offset_ms": 99999})["vocal_offset_ms"] == 5000
