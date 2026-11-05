from __future__ import annotations

import numpy as np

from modules.voice_recording import capability as capability_mod
from modules.voice_recording import recorder as recording
from modules.voice_recording import state as state_mod
from modules.voice_recording import takes as takes_mod


class _BrokenStream:
    def stop(self) -> None:
        raise RuntimeError("device disconnected")

    def close(self) -> None:
        raise AssertionError("close must not run after stop failure")


def test_recorder_records_metric_callback_failure_without_raising(monkeypatch) -> None:
    monkeypatch.setattr(recording, "_np", np)
    recorder = recording.RealMicRecorder(on_metrics=lambda _metrics: (_ for _ in ()).throw(RuntimeError("UI gone")))

    recorder._emit_metrics(np.ones(16, dtype=np.float32))

    assert recorder.last_error == "metrics callback: RuntimeError: UI gone"


def test_recorder_records_stream_shutdown_failure_without_raising() -> None:
    recorder = recording.RealMicRecorder()
    recorder._active = True
    recorder._stream = _BrokenStream()

    result = recorder.stop()

    assert result == {"ok": False, "reason": "no audio captured"}
    assert recorder.last_error == "stream shutdown: RuntimeError: device disconnected"


class _BrokenDeviceBackend:
    def query_devices(self):
        raise RuntimeError("audio service unavailable")


def test_capability_report_discloses_device_query_failure(monkeypatch) -> None:
    monkeypatch.setattr(capability_mod, "SD_OK", True)
    monkeypatch.setattr(capability_mod, "_sd", _BrokenDeviceBackend())
    monkeypatch.setattr(capability_mod, "_np", np)

    report = capability_mod.capability_report()

    assert report["input_devices_found"] == 0
    assert report["real_recording_possible"] is False
    assert report["device_query_error"] == "RuntimeError: audio service unavailable"


def test_split_keeps_takes_and_logs_when_manifest_write_fails(tmp_path, monkeypatch, caplog) -> None:
    import logging
    from pathlib import Path

    import soundfile as sf

    source = tmp_path / "phrase.wav"
    sf.write(source, np.full(8_000, 0.1, dtype=np.float32), 8_000)
    original_write_text = Path.write_text

    def fail_only_manifest(self, *args, **kwargs):
        if self.name == "phrase_takes.json":
            raise OSError("disk full")
        return original_write_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_only_manifest)
    with caplog.at_level(logging.WARNING, logger=state_mod.LOGGER.name):
        takes = takes_mod.split_wav_into_takes(str(source), min_take_ms=800)

    assert len(takes) == 1
    assert "voice take manifest was not written: disk full" in caplog.text


def test_recorded_audio_writes_valid_wav_and_can_be_split(monkeypatch, tmp_path):
    import wave
    monkeypatch.setattr(recording, "_np", np)
    monkeypatch.setattr(recording, "VAULT_DIR", tmp_path)
    recorder = recording.RealMicRecorder(sample_rate=8000, style="sing")
    recorder._active = True
    recorder._start_ts = 1234
    recorder._buf = [np.full((8000, 1), 0.1, dtype=np.float32)]
    class Stream:
        def stop(self): pass
        def close(self): pass
    recorder._stream = Stream()
    result = recorder.stop()
    assert result["ok"] is True
    with wave.open(result["path"], "rb") as audio:
        assert audio.getnframes() == 8000
        assert audio.getframerate() == 8000
    monkeypatch.setattr(recorder, "stop", lambda: result)
    takes = recorder.stop_and_split(min_take_ms=500)
    assert len(takes) == 1 and takes[0].style == "sing"
