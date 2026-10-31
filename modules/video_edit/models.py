# -*- coding: utf-8 -*-
"""
modules/video_edit/models.py — запрос и результат рендера вертикального видео.
"""

from __future__ import annotations

from dataclasses import dataclass


class VideoEditRequest:
    master_wav: str
    cover_png: str | None = None
    lyrics_lrc: str | None = None
    bpm: float = 140.0
    duration_sec: int = 20
    orientation: str = "vertical"  # vertical | horizontal | square
    output_path: str = "output/tiktok_edit.mp4"
    title: str = ""
    artist: str = ""
    beat_glow: bool = True
    waveform_bar: bool = True
    lyrics_overlay: bool = True

    def resolution(self) -> tuple[int, int]:
        if self.orientation == "vertical":
            return (1080, 1920)
        if self.orientation == "horizontal":
            return (1920, 1080)
        return (1080, 1080)


@dataclass
class VideoEditResult:
    ok: bool
    output_path: str
    duration_sec: float
    resolution: tuple[int, int]
    backend: str
    hook_start_sec: float
    reason: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["resolution"] = list(self.resolution)
        return d
