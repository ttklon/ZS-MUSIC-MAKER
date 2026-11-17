from __future__ import annotations

import logging
from pathlib import Path

import modules.voice_synth as voice_synth


def _voice(path):
    import numpy as np
    from modules.dsp.wavio import write_wav

    write_wav(path, np.sin(np.arange(8000) * 0.1).astype("float32") * 0.2, 8000)


def test_synth_uses_verified_primary_output(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(voice_synth, "OUT_DIR", tmp_path)
    calls: list[str] = []

    def write_silero(_text: str, path: str, speaker: str) -> bool:
        calls.append(speaker)
        _voice(path)
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

    def write_silero(text, path, **_kwargs) -> bool:
        calls.append("silero")
        _voice(path)
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


def test_auto_never_uses_system_or_cloud_without_permission(tmp_path, monkeypatch):
    monkeypatch.setattr(voice_synth, "OUT_DIR", tmp_path)
    monkeypatch.delenv("ZSMM_ALLOW_SYSTEM_TTS", raising=False)
    monkeypatch.setattr("app.core.net_policy.network_allowed", lambda: False)
    for name in ("_synth_silero", "_synth_xtts", "_synth_bark"):
        monkeypatch.setattr(voice_synth, name, lambda *a, **kw: False)
    for name in ("_synth_pyttsx3", "_synth_gtts"):
        monkeypatch.setattr(voice_synth, name, lambda *a, **kw: (_ for _ in ()).throw(AssertionError("forbidden fallback")))
    assert voice_synth.synth("текст", engine="auto") == ""


def test_pipeline_voice_outputs_are_project_local(tmp_path, monkeypatch):
    from app.core.stages.vocal import _stage_voice_synth
    import numpy as np
    from modules.dsp.wavio import write_wav

    paths = []

    def silero(text, path, **kwargs):
        paths.append(path)
        write_wav(path, np.sin(np.arange(8000) * 0.1).astype("float32") * 0.2, 8000)
        return True

    monkeypatch.setattr(voice_synth, "_synth_silero", silero)
    for name in ("one", "two"):
        project = tmp_path / name
        project.mkdir()
        result = _stage_voice_synth("текст", project)
        assert result["ok"]
        assert Path(result["path"]).parent == project
    assert paths[0] != paths[1]


def test_silero_audio_writes_without_torchaudio(tmp_path, monkeypatch):
    import sys
    import types
    import numpy as np
    import soundfile as sf

    class Audio:
        def detach(self):
            return self

        def cpu(self):
            return self

        def numpy(self):
            return np.sin(np.arange(4800) * 0.1).astype("float32") * 0.2

    model = types.SimpleNamespace(apply_tts=lambda **kw: Audio())
    torch = types.SimpleNamespace(hub=types.SimpleNamespace(load=lambda **kw: (model, None)))
    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setitem(sys.modules, "torchaudio", None)
    path = tmp_path / "silero.wav"
    assert voice_synth._synth_silero("текст", str(path))
    audio, sr = sf.read(path)
    assert sr == 48000 and len(audio) == 4800
