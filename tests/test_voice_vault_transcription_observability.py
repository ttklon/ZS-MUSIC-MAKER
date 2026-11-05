"""Regression coverage for Voice Vault transcription backend diagnostics."""

import sys
import types

from modules import voice_vault as vault


def test_transcription_reports_each_unavailable_backend(monkeypatch, tmp_path, caplog):
    recording = tmp_path / "voice.wav"
    recording.write_bytes(b"placeholder")
    monkeypatch.setitem(sys.modules, "faster_whisper", types.SimpleNamespace())

    def fail_whisper_model(name):
        raise RuntimeError("model cache unavailable")

    monkeypatch.setitem(
        sys.modules, "whisper", types.SimpleNamespace(load_model=fail_whisper_model)
    )

    transcript, diagnostics = vault._transcribe_with_diagnostics(recording)

    assert transcript is None
    assert diagnostics["ok"] is False
    assert diagnostics["engine"] is None
    assert [attempt["engine"] for attempt in diagnostics["attempts"]] == [
        "faster_whisper",
        "whisper",
    ]
    assert diagnostics["attempts"][0]["ok"] is False
    assert diagnostics["attempts"][1]["error"] == "RuntimeError: model cache unavailable"
    assert "faster_whisper transcription unavailable" in caplog.text
    assert "whisper transcription unavailable" in caplog.text


def test_add_recording_persists_transcription_diagnostics(monkeypatch, tmp_path):
    vault_dir = tmp_path / "vault"
    recording = tmp_path / "voice.wav"
    recording.write_bytes(b"voice")
    monkeypatch.setattr(vault, "VAULT_DIR", vault_dir)
    monkeypatch.setattr(vault, "INDEX_FILE", vault_dir / "index.json")
    monkeypatch.setattr(
        vault,
        "_transcribe_with_diagnostics",
        lambda path: (None, {"ok": False, "engine": None, "attempts": [{"engine": "whisper", "ok": False, "error": "ImportError: unavailable"}]}),
    )

    result = vault.add_recording(str(recording), transcribe=True)

    assert result["ok"] is True
    assert result["item"]["transcript"] is None
    assert result["item"]["transcription"] == {
        "ok": False,
        "engine": None,
        "attempts": [
            {"engine": "whisper", "ok": False, "error": "ImportError: unavailable"}
        ],
    }
