from __future__ import annotations

import numpy as np
import soundfile as sf

import modules.voice_vault_v9 as vault


def test_voice_vault_intake_and_speaker_selection(tmp_path, monkeypatch) -> None:
    vault_dir = tmp_path / "vault"
    monkeypatch.setattr(vault, "VAULT_DIR", vault_dir)
    monkeypatch.setattr(vault, "INDEX_FILE", vault_dir / "index.json")
    source = tmp_path / "voice.wav"
    sr = 8_000
    time_axis = np.arange(sr * 2) / sr
    sf.write(source, 0.1 * np.sin(2 * np.pi * 220 * time_axis), sr)

    added = vault.add_recording(str(source), style_hint="rap", transcribe=False)

    assert added["ok"] is True
    selected = vault.select_speaker_wav("rap")
    assert selected == added["item"]["vault_path"]
    assert vault.INDEX_FILE.exists()


def test_voice_vault_speaker_selection_skips_clipped_recordings(tmp_path, monkeypatch) -> None:
    vault_dir = tmp_path / "vault"
    vault_dir.mkdir()
    clipped = vault_dir / "clipped.wav"
    clean = vault_dir / "clean.wav"
    clipped.write_bytes(b"x")
    clean.write_bytes(b"y")
    monkeypatch.setattr(vault, "VAULT_DIR", vault_dir)
    monkeypatch.setattr(vault, "INDEX_FILE", vault_dir / "index.json")
    vault._save_index({"items": {
        "bad": {"vault_path": str(clipped), "style": "rap", "features": {"snr_db": 40, "clip_ratio": 0.1}},
        "good": {"vault_path": str(clean), "style": "rap", "features": {"snr_db": 18, "clip_ratio": 0.0}},
    }})

    assert vault.select_speaker_wav("rap") == str(clean)
