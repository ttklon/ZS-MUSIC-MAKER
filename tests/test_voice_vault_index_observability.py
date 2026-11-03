"""A damaged archive must never be treated as an empty index during writes."""
from pathlib import Path

import pytest
import modules.voice_vault as vault
from modules.voice_index_store import VoiceIndexError


def test_corrupt_voice_vault_index_is_preserved_and_reported(tmp_path: Path, monkeypatch) -> None:
    index = tmp_path / "index.json"
    original = b"{not valid json"
    index.write_bytes(original)
    recording = tmp_path / "recording.wav"
    recording.write_bytes(b"voice")
    monkeypatch.setattr(vault, "INDEX_FILE", index)
    monkeypatch.setattr(vault, "VAULT_DIR", tmp_path / "vault")
    with pytest.raises(VoiceIndexError, match="original preserved"):
        vault._load_index()
    result = vault.add_recording(str(recording))
    assert result["ok"] is False and "original preserved" in result["error"]
    assert index.read_bytes() == original and recording.read_bytes() == b"voice"
