from __future__ import annotations

from pathlib import Path

import modules.voice_cleaner as cleaner


def test_clean_vocal_records_successful_compatibility_copy(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "input.wav"
    target = tmp_path / "output.wav"
    source.write_bytes(b"raw")
    monkeypatch.setattr(cleaner, "clean_vocal_chain", lambda *args, **kwargs: {"ok": False, "reason": "DSP failed"})

    result = cleaner.clean_vocal(str(source), str(target))

    assert result["ok"] is False
    assert result["fallback_copy"] == {"ok": True, "path": str(target)}
    assert target.read_bytes() == b"raw"


def test_clean_vocal_records_failed_compatibility_copy(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "input.wav"
    target = tmp_path / "output.wav"
    monkeypatch.setattr(cleaner, "clean_vocal_chain", lambda *args, **kwargs: {"ok": False, "reason": "DSP failed"})

    def fail_copy(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(cleaner.shutil, "copy", fail_copy)
    result = cleaner.clean_vocal(str(source), str(target))

    assert result["ok"] is False
    assert result["fallback_copy"] == {"ok": False, "error": "OSError: disk full"}
    assert result["reason"] == "DSP failed; raw fallback copy failed: disk full"
