"""Regression coverage for RVC dataset collection copy diagnostics."""

from modules.rvc_manager import RVCBackend, RVCTrainer


def test_dataset_collection_reports_copy_failure_without_counting_clip(monkeypatch, tmp_path):
    trainer = RVCTrainer(backend=RVCBackend(ok=True))
    monkeypatch.setattr("modules.rvc_manager.MODELS_DIR", tmp_path / "models")
    monkeypatch.setattr("modules.voice_convert._load_index", lambda: [{"path": str(tmp_path / "source.wav")}])
    (tmp_path / "source.wav").write_bytes(b"wav")

    def fail_copy(source, destination):
        raise OSError("disk full")

    monkeypatch.setattr("modules.rvc_manager.shutil.copy", fail_copy)

    result = trainer._dataset_ready("voice")

    assert result == tmp_path / "models" / "voice" / "dataset"
    assert trainer.dataset_copy_errors == ["OSError: disk full"]
