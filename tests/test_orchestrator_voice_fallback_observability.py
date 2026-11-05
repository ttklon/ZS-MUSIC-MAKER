from types import SimpleNamespace

import modules
from app.core.stages import vocal as vocal_stage


def test_voice_fallback_preserves_primary_synth_failure_and_invalid_secondary_output(monkeypatch, tmp_path):
    def fail_synth(*_args, **_kwargs):
        raise RuntimeError("primary engine offline")

    module = SimpleNamespace(synth=fail_synth, synthesize=lambda *_args: None)
    monkeypatch.setattr(modules, "voice_synth", module, raising=False)
    monkeypatch.setattr(
        vocal_stage,
        "_pyttsx3_speak",
        lambda *_args: {"ok": True, "engine": "pyttsx3", "fallback_used": True},
    )

    result = vocal_stage._stage_voice_synth("test lyrics", tmp_path)

    assert result["ok"] is True
    assert result["engine"] == "pyttsx3"
    assert result["fallback_attempts"] == [
        {
            "engine": "voice_synth.synth",
            "status": "failed",
            "error": "RuntimeError: primary engine offline",
        },
        {
            "engine": "voice_synth.synthesize",
            "status": "invalid_output",
            "error": "expected result dict or existing path, got NoneType",
        },
    ]
