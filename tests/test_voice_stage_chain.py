"""`app/core/stages/vocal.py`: цепочка голоса и её честные отказы.

Порядок попыток — `voice_synth.synth` → `voice_synth.synthesize` → `pyttsx3`
→ numpy-каркас. Покрытие было 27 %: тесты дёргали стадию целиком на машине без
TTS и получали BLOCKED, но ни одна ветка выбора не проверялась. Здесь каждая
ступень подменяется и проверяется, что отказ называет причину, а не молчит.

Стаб-подмена — не имитация синтеза речи: тесты проверяют нашу логику выбора и
отчётности. Это прямо записано, чтобы результат не приняли за проверку звука.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

import modules as modules_pkg

from app.core.stages import vocal as vocal_stage


def _wav(path: Path, seconds: float = 0.5, sr: int = 8000) -> str:
    t = np.arange(int(sr * seconds)) / sr
    sf.write(path, 0.2 * np.sin(2 * np.pi * 200 * t), sr)
    return str(path)


@pytest.fixture
def out_dir(tmp_path) -> Path:
    directory = tmp_path / "out"
    directory.mkdir()
    return directory


# --------------------------------------------------------------------------- #
#  voice_synth.synth
# --------------------------------------------------------------------------- #

def test_synth_success_is_reported_with_engine(out_dir, monkeypatch, tmp_path) -> None:
    audio = _wav(tmp_path / "voice.wav")
    module = types.SimpleNamespace(synth=lambda text, **kwargs: audio)
    monkeypatch.setattr(modules_pkg, "voice_synth", module, raising=False)

    result = vocal_stage._stage_voice_synth("строка текста", out_dir)

    assert result["ok"] is True
    assert result["engine"] == "voice_synth.synth"
    assert result["path"] == audio


def test_synth_empty_output_falls_through_and_is_reported(out_dir, monkeypatch) -> None:
    calls: list[str] = []

    def fake_synth(text, **kwargs):
        return ""  # пустой путь — не успех

    module = types.SimpleNamespace(
        synth=fake_synth,
        synthesize=lambda text, path: calls.append(text)
        or {"ok": True, "path": path, "fallback_attempts": []},
    )
    monkeypatch.setattr(modules_pkg, "voice_synth", module, raising=False)

    result = vocal_stage._stage_voice_synth("строка", out_dir)

    # ступень `synthesize` возвращает dict — стадия обязана сохранить в нём
    # след отказа `synth`, а не выдать успех второй ступени за чистый старт
    assert result["ok"] is True
    assert calls, "вторая ступень не была опробована"
    attempts = result.get("fallback_attempts") or []
    assert any(item["status"] == "invalid_output" for item in attempts), (
        "отказ `synth` (пустой путь) обязан остаться в отчёте"
    )


def test_tiny_file_is_not_accepted_as_audio(out_dir, monkeypatch, tmp_path) -> None:
    """Файл на 10 байт — не голос, а огрызок: он не должен считаться успехом."""
    tiny = tmp_path / "tiny.wav"
    tiny.write_bytes(b"RIFF" + b"\0" * 6)
    module = types.SimpleNamespace(synth=lambda text, **kwargs: str(tiny))
    monkeypatch.setattr(modules_pkg, "voice_synth", module, raising=False)

    result = vocal_stage._stage_voice_synth("строка", out_dir)

    assert result.get("engine") != "voice_synth.synth"
    attempts = result.get("fallback_attempts") or []
    assert any(item["status"] == "invalid_output" for item in attempts)


def test_synth_exception_is_recorded_with_type(out_dir, monkeypatch) -> None:
    def explode(text, **kwargs):
        raise RuntimeError("model weights missing")

    module = types.SimpleNamespace(synth=explode)
    monkeypatch.setattr(modules_pkg, "voice_synth", module, raising=False)

    result = vocal_stage._stage_voice_synth("строка", out_dir)

    attempts = result.get("fallback_attempts") or []
    assert attempts and attempts[0]["error"] == "RuntimeError: model weights missing"


# --------------------------------------------------------------------------- #
#  voice_synth.synthesize
# --------------------------------------------------------------------------- #

def test_synthesize_returning_path_is_accepted(out_dir, monkeypatch, tmp_path) -> None:
    audio = _wav(tmp_path / "voice2.wav")
    module = types.SimpleNamespace(synthesize=lambda text, path: audio)
    monkeypatch.setattr(modules_pkg, "voice_synth", module, raising=False)

    result = vocal_stage._stage_voice_synth("строка", out_dir)

    assert result["ok"] is True and result["path"] == audio


def test_synthesize_returning_dict_is_passed_through(out_dir, monkeypatch) -> None:
    payload = {"ok": False, "blocked": True, "reason": "no engine"}
    module = types.SimpleNamespace(synthesize=lambda text, path: payload)
    monkeypatch.setattr(modules_pkg, "voice_synth", module, raising=False)

    assert vocal_stage._stage_voice_synth("строка", out_dir) == payload


def test_synthesize_invalid_result_is_reported(out_dir, monkeypatch) -> None:
    module = types.SimpleNamespace(synthesize=lambda text, path: 42)
    monkeypatch.setattr(modules_pkg, "voice_synth", module, raising=False)

    result = vocal_stage._stage_voice_synth("строка", out_dir)

    attempts = result.get("fallback_attempts") or []
    assert any(item["status"] == "invalid_output" for item in attempts)


# --------------------------------------------------------------------------- #
#  Границы стадии
# --------------------------------------------------------------------------- #

def test_empty_lyrics_is_refused_before_any_engine(out_dir, monkeypatch) -> None:
    def forbidden(*args, **kwargs):  # pragma: no cover - не должен вызваться
        raise AssertionError("движок вызван без текста")

    monkeypatch.setattr(modules_pkg, "voice_synth", types.SimpleNamespace(synth=forbidden), raising=False)

    result = vocal_stage._stage_voice_synth("   ", out_dir)

    assert result["ok"] is False
    assert result["reason"] == "empty lyrics"
    assert "notice" in result


def test_missing_voice_synth_module_uses_pyttsx3(out_dir, monkeypatch) -> None:
    monkeypatch.delattr(modules_pkg, "voice_synth", raising=False)
    monkeypatch.setitem(sys.modules, "modules.voice_synth", None)
    monkeypatch.setattr(
        vocal_stage, "_pyttsx3_speak", lambda text, path: {"ok": False, "reason": "no pyttsx3"}
    )

    result = vocal_stage._stage_voice_synth("строка", out_dir)

    assert result["ok"] is False
    attempts = result.get("fallback_attempts") or []
    assert attempts[0]["status"] == "unavailable"


# --------------------------------------------------------------------------- #
#  Разбор тональности и эффекты
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    ("key", "expected"),
    [
        ("A minor", ("A", "minor")),
        ("F# major", ("F#", "major")),
        ("C", ("C", "minor")),
        (None, ("A", "minor")),
        ("", ("A", "minor")),
    ],
)
def test_split_key(key, expected) -> None:
    assert vocal_stage._split_key(key) == expected


def test_vocal_fx_without_input_is_honest_bypass(tmp_path) -> None:
    result = vocal_stage._stage_vocal_fx(None, tmp_path, bpm=140.0, key="A minor")

    assert result["ok"] is False
    assert result["fallback_used"] is True
    assert "no vocal_wav" in result["reason"]


def test_vocal_fx_applies_effects_when_module_works(tmp_path, monkeypatch) -> None:
    source = _wav(tmp_path / "vocal.wav")
    seen: dict = {}

    def fake_process(path, out_path, **kwargs):
        seen.update(kwargs)
        Path(out_path).write_bytes(b"RIFF" + b"\0" * 2000)
        return {"ok": True, "path": out_path}

    monkeypatch.setattr(modules_pkg, "vocal_fx", types.SimpleNamespace(process_vocal=fake_process), raising=False)

    result = vocal_stage._stage_vocal_fx(source, tmp_path, bpm=140.0, key="F# major", tune=True)

    assert result["ok"] is True
    assert result["path"].endswith("voice_fx.wav")
    assert seen["tonic"] == "F#" and seen["scale"] == "major"
    assert seen["bpm"] == 140.0 and seen["use_tune"] is True
    assert seen["use_double"] is True and seen["use_throw"] is True


def test_vocal_fx_failure_bypasses_to_original_audio(tmp_path, monkeypatch) -> None:
    """Эффекты не критичны: при сбое микс идёт на исходном вокале, но с пометкой."""
    source = _wav(tmp_path / "vocal.wav")
    monkeypatch.setattr(
        modules_pkg,
        "vocal_fx",
        types.SimpleNamespace(process_vocal=lambda *a, **k: {"ok": False, "reason": "no pedalboard"}),
        raising=False,
    )

    result = vocal_stage._stage_vocal_fx(source, tmp_path, key="A minor")

    assert result["ok"] is True
    assert result["path"] == source
    assert result["engine"] == "bypass"
    assert result["fallback_used"] is True
    assert result["reason"] == "no pedalboard"


def test_vocal_fx_import_error_is_reported_not_raised(tmp_path, monkeypatch) -> None:
    source = _wav(tmp_path / "vocal.wav")
    monkeypatch.delattr(modules_pkg, "vocal_fx", raising=False)
    monkeypatch.setitem(sys.modules, "modules.vocal_fx", None)

    result = vocal_stage._stage_vocal_fx(source, tmp_path, key="A minor")

    assert result["ok"] is True and result["engine"] == "bypass"
    assert "import/run error" in result["reason"]


# --------------------------------------------------------------------------- #
#  pyttsx3 / numpy-каркас
# --------------------------------------------------------------------------- #

def test_scaffold_writes_flagged_placeholder_when_no_tts(tmp_path, monkeypatch) -> None:
    """Без TTS стадия не молчит: пишет каркас и честно помечает его синтетикой."""
    monkeypatch.setitem(sys.modules, "pyttsx3", None)
    target = tmp_path / "voice_preview.wav"

    result = vocal_stage._pyttsx3_speak("первая строка\nвторая строка", str(target))

    assert result["ok"] is True
    assert result["engine"] == "rap_scaffold_numpy_v22"
    assert result["synthetic"] is True and result["blocked"] is True
    assert result["fallback_used"] is True
    assert "NOT a real voice" in result["reason"]
    assert target.exists() and target.stat().st_size > 1000


def test_scaffold_handles_empty_text_without_crashing(tmp_path, monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "pyttsx3", None)

    result = vocal_stage._pyttsx3_speak("", str(tmp_path / "empty.wav"))

    assert result["ok"] is True and result["synthetic"] is True


def test_tts_engine_is_preferred_over_scaffold(tmp_path, monkeypatch) -> None:
    """Если TTS реально создал файл — каркас не подменяет его."""
    target = tmp_path / "tts.wav"

    class _Engine:
        def save_to_file(self, text, path):
            Path(path).write_bytes(b"RIFF" + b"\0" * 4000)

        def runAndWait(self):
            return None

    monkeypatch.setitem(sys.modules, "pyttsx3", types.SimpleNamespace(init=lambda: _Engine()))

    result = vocal_stage._pyttsx3_speak("текст", str(target))

    assert result["engine"] == "pyttsx3"
    assert "synthetic" not in result
    assert result["path"] == str(target)


# --------------------------------------------------------------------------- #
#  _stage_rvc — правило P0.05
# --------------------------------------------------------------------------- #

def test_rvc_is_blocked_for_synthetic_upstream(tmp_path) -> None:
    result = vocal_stage._stage_rvc(
        _wav(tmp_path / "v.wav"), tmp_path, upstream_synthetic=True
    )

    assert result["ok"] is True and result["blocked"] is True
    assert result["path"] == ""
    assert "P0.05" in result["reason"]


def test_rvc_is_blocked_without_pth_model(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        modules_pkg, "rvc_manager", types.SimpleNamespace(infer=lambda *a, **k: "/never"),
        raising=False,
    )

    result = vocal_stage._stage_rvc(
        _wav(tmp_path / "v.wav"), tmp_path, model_path=str(tmp_path / "nope.pth")
    )

    assert result["ok"] is True and result["blocked"] is True
    assert "RVC .pth model not available" in result["reason"]


def test_rvc_rejects_non_pth_suffix(tmp_path, monkeypatch) -> None:
    fake_model = tmp_path / "model.bin"
    fake_model.write_bytes(b"x")
    monkeypatch.setattr(modules_pkg, "rvc_manager", types.SimpleNamespace(
        infer=lambda *a, **k: "/never"), raising=False)

    result = vocal_stage._stage_rvc(
        _wav(tmp_path / "v.wav"), tmp_path, model_path=str(fake_model)
    )

    assert result["blocked"] is True
    assert "model.bin" in result["reason"]


def test_rvc_runs_in_process_when_model_present(tmp_path, monkeypatch) -> None:
    model = tmp_path / "my_voice.pth"
    model.write_bytes(b"x")
    seen: dict = {}

    def fake_infer(path, **kwargs):
        seen.update(kwargs)
        return str(tmp_path / "out" / "voice_rvc.wav")

    monkeypatch.setattr(modules_pkg, "rvc_manager", types.SimpleNamespace(infer=fake_infer), raising=False)
    monkeypatch.delenv("ZSMM_RVC_PYTHON", raising=False)

    result = vocal_stage._stage_rvc(
        _wav(tmp_path / "v.wav"), tmp_path, model_path=str(model), pitch_shift=3
    )

    assert result["ok"] is True and result["engine"] == "rvc_python"
    assert result["execution"] == "in_process"
    assert result["path"].endswith("voice_rvc.wav")
    assert seen["pitch_shift"] == 3 and seen["index_path"] is None


def test_rvc_reports_isolated_python_when_env_set(tmp_path, monkeypatch) -> None:
    model = tmp_path / "my_voice.pth"
    model.write_bytes(b"x")
    monkeypatch.setattr(modules_pkg, "rvc_manager", types.SimpleNamespace(
        infer=lambda *a, **k: ""), raising=False)
    monkeypatch.setenv("ZSMM_RVC_PYTHON", "/opt/py/bin/python")

    result = vocal_stage._stage_rvc(
        _wav(tmp_path / "v.wav"), tmp_path, model_path=str(model)
    )

    assert result["execution"] == "isolated_python"
    # пустой ответ infer → путь по умолчанию, а не пустая строка
    assert result["path"].endswith("voice_rvc.wav")


def test_rvc_runtime_error_is_blocked_not_crash(tmp_path, monkeypatch) -> None:
    model = tmp_path / "my_voice.pth"
    model.write_bytes(b"x")

    def boom(*a, **k):
        raise RuntimeError("RVC env not installed")

    monkeypatch.setattr(modules_pkg, "rvc_manager", types.SimpleNamespace(infer=boom), raising=False)

    result = vocal_stage._stage_rvc(
        _wav(tmp_path / "v.wav"), tmp_path, model_path=str(model)
    )

    assert result["ok"] is True and result["blocked"] is True
    assert result["reason"] == "RVC env not installed"


def test_rvc_unexpected_error_is_not_disguised_as_success(tmp_path, monkeypatch) -> None:
    model = tmp_path / "my_voice.pth"
    model.write_bytes(b"x")

    def boom(*a, **k):
        raise ValueError("bad index")

    monkeypatch.setattr(modules_pkg, "rvc_manager", types.SimpleNamespace(infer=boom), raising=False)

    result = vocal_stage._stage_rvc(
        _wav(tmp_path / "v.wav"), tmp_path, model_path=str(model)
    )

    assert result["ok"] is False
    assert result["reason"] == "bad index"


@pytest.mark.parametrize(
    "key,expected",
    [("f#-major", ("F#", "major")), ("A dorian", ("A", "dorian")), ("C", ("C", "minor"))],
)
def test_split_key_normalises_unknown_scales(key, expected) -> None:
    assert vocal_stage._split_key(key) == expected


def test_synthesize_raising_is_recorded_not_swallowed(out_dir, monkeypatch) -> None:
    class Boom(types.SimpleNamespace):
        def __init__(self):
            super().__init__(synth=lambda *a, **k: "")

        def synthesize(self, *a, **k):
            raise OSError("disk full")

    monkeypatch.setattr(modules_pkg, "voice_synth", Boom(), raising=False)

    result = vocal_stage._stage_voice_synth("строка", out_dir)

    attempts = result["fallback_attempts"]
    statuses = {(item["engine"], item["status"]) for item in attempts}
    assert ("voice_synth.synthesize", "failed") in statuses
    assert ("voice_synth.synth", "invalid_output") in statuses
    assert any("disk full" in item["error"] for item in attempts)


def test_scaffold_marks_unknown_vowel_words(tmp_path, monkeypatch) -> None:
    """Слова без знакомых гласных не выпадают из каркаса (дефолт «а»)."""
    monkeypatch.setitem(sys.modules, "pyttsx3", None)
    target = tmp_path / "consonants.wav"

    result = vocal_stage._pyttsx3_speak("бррр\nтссс", str(target))

    assert result["ok"] is True
    data, sr = sf.read(str(target))
    assert sr == 22050
    assert float(np.max(np.abs(data))) > 0.0


def test_scaffold_survives_missing_scipy(tmp_path, monkeypatch) -> None:
    """Без scipy каркас не падает: сегменты просто не фильтруются."""
    monkeypatch.setitem(sys.modules, "pyttsx3", None)
    monkeypatch.setitem(sys.modules, "scipy.signal", None)

    result = vocal_stage._pyttsx3_speak("мама мыла раму", str(tmp_path / "noscipy.wav"))

    assert result["ok"] is True and result["synthetic"] is True


def test_scaffold_failure_is_reported_honestly(tmp_path, monkeypatch) -> None:
    """Если и каркас не смог (нет soundfile) — ok=False с причиной, не тишина."""
    monkeypatch.setitem(sys.modules, "pyttsx3", None)
    monkeypatch.setitem(sys.modules, "soundfile", None)

    result = vocal_stage._pyttsx3_speak("текст", str(tmp_path / "broken.wav"))

    assert result["ok"] is False
    assert result["fallback_used"] is False
    assert "scaffold failed" in result["reason"]


def test_split_key_falls_back_to_minor_for_unknown_scale() -> None:
    assert vocal_stage._split_key("A blues") == ("A", "minor")
