"""
v6 Release Pack — надстройка над v5 release_export.
Добавляет:
  - LRC (тексты с таймингами)
  - cover.png (Pillow, offline)
  - TikTok / Reels MP4 (ffmpeg)
  - Мастер под стенды: car / club / streaming
  - manifest.json (лицензии + AI-QA)
Совместимо с v5: если чего-то нет — просто пропускает и логирует.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


def build_v6_release(
    project_dir: str,
    master_wav: str,
    lyrics_text: str,
    bpm: float,
    recipe: dict,
    provenance: list | None = None,
    ai_qa: dict | None = None,
) -> dict:
    project_dir = Path(project_dir)
    pkg = project_dir / "release_package_v6"
    pkg.mkdir(parents=True, exist_ok=True)
    out: dict = {"dir": str(pkg), "files": {}}

    # 1) исходный мастер
    try:
        shutil.copy2(master_wav, pkg / "master_24bit.wav")
        out["files"]["master_wav"] = str(pkg / "master_24bit.wav")
    except Exception as e:
        out["master_error"] = str(e)

    # 2) MP3 320 + FLAC через ffmpeg (если есть)
    ff = _ffmpeg()
    if ff and (pkg / "master_24bit.wav").exists():
        for fmt, args in [
            ("mp3", ["-b:a", "320k"]),
            ("flac", []),
        ]:
            outp = pkg / f"master.{fmt}"
            try:
                subprocess.run(
                    [ff, "-y", "-i", str(pkg / "master_24bit.wav"), *args, str(outp)],
                    capture_output=True,
                    timeout=180,
                )
                if outp.exists():
                    out["files"][fmt] = str(outp)
            except Exception as e:
                out[f"{fmt}_error"] = str(e)

    # 3) LRC
    try:
        from app.core.lrc_export import make_lrc

        lrc = pkg / "lyrics.lrc"
        make_lrc(lyrics_text or "", float(bpm or 140), str(lrc))
        out["files"]["lrc"] = str(lrc)
    except Exception as e:
        out["lrc_error"] = str(e)

    # 4) Обложка + TikTok / Reels
    try:
        from app.core.cover_gen import make_cover

        cover = pkg / "cover.png"
        make_cover(recipe, str(cover))
        out["files"]["cover"] = str(cover)
        if recipe.get("make_video", True):
            from app.core.video_edit import make_reels, make_tiktok

            r_tt = make_tiktok(
                (
                    str(pkg / "master.mp3")
                    if (pkg / "master.mp3").exists()
                    else str(pkg / "master_24bit.wav")
                ),
                str(cover),
                str(pkg / "tiktok.mp4"),
            )
            r_rl = make_reels(
                (
                    str(pkg / "master.mp3")
                    if (pkg / "master.mp3").exists()
                    else str(pkg / "master_24bit.wav")
                ),
                str(cover),
                str(pkg / "reels.mp4"),
            )
            out["files"]["tiktok"] = r_tt.get("path")
            out["files"]["reels"] = r_rl.get("path")
    except Exception as e:
        out["video_error"] = str(e)

    # 5) Стенды прослушивания
    try:
        from app.core.mastering_stands import render_stands

        stands_dir = pkg / "stands"
        r = render_stands(str(pkg / "master_24bit.wav"), str(stands_dir))
        if r.get("ok"):
            out["files"]["stands"] = r["stands"]
    except Exception as e:
        out["stands_error"] = str(e)

    # 6) recipe.json + manifest.json
    (pkg / "recipe.json").write_text(
        json.dumps(recipe, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    manifest = {
        "version": "v6",
        "samples_provenance": provenance or [],
        "ai_qa": ai_qa or {},
        "license_policy": "CC0 / Royalty-Free / CC-BY only by default",
    }
    (pkg / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 7) тексты
    (pkg / "lyrics.txt").write_text(lyrics_text or "", encoding="utf-8")
    return out


def _ffmpeg() -> str | None:
    for c in ["tools/ffmpeg/bin/ffmpeg.exe", "tools/ffmpeg.exe", "ffmpeg"]:
        if Path(c).exists():
            return c
        if shutil.which(c):
            return c
    return None
