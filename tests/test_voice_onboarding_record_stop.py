from __future__ import annotations

import threading

import modules.voice_onboarding as onboarding
import modules.voice_recording as voice_recording


class _FakeRecorder:
    instances: list["_FakeRecorder"] = []

    def __init__(self, **_kwargs) -> None:
        self.stopped = False
        self.__class__.instances.append(self)

    def start(self) -> dict[str, object]:
        return {"ok": True}

    def stop(self) -> dict[str, object]:
        self.stopped = True
        return {"ok": True, "path": "partial.wav", "duration_sec": 7.5}


def test_record_step_stop_event_finalizes_without_accepting_partial_capture(monkeypatch) -> None:
    _FakeRecorder.instances = []
    monkeypatch.setattr(
        voice_recording, "capability_report", lambda: {"real_recording_possible": True}
    )
    monkeypatch.setattr(voice_recording, "RealMicRecorder", _FakeRecorder)
    stop_event = threading.Event()
    stop_event.set()
    step = onboarding.OnboardingStep(
        step_id="phon_01", kind="phoneme_text", label="test", target_sec=60, text_or_prompt="text"
    )

    recorded = onboarding.record_step(step, stop_event=stop_event)

    assert _FakeRecorder.instances[0].stopped
    assert recorded.cancelled is True
    assert recorded.ok is False
    assert recorded.recorded_path == "partial.wav"
    assert recorded.duration_sec == 7.5
    assert onboarding.compute_progress([recorded]).total_recorded_sec == 0.0
