# -*- coding: utf-8 -*-
"""
modules/video_edit/edits.py — набор релизных нарезок (TikTok/Reels/Shorts)
и встроенный self-test.
"""

from __future__ import annotations

import json
import os

from modules.video_edit.audio import _rms_windows
from modules.video_edit.lrc import _parse_lrc
from modules.video_edit.models import VideoEditRequest
from modules.video_edit.render import build_video


def build_release_edits(
    master_wav, cover_png, lyrics_lrc, bpm, title, artist, out_dir
) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    manifest = {}
    for name, orient, dur in [
        ("tiktok_edit.mp4", "vertical", 20),
        ("reels_edit.mp4", "vertical", 30),
        ("shorts_edit.mp4", "vertical", 20),
    ]:
        req = VideoEditRequest(
            master_wav=master_wav,
            cover_png=cover_png,
            lyrics_lrc=lyrics_lrc,
            bpm=bpm,
            duration_sec=dur,
            orientation=orient,
            output_path=os.path.join(out_dir, name),
            title=title,
            artist=artist,
        )
        manifest[name] = build_video(req).to_dict()
    with open(
        os.path.join(out_dir, "video_edits_manifest.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    return manifest


def _self_test() -> bool:
    """Run the parser check with an OS-portable, automatically removed fixture."""
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory(prefix="zsmm_v11_lrc_") as directory:
        tmp = Path(directory) / "lrc_test.lrc"
        tmp.write_text("[00:01.00]hello\n[00:02.50]world\n[bad]skip\n", encoding="utf-8")
        parsed = _parse_lrc(str(tmp))
    ok = len(parsed) == 2 and parsed[0][1] == "hello"
    rms = _rms_windows([0.0] * 44100 + [0.5] * 44100, 44100, 1.0)
    ok &= len(rms) == 2 and rms[1] > rms[0]
    return ok


if __name__ == "__main__":
    print("video_edit self-test:", "OK" if _self_test() else "FAIL")
