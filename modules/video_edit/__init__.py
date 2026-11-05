# -*- coding: utf-8 -*-
"""
modules/video_edit — вертикальные клипы из финального мастера.

  * `build_video(req)`        — один рендер (moviepy+ffmpeg либо fallback);
  * `build_release_edits(...)`— TikTok / Reels / Shorts + manifest;
  * `detect_hook(...)`        — найти самый энергичный участок мастера;
  * `_parse_lrc_with_diagnostics` — LRC-субтитры с честной диагностикой.

Раскладка: `models`, `audio`, `lrc`, `render`, `edits`.
"""

from modules.video_edit.audio import detect_hook  # noqa: F401
from modules.video_edit.edits import build_release_edits  # noqa: F401
from modules.video_edit.lrc import _parse_lrc, _parse_lrc_with_diagnostics  # noqa: F401
from modules.video_edit.models import VideoEditRequest, VideoEditResult  # noqa: F401
from modules.video_edit.render import build_video  # noqa: F401

__all__ = [
    "VideoEditRequest",
    "VideoEditResult",
    "build_release_edits",
    "build_video",
    "detect_hook",
]
