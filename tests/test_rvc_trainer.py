from __future__ import annotations

import json

import modules.rvc_trainer_v9 as trainer


def test_rvc_trainer_dry_run_persists_honest_no_model_status(tmp_path, monkeypatch) -> None:
    jobs = tmp_path / "training_jobs"
    manifest = tmp_path / "voice_manifest.json"
    manifest.write_text(json.dumps({"n_items": 1, "total_sec": 20, "items": []}), encoding="utf-8")
    monkeypatch.setattr(trainer, "JOBS_DIR", jobs)

    job = trainer.retrain_incremental(str(manifest), dry_run=True, background=False)
    persisted = trainer.get_job(job["id"])

    assert job["status"] == "done_dry"
    assert persisted is not None
    assert persisted["status"] == "done_dry"
    assert "no .pth model was produced" in persisted["log"][-1]
    assert jobs.exists()


def test_rvc_trainer_non_dry_blocks_without_claiming_simulated_training(tmp_path, monkeypatch) -> None:
    jobs = tmp_path / "training_jobs"
    manifest = tmp_path / "voice_manifest.json"
    manifest.write_text(json.dumps({"n_items": 1, "total_sec": 20, "items": []}), encoding="utf-8")
    monkeypatch.setattr(trainer, "JOBS_DIR", jobs)

    job = trainer.retrain_incremental(str(manifest), dry_run=False, background=False)
    persisted = trainer.get_job(job["id"])

    assert job["status"] == "blocked_backend"
    assert persisted is not None
    assert persisted["status"] == "blocked_backend"
    assert "no backend invocation or model output was claimed" in persisted["log"][-1]
