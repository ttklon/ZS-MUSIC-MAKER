"""Regression coverage for observable optional MP3 export in mixdown."""

import sys
import types

from modules import mixdown


class _ExportingAudioSegment:
    @classmethod
    def from_wav(cls, path):
        return cls()

    def export(self, path, format, bitrate):
        assert format == "mp3"
        assert bitrate == "320k"
        with open(path, "wb") as handle:
            handle.write(b"mp3")


class _FailingAudioSegment:
    @classmethod
    def from_wav(cls, path):
        return cls()

    def export(self, path, format, bitrate):
        raise OSError("encoder unavailable")


def _fake_pydub(audio_segment):
    return types.SimpleNamespace(AudioSegment=audio_segment)


def test_mastering_status_reports_successful_optional_mp3_export(monkeypatch, tmp_path):
    mix_source = tmp_path / "input.wav"
    mix_source.write_bytes(b"wav")
    monkeypatch.setattr(mixdown, "OUTPUT_DIR", str(tmp_path))
    monkeypatch.setitem(sys.modules, "matchering", None)
    monkeypatch.setitem(sys.modules, "pydub", _fake_pydub(_ExportingAudioSegment))

    result = mixdown.master_with_matchering_status(
        str(mix_source), "unused-reference.wav", "master.wav"
    )

    assert result["engine"] == "copy_fallback"
    assert result["mp3_export"] == {
        "ok": True,
        "path": str(tmp_path / "master.mp3"),
    }
    assert (tmp_path / "master.wav").read_bytes() == b"wav"
    assert (tmp_path / "master.mp3").read_bytes() == b"mp3"


def test_mastering_status_keeps_wav_and_reports_optional_mp3_failure(
    monkeypatch, tmp_path, caplog
):
    mix_source = tmp_path / "input.wav"
    mix_source.write_bytes(b"wav")
    monkeypatch.setattr(mixdown, "OUTPUT_DIR", str(tmp_path))
    monkeypatch.setitem(sys.modules, "matchering", None)
    monkeypatch.setitem(sys.modules, "pydub", _fake_pydub(_FailingAudioSegment))

    result = mixdown.master_with_matchering_status(
        str(mix_source), "unused-reference.wav", "master.wav"
    )

    assert result["master_wav"] == str(tmp_path / "master.wav")
    assert (tmp_path / "master.wav").read_bytes() == b"wav"
    assert result["mp3_export"] == {
        "ok": False,
        "path": None,
        "error": "encoder unavailable",
    }
    assert "MP3 export unavailable" in caplog.text
