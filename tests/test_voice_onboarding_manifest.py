from __future__ import annotations

import logging
from pathlib import Path

import modules.voice_onboarding as onboarding


def test_corrupt_onboarding_manifest_falls_back_and_logs_warning(tmp_path: Path, monkeypatch, caplog) -> None:
    manifest = tmp_path / "onboarding_manifest.json"
    manifest.write_text("{invalid json", encoding="utf-8")
    monkeypatch.setattr(onboarding, "MANIFEST", manifest)

    with caplog.at_level(logging.WARNING, logger=onboarding.LOGGER.name):
        loaded = onboarding._load_manifest()

    assert loaded == {"steps": [], "started_at": None, "completed_at": None}
    assert "voice onboarding manifest unreadable; using empty plan" in caplog.text
