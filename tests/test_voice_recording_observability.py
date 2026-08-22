from __future__ import annotations

import numpy as np

import modules.voice_recording as recording


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
    monkeypatch.setattr(recording, "SD_OK", True)
    monkeypatch.setattr(recording, "_sd", _BrokenDeviceBackend())
    monkeypatch.setattr(recording, "_np", np)

    report = recording.capability_report()

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
    with caplog.at_level(logging.WARNING, logger=recording.LOGGER.name):
        takes = recording.split_wav_into_takes(str(source), min_take_ms=800)

    assert len(takes) == 1
    assert "voice take manifest was not written: disk full" in caplog.text
