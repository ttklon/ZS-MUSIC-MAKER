"""Regression coverage for RVC subprocess progress parse diagnostics."""

from modules.rvc_manager import RVCBackend, RVCTrainer, TrainingJob


def test_progress_parser_records_malformed_epoch_token(monkeypatch):
    trainer = RVCTrainer(backend=RVCBackend(ok=True))
    job = TrainingJob(voice_name="voice", epochs=10, device="cpu")

    class _Proc:
        stdout = ["Epoch ???/10\n"]

        def wait(self):
            return 0

    monkeypatch.setattr("modules.rvc_manager.trainer.subprocess.Popen", lambda *args, **kwargs: _Proc())

    trainer._run_with_progress(["fake-train"], job)

    assert job.progress == 0.0
    # Формат ошибки теперь прямо называет испорченный токен: по нему видно,
    # что именно прислал тренер, а не только «int() не смог».
    assert trainer.progress_parse_errors == ["ValueError: invalid epoch token '???'"]
    assert job.progress == 0.0
