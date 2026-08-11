"""
ZS Music Maker v13 — release_pack_v13.py
========================================

Расширение release_pack_v9 / distribution_export_v11.

v11 закрывает 5 платформ: Spotify/YM/VK/TikTok/YouTube/Shazam.
v9 даёт базовый release pack.

G4 (PROGRESS.md): нет
  · DistroKid XML feed — крупнейший мировой агрегатор;
  · YouTube HTML description (markdown → sanitized HTML,
    3 превью-ссылки, 15 хэштегов);
  · VK Client pre-fill `.txt` для буфера обмена;
  · Shazam Kit JSON-LD для Apple/Songwritter.

Это ВСЁ 4 локальных файла без API-ключей. Платформы их читают
при сабмите вручную.

ВАЖНО: модуль не делает сетевых запросов, не загружает ничего на
платформы авто-up. Только формирует файлы, которые пользователь
сам копирует в форму загрузки.
"""

from __future__ import annotations

import html
import json
import re
import time
from collections import OrderedDict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class TrackMeta:
    """Минимальная мета, нужная дистрибуторам (ISO + Spotify-стандарт)."""

    artist: str = "Unknown Artist"
    title: str = "Untitled Track"
    version: str = ""  # remix/edit/etc
    language: str = "ru"
    isrc: str = ""  # 12 chars (например 'RU-A0B-26-00001')
    upc: str = ""  # 12-13 chars
    iswc: str = ""
    copyright_year: str = "2026"
    copyright_owner: str = ""
    p_line: str = ""  # (P) 2026 Owner
    c_line: str = ""  # (C) 2026 Owner
    genres: list[str] = field(default_factory=list)
    subgenres: list[str] = field(default_factory=list)
    moods: list[str] = field(default_factory=list)
    descripton_short: str = ""
    description_long: str = ""
    lyrics_ru: str = ""
    lyrics_en_hook: str = ""
    bpm: int = 0
    key: str = ""  # e.g. "F#m"
    explicit: bool = False
    release_date: str = ""  # YYYY-MM-DD
    track_length_ms: int = 0
    tags: list[str] = field(default_factory=list)
    cover_path: str = ""  # relative
    wav_path: str = ""
    mp3_path: str = ""
    flac_path: str = ""
    instrumental_path: str = ""
    acapella_path: str = ""
    tiktok_hook_path: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
#  Утилиты
# ---------------------------------------------------------------------------


def _md_to_sanitized_html(md: str) -> str:
    """
    Простейший md → sanitized HTML БЕЗ зависимостей.
    Поддерживает: **bold**, _italic_, [text](url), строки.
    Не исполняет js/iframe.
    """
    if not md:
        return ""
    out: list[str] = []
    for line in md.splitlines():
        safe = html.escape(line, quote=False)
        safe = re.sub(
            r"\[([^\]]+)\]\(([^\)]+)\)",
            lambda m: f'<a href="{html.escape(m.group(2))}">' f"{m.group(1)}</a>",
            safe,
        )
        safe = re.sub(r"\*\*([^\*]+)\*\*", r"<b>\1</b>", safe)
        safe = re.sub(r"_([^_]+)_", r"<i>\1</i>", safe)
        out.append(safe)
    return "\n".join(out)


def _hashtags(tags: list[str], mood_count: int = 15) -> list[str]:
    base = [
        "#phonk",
        "#drift",
        "#car",
        "#turkey",
        "#summer",
        "#hit",
        "#club",
        "#tiktok",
        "#russia",
        "#neon",
        "#vibe",
        "#bass",
        "#beat",
        "#night",
        "#edit",
    ]
    for t in tags:
        if t and not t.startswith("#"):
            base.append("#" + re.sub(r"\s+", "", t))
        elif t:
            base.append(t)
    seen = OrderedDict()
    for x in base:
        seen[x] = True
    return list(seen.keys())[: max(8, mood_count)]


# ---------------------------------------------------------------------------
#  DistroKid XML feed
# ---------------------------------------------------------------------------

DISTROKID_XML_HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<track xmlns="http://distrokid.com/xml/track/v1">
"""

DISTROKID_XML_FOOTER = "</track>\n"


def _xml_field(name: str, text: str, indent: str = "    ") -> str:
    safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"{indent}<{name}>{safe}</{name}>\n"


def build_distrokid_xml(meta: TrackMeta) -> str:
    """DistroKid принимает XML-submission с полями ниже."""
    xml = DISTROKID_XML_HEADER
    xml += _xml_field("artist", meta.artist)
    xml += _xml_field(
        "title", meta.title + (f" ({meta.version})" if meta.version else "")
    )
    xml += _xml_field("language", meta.language)
    xml += _xml_field("primaryGenre", meta.genres[0] if meta.genres else "Hip-Hop/Rap")
    if len(meta.genres) > 1:
        xml += _xml_field("secondaryGenre", meta.genres[1])
    if meta.isrc:
        xml += _xml_field("isrc", meta.isrc)
    if meta.upc:
        xml += _xml_field("upc", meta.upc)
    if meta.copyright_year or meta.copyright_owner:
        xml += _xml_field(
            "copyright",
            f"{meta.c_line} {meta.copyright_year} " f"{meta.copyright_owner}",
        )
    if meta.p_line:
        xml += _xml_field("pLine", meta.p_line)
    xml += _xml_field("explicit", "yes" if meta.explicit else "no")
    if meta.release_date:
        xml += _xml_field("releaseDate", meta.release_date)
    if meta.bpm:
        xml += _xml_field("bpm", str(meta.bpm))
    tags_str = ", ".join(meta.tags[:8])
    xml += _xml_field("tags", tags_str)
    xml += _xml_field("coverPath", meta.cover_path)
    xml += _xml_field("wavPath", meta.wav_path)
    xml += _xml_field("mp3Path", meta.mp3_path)
    xml += DISTROKID_XML_FOOTER
    return xml


# ---------------------------------------------------------------------------
#  YouTube HTML description
# ---------------------------------------------------------------------------


def build_youtube_description(meta: TrackMeta) -> str:
    md = []
    md.append(
        f"**{meta.artist} — {meta.title}"
        + (f" ({meta.version})" if meta.version else "")
        + "**"
    )
    md.append("")
    if meta.descripton_short:
        md.append(meta.descripton_short)
        md.append("")
    if meta.description_long:
        md.append(meta.description_long)
        md.append("")
    md.append("🎧 Streaming links: TODO")
    if meta.tiktok_hook_path:
        md.append(f"📱 TikTok preview: {meta.tiktok_hook_path}")
    if meta.instrumental_path:
        md.append(f"🎹 Instrumental: {meta.instrumental_path}")
    if meta.acapella_path:
        md.append(f"🎙 Acapella: {meta.acapella_path}")
    md.append("")
    md.append("**Tags:**")
    md.append(" ".join(_hashtags(meta.tags)))
    md.append("")
    md.append(f"© {meta.copyright_year} {meta.copyright_owner}")
    md.append(f"℗ {meta.p_line or meta.copyright_year}")
    return _md_to_sanitized_html("\n".join(md))


# ---------------------------------------------------------------------------
#  VK Client pre-fill (txt для copy-paste в форму VK Music)
# ---------------------------------------------------------------------------


def build_vk_client_prefill(meta: TrackMeta) -> str:
    lines: list[str] = []
    lines.append(f"Исполнитель: {meta.artist}")
    lines.append(
        f"Название: {meta.title}" + (f" ({meta.version})" if meta.version else "")
    )
    lines.append(f"Жанр: {', '.join(meta.genres) or 'Hip-Hop/Rap'}")
    if meta.bpm:
        lines.append(f"BPM: {meta.bpm}")
    if meta.key:
        lines.append(f"Тональность: {meta.key}")
    if meta.release_date:
        lines.append(f"Дата релиза: {meta.release_date}")
    lines.append("")
    lines.append("Краткое описание:")
    lines.append(meta.descripton_short or "(краткое описание трека)")
    lines.append("")
    lines.append("Полное описание:")
    lines.append(meta.description_long or "(что в треке — вайб, тема)")
    lines.append("")
    if meta.lyrics_ru:
        lines.append("Текст (RU):")
        lines.append(meta.lyrics_ru)
        lines.append("")
    if meta.lyrics_en_hook:
        lines.append("Хук (EN):")
        lines.append(meta.lyrics_en_hook)
        lines.append("")
    lines.append("Теги: " + ", ".join(meta.tags))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
#  Shazam Kit JSON-LD
# ---------------------------------------------------------------------------


def build_shazam_jsonld(meta: TrackMeta) -> str:
    """Формат Apple Shazam Kit Music Catalog Feed."""
    payload = {
        "musicId": meta.isrc or f"QQ-{int(time.time())}",
        "title": meta.title,
        "artist": meta.artist,
        "album": "",  # Single-track release
        "composer": meta.copyright_owner or meta.artist,
        "year": meta.copyright_year,
        "genre": (meta.genres + meta.subgenres)[:3],
        "isrc": meta.isrc,
        "upc": meta.upc,
        "duration_ms": meta.track_length_ms,
        "explicit": meta.explicit,
        "lyrics": meta.lyrics_ru
        + ("\n---\n" + meta.lyrics_en_hook if meta.lyrics_en_hook else ""),
        "copyright": f"© {meta.copyright_year} {meta.copyright_owner}",
        "phonographic": f"℗ {meta.copyright_year} " f"{meta.copyright_owner}",
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
#  Все 4 файла разом
# ---------------------------------------------------------------------------


def build_all(meta: TrackMeta, out_dir: Path) -> dict[str, str]:
    """
    Генерирует все 4 файла в указанную папку.
    Возвращает dict {имя_файла: путь}.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    files: dict[str, str] = {}

    dk = build_distrokid_xml(meta)
    p1 = out_dir / "distrokid_feed.xml"
    p1.write_text(dk, encoding="utf-8")
    files["distrokid_feed.xml"] = str(p1)

    yt = build_youtube_description(meta)
    p2 = out_dir / "youtube_description.html"
    p2.write_text(yt, encoding="utf-8")
    files["youtube_description.html"] = str(p2)

    vk = build_vk_client_prefill(meta)
    p3 = out_dir / "vk_client_prefill.txt"
    p3.write_text(vk, encoding="utf-8")
    files["vk_client_prefill.txt"] = str(p3)

    sh = build_shazam_jsonld(meta)
    p4 = out_dir / "shazam_kit_feed.jsonld.json"
    p4.write_text(sh, encoding="utf-8")
    files["shazam_kit_feed.jsonld.json"] = str(p4)

    return files


def demo_meta() -> TrackMeta:
    return TrackMeta(
        artist="Smoke Artist",
        title="Summer Drift",
        version="Radio Edit",
        language="ru",
        isrc="RU-A0B-26-12345",
        upc="899876543210",
        copyright_year="2026",
        copyright_owner="Sound Bureau",
        p_line="(P) 2026 Sound Bureau",
        c_line="(C) 2026 Sound Bureau",
        genres=["Hip-Hop/Rap", "Phonk"],
        subgenres=["Drift Phonk"],
        moods=["energetic", "driving", "summer"],
        descripton_short="Phonk-трек про лето, тачки и ночной драйв.",
        description_long="Жёсткий 808-й бас, женский бэк-вокал, "
        "рюкзак-мотив хука 'summer drift'. "
        "Длина 2:30, BPM 138, тональность F#m.",
        lyrics_ru="[Куплет]\nВ ночь уходим мы в драйв\n"
        "Фары режут темноту\n[Припев]\nSummer Drift!",
        lyrics_en_hook="[Hook]\nSummer Drift!",
        bpm=138,
        key="F#m",
        explicit=False,
        release_date="2026-08-15",
        track_length_ms=150000,
        tags=["summer", "drift", "phonk", "car", "turkey", "russia", "edit", "club"],
        cover_path="cover.png",
        wav_path="track.wav",
        mp3_path="track.mp3",
        instrumental_path="track_instrumental.wav",
        acapella_path="track_acapella.wav",
        tiktok_hook_path="tiktok_30s.wav",
    )


def main_entry() -> int:
    meta = demo_meta()
    out_dir = ROOT / "output" / "releases" / "v13_demo" / "distro_packs"
    files = build_all(meta, out_dir)
    print(f"distro_pack_v13 wrote {len(files)} files in {out_dir}:")
    for n, p in files.items():
        sz = Path(p).stat().st_size
        print(f"  · {n}  ({sz}B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main_entry())
