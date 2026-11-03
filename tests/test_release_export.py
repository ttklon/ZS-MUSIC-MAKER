from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import soundfile as sf

from modules.release import export as release_export


def test_release_export_writes_fingerprinted_manifest_and_zip(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(release_export, "RELEASES_DIR", tmp_path / "releases")
    source = tmp_path / "master.wav"
    sample_rate = 8_000
    time_axis = np.arange(sample_rate) / sample_rate
    sf.write(source, 0.1 * np.sin(2 * np.pi * 220 * time_axis), sample_rate)

    result = release_export.export_release(
        beat_path=str(source), vocal_path="", master_path=str(source),
        lyrics="[Куплет]\nПроверка релиза", recipe={"duration_sec": 1},
        project_name="release_test", artist_name="Test Artist", title="Test Track",
    )

    release_dir = Path(result["release_dir"])
    manifest = json.loads((release_dir / "manifest.json").read_text(encoding="utf-8"))
    metadata = json.loads((release_dir / "metadata.json").read_text(encoding="utf-8"))
    assert result["ok"] is True
    assert Path(result["files"]["release.zip"]).is_file()
    assert "master.wav" in manifest["artifacts_sha256"]
    assert len(manifest["artifacts_sha256"]["master.wav"]) == 64
    assert metadata["isrc"] == ""
    assert metadata["isrc_status"] == "UNREGISTERED"
    assert {"lyrics.txt", "recipe.json", "metadata.csv", "release_notes.txt"} <= set(result["files"])
    assert "Test Artist" in (release_dir / "release_notes.txt").read_text(encoding="utf-8")
    assert (release_dir / "metadata.csv").is_file()
