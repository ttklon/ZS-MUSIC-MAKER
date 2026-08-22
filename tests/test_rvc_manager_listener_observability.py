"""Regression coverage for observable isolated RVC progress-listener failures."""

from modules.rvc_manager import RVCBackend, RVCTrainer, TrainingJob


def test_emit_records_listener_failure_without_blocking_other_listeners():
    trainer = RVCTrainer(backend=RVCBackend(ok=True))
    trainer.job = TrainingJob(voice_name="voice", epochs=1, device="cpu")
    received = []

    def failing_listener(job):
        raise RuntimeError("ui callback failed")

    trainer.on_progress(failing_listener)
    trainer.on_progress(lambda job: received.append(job.voice_name))

    trainer._emit()

    assert received == ["voice"]
    assert trainer.listener_errors == ["RuntimeError: ui callback failed"]
