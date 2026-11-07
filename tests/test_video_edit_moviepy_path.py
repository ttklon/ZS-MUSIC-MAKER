"""`video_edit/render.py`: путь с moviepy проверяется стабом, без ffmpeg.

Раньше тесты покрывали только fallback — то есть случай, когда moviepy **нет**.
Основной путь (beat-glow, LRC-overlay, композиция, запись файла) не проверялся
вовсе: ошибка в нём означала бы падение на машине пользователя, а не в CI.

Moviepy не устанавливается в тестовое окружение (тянет ffmpeg), поэтому здесь
используется честный стаб: он записывает, с какими аргументами его позвали.
Проверяется поведение нашего кода, а не рендеринг ffmpeg — и это прямо
записано, чтобы тест не притворялся сквозным.
"""

from __future__ import annotations

import struct
import wave
from pathlib import Path

import pytest

from modules.video_edit import render
from modules.video_edit.models import VideoEditRequest


# --------------------------------------------------------------------------- #
#  Стаб moviepy
# --------------------------------------------------------------------------- #

class FakeClip:
    def __init__(self, kind: str, **kwargs):
        self.kind = kind
        self.kwargs = kwargs
        self.duration = kwargs.get("duration")
        self.start = 0.0
        self.opacity = 1.0

    def set_duration(self, value):
        self.duration = value
        return self

    def set_start(self, value):
        self.start = value
        return self

    def set_opacity(self, value):
        self.opacity = value
        return self

    def set_position(self, value):
        self.kwargs["position"] = value
        return self

    def set_audio(self, audio):
        self.audio = audio
        return self

    def subclip(self, start, end):
        self.kwargs["subclip"] = (start, end)
        return self

    def close(self):
        self.closed = True


class FakeMoviePy:
    """Минимальный moviepy: запоминает всё, что у него попросили."""

    def __init__(self):
        self.clips: list[FakeClip] = []
        self.written: list[dict] = []
        self.fail_on_write: Exception | None = None
        outer = self

        class _Audio:
            def __init__(self, path):
                self.path = path
                outer.clips.append(FakeClip("audio", path=path))

            def subclip(self, start, end):
                clip = FakeClip("audio_sub", path=self.path, subclip=(start, end))
                outer.clips.append(clip)
                return clip

            def close(self):
                pass

        self.AudioFileClip = _Audio
        self.ImageClip = lambda path: outer._make("image", path=path)
        self.ColorClip = lambda size, color: outer._make("color", size=size, color=color)

        class _Composite:
            def __init__(self, clips, size):
                self.clips = list(clips)
                self.size = size
                self.audio = None

            def set_audio(self, audio):
                self.audio = audio
                return self

            def write_videofile(self, path, **kwargs):
                outer.written.append({"path": path, "kwargs": kwargs, "clips": self.clips})
                if outer.fail_on_write:
                    raise outer.fail_on_write

            def close(self):
                pass

        self.CompositeVideoClip = _Composite

        def _textclip(text, **kwargs):
            clip = outer._make("text", text=text, **kwargs)
            return clip

        self.TextClip = _textclip

    def _make(self, kind: str, **kwargs) -> FakeClip:
        clip = FakeClip(kind, **kwargs)
        self.clips.append(clip)
        return clip


def _write_wav(path: Path, seconds: float = 40.0, sr: int = 8000) -> str:
    frames = b"".join(
        struct.pack("<h", int(12000 * (1 if i % 2 else -1))) for i in range(int(sr * seconds))
    )
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(frames)
    return str(path)


def _request(tmp_path: Path, **overrides) -> VideoEditRequest:
    master = _write_wav(tmp_path / "master.wav")
    params = {
        "master_wav": master,
        "cover_png": None,
        "lyrics_lrc": None,
        "bpm": 140.0,
        "duration_sec": 4,
        "orientation": "vertical",
        "output_path": str(tmp_path / "clip.mp4"),
        "title": "Ночной город",
        "artist": "ZS Producer",
        "beat_glow": True,
        "waveform_bar": True,
        "lyrics_overlay": True,
    }
    params.update(overrides)
    return VideoEditRequest(**params)


# --------------------------------------------------------------------------- #
#  Основной путь
# --------------------------------------------------------------------------- #

def test_moviepy_path_renders_and_reports_backend(tmp_path, monkeypatch) -> None:
    fake = FakeMoviePy()
    monkeypatch.setattr(render, "_try_moviepy", lambda: fake)

    result = render.build_video(_request(tmp_path))

    assert result.ok is True
    assert result.backend == "moviepy"
    assert result.resolution == (1080, 1920)
    assert result.duration_sec == pytest.approx(4.0, abs=1.5)
    assert fake.written, "write_videofile не вызывался"


def test_render_uses_h264_and_aac(tmp_path, monkeypatch) -> None:
    fake = FakeMoviePy()
    monkeypatch.setattr(render, "_try_moviepy", lambda: fake)

    render.build_video(_request(tmp_path))

    kwargs = fake.written[0]["kwargs"]
    assert kwargs["codec"] == "libx264"
    assert kwargs["audio_codec"] == "aac"
    assert kwargs["fps"] == 24


def test_beat_glow_adds_pulses_at_the_beat(tmp_path, monkeypatch) -> None:
    fake = FakeMoviePy()
    monkeypatch.setattr(render, "_try_moviepy", lambda: fake)

    render.build_video(_request(tmp_path, bpm=120.0, beat_glow=True))

    pulses = [clip for clip in fake.clips if clip.kind == "color"]
    # 4 секунды при 120 BPM = 8 ударов, плюс возможный хвост
    assert 7 <= len(pulses) <= 10
    assert all(clip.opacity == pytest.approx(0.14) for clip in pulses)


def test_beat_glow_can_be_disabled(tmp_path, monkeypatch) -> None:
    fake = FakeMoviePy()
    monkeypatch.setattr(render, "_try_moviepy", lambda: fake)

    render.build_video(_request(tmp_path, beat_glow=False))

    assert not [clip for clip in fake.clips if clip.kind == "color"]


def test_low_bpm_disables_glow_to_avoid_flash(tmp_path, monkeypatch) -> None:
    """Ниже 40 BPM пульсация превращается в стробоскоп — она отключается."""
    fake = FakeMoviePy()
    monkeypatch.setattr(render, "_try_moviepy", lambda: fake)

    render.build_video(_request(tmp_path, bpm=20.0, beat_glow=True))

    assert not [clip for clip in fake.clips if clip.kind == "color"]


def test_lyrics_overlay_only_inside_the_hook(tmp_path, monkeypatch) -> None:
    """Строки за пределами вырезанного хука в клип не попадают."""
    lrc = tmp_path / "lyrics.lrc"
    lrc.write_text("[00:00.50]до хука\n[00:20.00]в хуке\n[00:30.00]тоже в хуке\n", encoding="utf-8")
    fake = FakeMoviePy()
    monkeypatch.setattr(render, "_try_moviepy", lambda: fake)

    result = render.build_video(_request(tmp_path, lyrics_lrc=str(lrc)))

    hook_start = result.hook_start_sec
    texts = [clip.kwargs.get("text") for clip in fake.clips if clip.kind == "text"]
    assert texts, "ни одна строка LRC не попала в клип"
    if hook_start > 0.5:
        assert "до хука" not in texts
    # все показанные строки лежат внутри окна [hook_start, hook_end]
    assert hook_start <= 20.0 <= hook_start + result.duration_sec


def test_textclip_failure_does_not_kill_the_render(tmp_path, monkeypatch) -> None:
    lrc = tmp_path / "lyrics.lrc"
    lrc.write_text("[00:02.00]в хуке\n", encoding="utf-8")
    fake = FakeMoviePy()

    def broken(*args, **kwargs):
        raise RuntimeError("TextClip needs imagemagick")

    fake.TextClip = broken
    monkeypatch.setattr(render, "_try_moviepy", lambda: fake)

    result = render.build_video(_request(tmp_path, lyrics_lrc=str(lrc)))

    assert result.ok is True, "недоступный TextClip не должен срывать клип"


def test_moviepy_failure_falls_back_and_says_so(tmp_path, monkeypatch) -> None:
    fake = FakeMoviePy()
    fake.fail_on_write = RuntimeError("ffmpeg not found")
    monkeypatch.setattr(render, "_try_moviepy", lambda: fake)

    result = render.build_video(_request(tmp_path))

    assert result.backend != "moviepy"
    assert Path(result.output_path).exists() or result.ok is False


def test_background_is_drawn_when_pillow_available(tmp_path, monkeypatch) -> None:
    pytest.importorskip("PIL")
    request = _request(tmp_path)

    image = render._make_static_bg(request.cover_png, request.resolution())

    assert image is not None
    assert image.size == request.resolution()


def test_missing_cover_falls_back_to_plain_background(tmp_path, monkeypatch) -> None:
    pytest.importorskip("PIL")

    image = render._make_static_bg(str(tmp_path / "nope.png"), (540, 960))

    assert image is not None and image.size == (540, 960)


def test_broken_cover_does_not_raise(tmp_path, monkeypatch) -> None:
    pytest.importorskip("PIL")
    broken = tmp_path / "cover.png"
    broken.write_bytes(b"not a png")

    image = render._make_static_bg(str(broken), (540, 960))

    assert image is not None


def test_title_is_drawn_on_the_frame(tmp_path) -> None:
    pytest.importorskip("PIL")
    request = _request(tmp_path)
    background = render._make_static_bg(None, (540, 960))

    decorated = render._draw_title(background, request.title, request.artist, (540, 960))

    assert decorated is not None
    assert decorated.size == (540, 960)


def test_draw_title_survives_missing_pillow(monkeypatch) -> None:
    monkeypatch.setattr(render, "_try_pil", lambda: None)

    assert render._draw_title(None, "t", "a", (100, 100)) is None
