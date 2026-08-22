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
