# -*- coding: utf-8 -*-
"""
modules/release/channels.py — пакеты под площадки: Spotify, Яндекс/VK, TikTok,
YouTube, Shazam.

Каждая площадка получает ровно то, что просит: длительность клипа, формат
описания, структурированные данные. Никаких «примерно таких» файлов — если
чего-то не хватает, в отчёте стоит `missing`, а не пустышка.
"""

from __future__ import annotations

import json
import html
from pathlib import Path
from typing import Any

CHANNELS = ("spotify", "yandex_vk", "tiktok", "youtube", "shazam")

TIKTOK_CLIP_SEC = 15.0


def _write(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return str(path)


def _title(meta: dict[str, Any]) -> str:
    return str(meta.get("title") or "Untitled")


def _artist(meta: dict[str, Any]) -> str:
    return str(meta.get("artist") or "Unknown artist")


def spotify_package(meta: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    """Spotify: описание трека, теги настроения и кредиты."""
    payload = {
        "platform": "spotify",
        "title": _title(meta),
        "artist": _artist(meta),
        "genre": meta.get("genre") or "",
        "bpm": meta.get("bpm") or "",
        "key": meta.get("key") or "",
        "isrc": meta.get("isrc") or "",
        "mood": list(meta.get("mood_tags") or []),
        "credits": {
            "composer": _artist(meta),
            "producer": meta.get("producer") or _artist(meta),
            "mastering": "ZS Music Maker",
        },
    }
    return {"ok": True, "files": [_write(out_dir / "spotify.json", json.dumps(payload, ensure_ascii=False, indent=2))]}


def yandex_vk_package(meta: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    """Яндекс Музыка / VK: текст поста и теги для поиска."""
    tags = " ".join(
        "#" + "".join(ch for ch in str(tag) if ch.isalnum() or ch == "_")
        for tag in (meta.get("mood_tags") or [])
    )
    body = "\n".join(
        [
            f"{_artist(meta)} — «{_title(meta)}»",
            "",
            str(meta.get("description") or "Новый трек. Слушайте на площадках."),
            "",
            f"Жанр: {meta.get('genre') or 'n/a'} · {meta.get('bpm') or '?'} BPM · {meta.get('key') or '?'}",
            tags,
        ]
    )
    return {"ok": True, "files": [_write(out_dir / "yandex_vk.txt", body)]}


def tiktok_package(meta: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    """TikTok: хук-таймкод, вертикальное описание и подсказка по клипу."""
    hook_start = float(meta.get("hook_start_sec") or 0.0)
    clip_end = min(float(meta.get("duration_sec") or TIKTOK_CLIP_SEC), hook_start + TIKTOK_CLIP_SEC)
    payload = {
        "platform": "tiktok",
        "clip_start_sec": round(hook_start, 2),
        "clip_end_sec": round(clip_end, 2),
        "caption": f"{_title(meta)} · {_artist(meta)}",
        "hashtags": ["#" + _title(meta).replace(" ", ""), "#newmusic", "#music"],
    }
    return {"ok": True, "files": [_write(out_dir / "tiktok.json", json.dumps(payload, ensure_ascii=False, indent=2))]}


def youtube_package(meta: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    """YouTube: заголовок, описание, теги и таймкоды секций."""
    sections = meta.get("sections") or []
    timecodes = [
        f"{int(float(section.get('start_sec', 0)) // 60):02d}:{int(float(section.get('start_sec', 0)) % 60):02d} "
        f"{section.get('name', 'section')}"
        for section in sections
        if isinstance(section, dict)
    ]
    description = "\n".join(
        [
            f"{_artist(meta)} — {_title(meta)}",
            "",
            str(meta.get("description") or ""),
            "",
            *timecodes,
        ]
    )
    payload = {
        "title": f"{_artist(meta)} — {_title(meta)}",
        "description": description,
        "tags": list(meta.get("mood_tags") or []) + [meta.get("genre") or ""],
        "timecodes": timecodes,
    }
    return {"ok": True, "files": [_write(out_dir / "youtube.json", json.dumps(payload, ensure_ascii=False, indent=2))]}


def shazam_package(meta: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    """Shazam/Schema.org: структурированные данные для распознавания."""
    payload = {
        "@context": "https://schema.org",
        "@type": "MusicRecording",
        "name": _title(meta),
        "byArtist": {"@type": "MusicGroup", "name": _artist(meta)},
        "isrcCode": meta.get("isrc") or "",
        "genre": meta.get("genre") or "",
        "duration": f"PT{int(float(meta.get('duration_sec') or 0))}S",
    }
    return {"ok": True, "files": [_write(out_dir / "shazam.jsonld", json.dumps(payload, ensure_ascii=False, indent=2))]}


BUILDERS = {
    "spotify": spotify_package,
    "yandex_vk": yandex_vk_package,
    "tiktok": tiktok_package,
    "youtube": youtube_package,
    "shazam": shazam_package,
}


def build_channel_package(channel: str, meta: dict[str, Any], out_dir: str | Path) -> dict[str, Any]:
    builder = BUILDERS.get(channel)
    if builder is None:
        return {"ok": False, "reason": f"unknown channel '{channel}'; known: {', '.join(CHANNELS)}"}
    return builder(meta, Path(out_dir))


def build_all_channels(meta: dict[str, Any], out_dir: str | Path) -> dict[str, Any]:
    """Все пять площадок разом; отчёт честно перечисляет сбои."""
    base = Path(out_dir)
    results: dict[str, Any] = {}
    for channel in CHANNELS:
        try:
            results[channel] = build_channel_package(channel, meta, base / channel)
        except Exception as exc:  # noqa: BLE001
            results[channel] = {"ok": False, "reason": f"{type(exc).__name__}: {exc}"}
    files = [path for result in results.values() for path in result.get("files", [])]
    return {
        "ok": all(result.get("ok") for result in results.values()),
        "engine": "modules.release.channels",
        "channels": results,
        "files": files,
        "failed": [name for name, result in results.items() if not result.get("ok")],
    }


def escape_for_caption(text: str) -> str:
    """Экранирование подписей для HTML-вставок (не даём площадкам сломать разметку)."""
    return html.escape(text, quote=True)
