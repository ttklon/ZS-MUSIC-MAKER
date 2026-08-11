"""
v6 Video Edit — вертикальные MP4 для TikTok / Reels.
Требует ffmpeg (кладётся в tools/ffmpeg/ автосборкой).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

FFMPEG_CANDIDATES = ["tools/ffmpeg/bin/ffmpeg.exe", "tools/ffmpeg.exe", "ffmpeg"]


def _find_ffmpeg() -> str:
    for c in FFMPEG_CANDIDATES:
        p = Path(c)
        if p.exists():
            return str(p)
        if shutil.which(c):
            return c
    return "ffmpeg"


def make_vertical_edit(
    audio_path: str,
    cover_path: str,
    out_mp4: str,
    seconds: int = 25,
    size: str = "1080x1920",
) -> dict:
    ff = _find_ffmpeg()
    Path(out_mp4).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ff,
        "-y",
        "-loop",
        "1",
        "-i",
        cover_path,
        "-i",
        audio_path,
        "-t",
        str(seconds),
        "-vf",
        f"scale={size}:force_original_aspect_ratio=increase,crop={size}",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-tune",
        "stillimage",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-pix_fmt",
        "yuv420p",
        "-shortest",
        out_mp4,
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=180)
        return {
            "ok": r.returncode == 0,
            "path": out_mp4,
            "stderr": r.stderr.decode("utf-8", "replace")[-400:],
        }
    except Exception as e:
        return {"ok": False, "reason": str(e), "path": None}


def make_tiktok(audio, cover, out):
    return make_vertical_edit(audio, cover, out, 25)


def make_reels(audio, cover, out):
    return make_vertical_edit(audio, cover, out, 30)
