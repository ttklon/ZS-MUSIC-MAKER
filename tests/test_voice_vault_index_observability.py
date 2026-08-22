from __future__ import annotations

import logging
from pathlib import Path

import modules.voice_vault_v9 as vault


def test_corrupt_voice_vault_index_falls_back_and_logs_warning(tmp_path: Path, monkeypatch, caplog) -> None:
    index = tmp_path / "index.json"
    index.write_text("{not valid json", encoding="utf-8")
    monkeypatch.setattr(vault, "INDEX_FILE", index)

    with caplog.at_level(logging.WARNING, logger=vault.LOGGER.name):
        loaded = vault._load_index()

    assert loaded == {"items": {}}
    assert "voice vault index unreadable; using empty index" in caplog.text
