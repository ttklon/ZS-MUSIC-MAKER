"""Simulate devices to test routing and indexing; not a physical microphone test."""
import sys
from types import SimpleNamespace

import numpy as np
import soundfile as sf
import pytest

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
    sf.write(backing, np.full(8000, 0.2, dtype=np.float32), 8000)
    calls = {}
    def playrec(audio, **kwargs):
        calls.update(kwargs)
        calls["shape"] = audio.shape
        return np.full((len(audio), 1), 0.1, dtype=np.float32)
    monkeypatch.setitem(sys.modules, "sounddevice", SimpleNamespace(playrec=playrec))
    result = karaoke_recorder.record_with_backing(str(backing), duration_sec=1, style="singing", sr=16000)
    assert result["ok"] and result["backing_used"] and not result["warning"]
    assert calls["blocking"] is True and calls["shape"] == (16000, 1)
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


def test_float_recording_preserves_samples_and_survives_corrupt_index(tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    vault.mkdir()
    index = vault / "vault_index.json"
    old_index = b"invalid index"
    index.write_bytes(old_index)
    monkeypatch.setattr(karaoke_recorder, "VAULT", vault)
    monkeypatch.setattr(voice_convert, "VAULT_DIR", vault)
    monkeypatch.setattr(voice_convert, "VOICE_INDEX", index)
    monkeypatch.setattr(voice_convert, "_ensure_dirs", lambda: None)
    wave = np.linspace(-0.8, 0.8, 8000, dtype=np.float32)
    fake = SimpleNamespace(rec=lambda *a, **kw: wave[:, None].copy(), wait=lambda: None)
    monkeypatch.setitem(sys.modules, "sounddevice", fake)
    result = karaoke_recorder.record_with_backing("", duration_sec=1, sr=8000)
    assert result["ok"] and "indexing failed" in result["warning"]
    assert sf.info(result["path"]).subtype == "FLOAT"
    restored, _ = sf.read(result["path"], dtype="float32")
    assert np.array_equal(restored, wave) and index.read_bytes() == old_index


def test_device_rate_probe_falls_back_and_downmixes_for_mono_output(tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    vault.mkdir()
    monkeypatch.setattr(karaoke_recorder, "VAULT", vault)
    monkeypatch.setattr(voice_convert, "VAULT_DIR", vault)
    monkeypatch.setattr(voice_convert, "VOICE_INDEX", vault / "vault_index.json")
    monkeypatch.setattr(voice_convert, "_ensure_dirs", lambda: None)
    backing = tmp_path / "beat.wav"
    sf.write(backing, np.column_stack([np.full(44100, .1), np.full(44100, .3)]), 44100)
    calls = []
    def check_input_settings(**kw):
        if kw["samplerate"] != 48000:
            raise RuntimeError("unsupported input rate")
    def check_output_settings(**kw):
        if kw["samplerate"] != 48000 or kw["channels"] != 1:
            raise RuntimeError("unsupported output format")
    def playrec(data, **kw):
        calls.append((data, kw))
        return np.full((len(data), 1), .1, dtype=np.float32)
    fake = SimpleNamespace(query_devices=lambda kind: {"default_samplerate": 48000},
                           check_input_settings=check_input_settings,
                           check_output_settings=check_output_settings, playrec=playrec)
    monkeypatch.setitem(sys.modules, "sounddevice", fake)
    result = karaoke_recorder.record_with_backing(str(backing), duration_sec=1, sr=44100)
    assert result["ok"] and result["device_format_checked"] and result["sample_rate"] == 48000
    assert result["playback_channels"] == 1 and sf.info(result["path"]).samplerate == 48000
    assert "downmixed to mono" in result["warning"] and "48000 Hz" in result["warning"]
    assert calls[0][0].shape == (48000, 1) and abs(float(calls[0][0][2000, 0]) - 0.2) < 0.01


def test_device_probe_failure_does_not_silently_drop_backing(tmp_path, monkeypatch):
    backing = tmp_path / "beat.wav"
    sf.write(backing, np.full(8000, .1, dtype=np.float32), 8000)
    fake = SimpleNamespace(check_input_settings=lambda **kw: None,
                           check_output_settings=lambda **kw: (_ for _ in ()).throw(RuntimeError("no output")),
                           playrec=lambda *a, **k: pytest.fail("must not record without backing"))
    monkeypatch.setitem(sys.modules, "sounddevice", fake)
    result = karaoke_recorder.record_with_backing(str(backing), duration_sec=1, sr=8000)
    assert "No compatible input/output" in result["error"]


def test_short_backing_reports_silence_padding(tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    vault.mkdir()
    monkeypatch.setattr(karaoke_recorder, "VAULT", vault)
    monkeypatch.setattr(voice_convert, "VAULT_DIR", vault)
    monkeypatch.setattr(voice_convert, "VOICE_INDEX", vault / "vault_index.json")
    monkeypatch.setattr(voice_convert, "_ensure_dirs", lambda: None)
    backing = tmp_path / "short.wav"
    sf.write(backing, np.full(4000, .1, dtype=np.float32), 8000)
    captured = []
    fake = SimpleNamespace(playrec=lambda data, **kw: captured.append(data) or np.ones((len(data), 1), dtype=np.float32) * .1)
    monkeypatch.setitem(sys.modules, "sounddevice", fake)
    result = karaoke_recorder.record_with_backing(str(backing), duration_sec=1, sr=8000)
    assert result["ok"] and result["backing_shorter"] and "remaining playback was silence" in result["warning"]
    assert not captured[0][4000:].any()


def test_device_probe_prefers_stereo_at_alternate_compatible_rate():
    def output(**kw):
        pair = kw["samplerate"], kw["channels"]
        if pair not in {(44100, 1), (48000, 2)}:
            raise RuntimeError("unsupported output")
    fake = SimpleNamespace(query_devices=lambda kind: {"default_samplerate": 48000},
                           check_input_settings=lambda **kw: None, check_output_settings=output)
    rate, channels, checked = karaoke_recorder._select_device_format(fake, 44100, 2)
    assert (rate, channels, checked) == (48000, 2, True)
