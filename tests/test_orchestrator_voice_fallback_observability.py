from types import SimpleNamespace

import modules
from app.core.stages import vocal as vocal_stage


def test_voice_fallback_preserves_primary_synth_failure_and_invalid_secondary_output(monkeypatch, tmp_path):
    """Отчёт о попытках сохраняется; системный TTS — только явным флагом.

    Раньше последней ступенью молча был `pyttsx3` (голос Windows), и человек
    слышал «виндовский» голос вместо своего. Теперь ступень есть, но включается
    `ZSMM_ALLOW_SYSTEM_TTS=1`; без флага — честный BLOCKED с той же историей
    попыток.
    """
    monkeypatch.setenv("ZSMM_ALLOW_SYSTEM_TTS", "1")

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


def test_voice_without_neural_tts_is_honestly_blocked(monkeypatch, tmp_path):
    """Без флага системный голос не подставляется: BLOCKED и причина."""
    monkeypatch.delenv("ZSMM_ALLOW_SYSTEM_TTS", raising=False)
    module = SimpleNamespace(
        synth=lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("no engine")),
        synthesize=lambda *_a: None,
    )
    monkeypatch.setattr(modules, "voice_synth", module, raising=False)
    monkeypatch.setattr(
        vocal_stage, "_pyttsx3_speak",
        lambda *_args: (_ for _ in ()).throw(AssertionError("системный TTS запрещён")),
    )

    result = vocal_stage._stage_voice_synth("test lyrics", tmp_path)

    assert result["ok"] is False and result["blocked"] is True
    assert result["engine"] == "BLOCKED"
    assert "RVC" in result["action"]
