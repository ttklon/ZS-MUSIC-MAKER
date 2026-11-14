# -*- coding: utf-8 -*-
"""
app/core/stages/release.py — Релиз: полный пакет и честный минимальный фоллбек.
"""

from __future__ import annotations

import logging

import json

from pathlib import Path
from typing import Any


def _stage_release_pack(
    master_wav: str,
    meta: dict[str, Any],
    out_dir: Path,
    masters_map=None,
    stems_map=None,
    lyrics_text: str = "",
    stages=None,
    hit_metrics=None,
) -> dict[str, Any]:
    """Полный релиз-пакет; при отказе движка — честный минимальный пакет."""
    out = out_dir / "release"
    fallback_attempts: list[dict[str, str]] = []
    try:
        from modules.release import build_pack

        result = build_pack(
            master_wav,
            str(out),
            meta,
            masters_map=masters_map,
            stems_map=stems_map,
            lyrics_text=lyrics_text,
            stages=stages,
            hit_metrics=hit_metrics,
        )
        if isinstance(result, dict):
            return result
        fallback_attempts.append({
            "engine": "modules.release",
            "status": "invalid_result",
            "error": f"expected dict, got {type(result).__name__}",
        })
    except Exception as exc:  # noqa: BLE001 - отчёт о сбое важен для диагностики
        fallback_attempts.append({
            "engine": "modules.release",
            "status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
        })
    result = _minimal_release_pack(master_wav, meta, out)
    if fallback_attempts:
        result = dict(result)
        result["fallback_attempts"] = fallback_attempts
    return result


def _minimal_release_pack(
    master_wav: str, meta: dict[str, Any], out: Path
) -> dict[str, Any]:
    try:
        import shutil

        out.mkdir(parents=True, exist_ok=True)
        files: list[str] = []
        dst_wav = out / "full_master_streaming.wav"
        shutil.copy(master_wav, dst_wav)
        files.append(str(dst_wav))
        try:
            from pydub import AudioSegment

            seg = AudioSegment.from_file(master_wav)
            mp3 = out / "full_master.mp3"
            seg.export(mp3, format="mp3", bitrate="320k")
            files.append(str(mp3))
        except Exception:
            logging.getLogger(__name__).debug("ignored exception", exc_info=True)
        try:
            from PIL import Image, ImageDraw

            img = Image.new("RGB", (1400, 1400), (20, 20, 40))
            d = ImageDraw.Draw(img)
            d.text((60, 60), meta.get("title", "ZS Track"), fill=(255, 170, 60))
            cov = out / "cover.png"
            img.save(cov)
            files.append(str(cov))
        except Exception:
            logging.getLogger(__name__).debug("ignored exception", exc_info=True)
        (out / "lyrics.txt").write_text(meta.get("lyrics_text", ""), encoding="utf-8")
        (out / "metadata.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (out / "licenses.txt").write_text(
            "ZS Music Maker minimal pack.\n"
            "Licenses and rights have not been verified automatically. "
            "Check all samples, models, reference material and voice permissions before release.\n",
            encoding="utf-8",
        )
        (out / "hit_report.md").write_text(
            f"# Hit Report\n\nScore: {meta.get('hit_score','n/a')}\n"
            f"Verdict: {meta.get('verdict','n/a')}\n",
            encoding="utf-8",
        )
        return {
            "ok": True,
            "n_files": len(files) + 4,
            "files": files,
            "path": str(out),
            "fallback_used": True,
            "reason": "modules.release unavailable; minimal pack",
        }
    except Exception as e:
        return {"ok": False, "reason": str(e)}
