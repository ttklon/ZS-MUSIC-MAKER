"""`VideoEditRequest` — контракт запроса, который обязан работать.

Класс объявлен без `@dataclass` при наличии аннотированных полей и значений по
умолчанию. Python не создаёт по аннотациям `__init__`, поэтому
`VideoEditRequest(master_wav=...)` падал с `TypeError: takes no arguments`.

Следствие: `build_release_edits` — публичная функция пакета
(`modules/video_edit/__init__.py` реэкспортирует её как часть API) — не могла
создать ни одного запроса, то есть релизные нарезки TikTok/Reels/Shorts не
собирались вообще. Стадия `_stage_release_pack` их не вызывает, поэтому ни один
тест и ни один прогон пайплайна этого не замечал.
"""

from __future__ import annotations

import json
import struct
import wave
from pathlib import Path

import pytest

from modules.video_edit import edits as edits_module
from modules.video_edit.models import VideoEditRequest, VideoEditResult


def _write_wav(path: Path, seconds: float = 6.0, sr: int = 8000) -> str:
    frames = b"".join(
        struct.pack("<h", int(9000 * (1 if i % 2 else -1))) for i in range(int(sr * seconds))
    )
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(frames)
    return str(path)


# --------------------------------------------------------------------------- #
#  Модель запроса
# --------------------------------------------------------------------------- #

def test_request_accepts_keyword_arguments() -> None:
    request = VideoEditRequest(master_wav="master.wav", title="Ночь", bpm=128.0)

    assert request.master_wav == "master.wav"
    assert request.title == "Ночь"
    assert request.bpm == 128.0
    assert request.orientation == "vertical"


def test_request_defaults_are_sane() -> None:
    request = VideoEditRequest(master_wav="m.wav")

    assert request.duration_sec == 20
    assert request.beat_glow is True
    assert request.lyrics_overlay is True
    assert request.output_path.endswith(".mp4")


@pytest.mark.parametrize(
    ("orientation", "expected"),
    [("vertical", (1080, 1920)), ("horizontal", (1920, 1080)), ("square", (1080, 1080))],
)
def test_resolution_follows_orientation(orientation: str, expected: tuple[int, int]) -> None:
    assert VideoEditRequest(master_wav="m.wav", orientation=orientation).resolution() == expected


def test_unknown_orientation_is_square() -> None:
    assert VideoEditRequest(master_wav="m.wav", orientation="weird").resolution() == (1080, 1080)


def test_result_serializes_resolution_as_list() -> None:
    result = VideoEditResult(
        ok=True,
        output_path="a.mp4",
        duration_sec=1.0,
        resolution=(1080, 1920),
        backend="moviepy",
        hook_start_sec=2.0,
    )

    payload = result.to_dict()

    assert payload["resolution"] == [1080, 1920]
    assert payload["backend"] == "moviepy"


# --------------------------------------------------------------------------- #
#  Публичный API пакета
# --------------------------------------------------------------------------- #

def test_build_release_edits_builds_three_orientations(tmp_path, monkeypatch) -> None:
    """Функция из `__all__` обязана работать, а не падать на первом запросе."""
    monkeypatch.setattr(edits_module, "build_video", lambda req: VideoEditResult(
        ok=True,
        output_path=req.output_path,
        duration_sec=float(req.duration_sec),
        resolution=req.resolution(),
        backend="stub",
        hook_start_sec=0.0,
    ))
    master = _write_wav(tmp_path / "master.wav")

    manifest = edits_module.build_release_edits(
        master, None, None, 140.0, "Ночь", "ZS Producer", str(tmp_path / "edits")
    )

    assert set(manifest) == {"tiktok_edit.mp4", "reels_edit.mp4", "shorts_edit.mp4"}
    written = json.loads((tmp_path / "edits" / "video_edits_manifest.json").read_text("utf-8"))
    assert written["tiktok_edit.mp4"]["resolution"] == [1080, 1920]


def test_build_release_edits_passes_the_right_durations(tmp_path, monkeypatch) -> None:
    seen: list[int] = []

    def capture(req):
        seen.append(req.duration_sec)
        return VideoEditResult(
            ok=True,
            output_path=req.output_path,
            duration_sec=float(req.duration_sec),
            resolution=req.resolution(),
            backend="stub",
            hook_start_sec=0.0,
        )

    monkeypatch.setattr(edits_module, "build_video", capture)
    master = _write_wav(tmp_path / "master.wav")

    edits_module.build_release_edits(
        master, None, None, 140.0, "Ночь", "ZS Producer", str(tmp_path / "e")
    )

    assert seen == [20, 30, 20]


def test_self_test_of_the_module_passes() -> None:
    assert edits_module._self_test() is True
