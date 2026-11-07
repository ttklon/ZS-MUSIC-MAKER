"""T8: fallback вертикального клипа действительно пишет WAV-хук.

До доработки `modules/video_edit/render.py` использовал `wave`, `struct` и
`_read_wav_mono`, не импортировав их: без `moviepy` пользователь получал
`NameError` вместо `*_HOOK.wav` — то есть «фолбэк» не существовал.
"""

from __future__ import annotations

import types
import wave
from pathlib import Path

import numpy as np
import pytest

from modules.video_edit import render
from modules.video_edit.audio import _read_wav_mono
from modules.video_edit.models import VideoEditRequest  # noqa: F401 - тип запроса


def _write_wav(path: Path, sr: int = 44100, seconds: float = 3.0, channels: int = 2) -> Path:
    t = np.arange(int(sr * seconds)) / sr
    mono = (0.3 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)
    data = np.stack([mono] * channels, axis=1) if channels > 1 else mono
    import soundfile as sf

    sf.write(path, data, sr)
    return path


def _request(tmp_path: Path, master: Path):
    """Запрос как их реально строит пайплайн: `VideoEditRequest` — не dataclass,
    а набор атрибутов (см. `modules/video_edit/models.py`), поэтому здесь
    используется объект с теми же полями."""
    cover = tmp_path / "cover.png"
    cover.write_bytes(b"\x89PNG\r\n\x1a\n")  # не читается: fallback не должен её требовать
    return types.SimpleNamespace(
        master_wav=str(master),
        cover_png=str(cover),
        lyrics_lrc=str(tmp_path / "lyrics.lrc"),
        output_path=str(tmp_path / "clip.mp4"),
        bpm=128,
        duration_sec=20,
        orientation="vertical",
        title="",
        artist="",
        beat_glow=True,
        waveform_bar=True,
        lyrics_overlay=True,
        resolution=lambda: (1080, 1920),
    )


# ------------------------------------------------------------------ audio
@pytest.mark.parametrize("channels", [1, 2])
def test_read_wav_mono_handles_mono_and_stereo(tmp_path, channels) -> None:
    path = _write_wav(tmp_path / f"m{channels}.wav", sr=8000, seconds=0.5, channels=channels)

    samples, sr = _read_wav_mono(str(path))

    assert sr == 8000
    assert len(samples) == pytest.approx(4000, abs=2)
    assert max(abs(value) for value in samples) < 1.0


def test_read_wav_mono_rejects_unsupported_width(tmp_path) -> None:
    path = tmp_path / "bad.wav"
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(1)  # 8 бит не поддерживается осознанно
        wf.setframerate(8000)
        wf.writeframes(b"\x00" * 100)

    with pytest.raises(ValueError):
        _read_wav_mono(str(path))


# ------------------------------------------------------------------ fallback
def test_fallback_writes_hook_wav(tmp_path) -> None:
    master = _write_wav(tmp_path / "master.wav", seconds=4.0)
    req = _request(tmp_path, master)

    result = render._build_fallback(req, 1.0, 3.0)

    hook = Path(result.output_path)
    assert hook.exists(), "fallback не создал ни одного файла"
    assert hook.name.endswith("_HOOK.wav")
    assert result.backend == "fallback_wav"
    with wave.open(str(hook), "rb") as wf:
        duration = wf.getnframes() / wf.getframerate()
    assert duration == pytest.approx(2.0, abs=0.05)


def test_fallback_reports_honest_failure_for_broken_master(tmp_path) -> None:
    """Нечитаемый мастер — не повод врать: ok=False и причина."""
    master = tmp_path / "broken.wav"
    master.write_bytes(b"not a wav")
    req = _request(tmp_path, master)

    result = render._build_fallback(req, 0.0, 5.0)

    assert result.ok is False
    assert result.backend != "fallback_wav"
    reason = (result.reason or "").lower()
    assert reason, "отказ обязан называть причину, а не молчать"
    assert "fallback wav" in reason or "format" in reason or "wav" in reason
    # инструкция для ручной сборки всё равно пишется
    assert (tmp_path / "clip_build_manually.txt").exists()


def test_build_video_uses_fallback_without_moviepy(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(render, "_try_moviepy", lambda: None)
    master = _write_wav(tmp_path / "master.wav", seconds=4.0)
    req = _request(tmp_path, master)

    result = render.build_video(req)

    assert result.backend in ("fallback_wav", "fallback_txt")
    assert Path(result.output_path).exists()
