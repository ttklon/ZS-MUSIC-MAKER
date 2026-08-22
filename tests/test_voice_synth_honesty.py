from __future__ import annotations

import logging
from pathlib import Path

import modules.voice_synth as voice_synth


def test_synth_uses_verified_primary_output(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(voice_synth, "OUT_DIR", tmp_path)
    calls: list[str] = []

    def write_silero(_text: str, path: str, speaker: str) -> bool:
        calls.append(speaker)
        Path(path).write_bytes(b"a" * 101)
        return True

    monkeypatch.setattr(voice_synth, "_synth_silero", write_silero)

    result = voice_synth.synth("тест", engine="silero", out_name="draft.wav", gender="female")

    assert result == str(tmp_path / "draft.wav")
    assert calls == ["kseniya"]


def test_synth_falls_back_only_when_prior_engine_has_no_verified_output(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(voice_synth, "OUT_DIR", tmp_path)
    calls: list[str] = []

    def fail_xtts(*_args, **_kwargs) -> bool:
        calls.append("xtts")
        return False

    def write_silero(*_args, **_kwargs) -> bool:
        calls.append("silero")
        (tmp_path / "draft.wav").write_bytes(b"a" * 101)
        return True

    monkeypatch.setattr(voice_synth, "_synth_xtts", fail_xtts)
    monkeypatch.setattr(voice_synth, "_synth_silero", write_silero)

    result = voice_synth.synth("тест", engine="xtts", out_name="draft.wav")

    assert result == str(tmp_path / "draft.wav")
    assert calls == ["xtts", "silero"]


def test_synth_returns_empty_and_logs_when_all_fake_backends_fail(tmp_path: Path, monkeypatch, caplog) -> None:
    monkeypatch.setattr(voice_synth, "OUT_DIR", tmp_path)
    for backend in ("_synth_silero", "_synth_xtts", "_synth_bark", "_synth_pyttsx3", "_synth_gtts"):
        monkeypatch.setattr(voice_synth, backend, lambda *_args, **_kwargs: False)

    with caplog.at_level(logging.WARNING, logger=voice_synth.LOGGER.name):
        result = voice_synth.synth("тест", engine="auto", out_name="missing.wav")

    assert result == ""
    assert "all draft voice engines failed or are unavailable; returning empty result" in caplog.text
