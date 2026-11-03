"""Simulate devices to test routing and indexing; not a physical microphone test."""
import sys
from types import SimpleNamespace

import numpy as np
import soundfile as sf

from modules import voice_convert
from ui import karaoke_recorder


def test_duplex_recording_uses_backing_and_indexes_only_one_wav(tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    vault.mkdir()
    monkeypatch.setattr(karaoke_recorder, "VAULT", vault)
    monkeypatch.setattr(voice_convert, "VAULT_DIR", vault)
    monkeypatch.setattr(voice_convert, "VOICE_INDEX", vault / "vault_index.json")
    monkeypatch.setattr(voice_convert, "_ensure_dirs", lambda: None)
    backing = tmp_path / "beat.wav"
    sf.write(backing, np.full(4000, 0.2, dtype=np.float32), 4000)
    calls = {}
    def playrec(audio, **kwargs):
        calls.update(kwargs)
        calls["shape"] = audio.shape
        return np.full((len(audio), 1), 0.1, dtype=np.float32)
    monkeypatch.setitem(sys.modules, "sounddevice", SimpleNamespace(playrec=playrec))
    result = karaoke_recorder.record_with_backing(str(backing), duration_sec=1, style="singing", sr=8000)
    assert result["ok"] and result["backing_used"] and not result["warning"]
    assert calls["blocking"] is True and calls["shape"] == (8000, 1)
    assert len(list(vault.glob("*.wav"))) == 1
    index = voice_convert._load_index()
    assert len(index) == 1 and index[0]["path"] == result["path"]


def test_silence_and_missing_backing_do_not_become_recordings(tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    vault.mkdir()
    monkeypatch.setattr(karaoke_recorder, "VAULT", vault)
    fake = SimpleNamespace(rec=lambda frames, **kw: np.zeros((frames, 1)), wait=lambda: None)
    monkeypatch.setitem(sys.modules, "sounddevice", fake)
    result = karaoke_recorder.record_with_backing("", duration_sec=1, sr=8000)
    assert "silent" in result["error"]
    result = karaoke_recorder.record_with_backing("missing.wav", duration_sec=1, sr=8000)
    assert "not found" in result["error"]
    assert not list(vault.iterdir())


def test_missing_internal_file_is_not_registered(tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    vault.mkdir()
    monkeypatch.setattr(voice_convert, "VAULT_DIR", vault)
    monkeypatch.setattr(voice_convert, "VOICE_INDEX", vault / "vault_index.json")
    monkeypatch.setattr(voice_convert, "_ensure_dirs", lambda: None)
    result = voice_convert.add_recording(str(vault / "missing.wav"), {"style": "singing"})
    assert "error" in result
    assert not voice_convert._load_index()
