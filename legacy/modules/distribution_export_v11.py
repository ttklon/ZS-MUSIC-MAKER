# -*- coding: utf-8 -*-
"""
ZS Music Maker v11 — distribution_export_v11.py

Реализует ТЗ 20.2 п.33 «Куда выкладывать: ВЕЗДЕ».
5 пакетов: Spotify/DSP, Яндекс+VK, TikTok, YouTube, Shazam.
Никаких autoupload — только файлы + инструкции.
"""

from __future__ import annotations

import csv
import json
import os
import shutil
import sys
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


def _safe_print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        sys.stdout.buffer.write((msg + "\n").encode("cp866", errors="replace"))


@dataclass
class TrackMetadata:
    title: str
    artist: str
    album: str = ""
    genre: str = "Hip-Hop/Rap"
    subgenre: str = "Phonk / Trap / Hyperpop"
    bpm: float = 140.0
    key: str = ""
    language: str = "ru"
    explicit: bool = False
    isrc: str = ""
    iswc: str = ""
    upc: str = ""
    release_date: str = ""
    label: str = "Self-Released"
    copyright: str = ""
    p_line: str = ""
    duration_sec: float = 0.0
    tags: List[str] = field(default_factory=list)
    lyrics_ru: str = ""
    lyrics_en_hook: str = ""

    def ensure(self):
        if not self.release_date:
            self.release_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        year = self.release_date[:4]
        if not self.copyright:
            self.copyright = f"© {year} {self.artist}"
        if not self.p_line:
            self.p_line = f"℗ {year} {self.artist}"
        if not self.album:
            self.album = self.title


@dataclass
class ReleaseFiles:
    master_wav: str = ""
    mp3_320: str = ""
    flac: str = ""
    instrumental_wav: str = ""
    acapella_wav: str = ""
    stems_dir: str = ""
    tiktok_mp4: str = ""
    reels_mp4: str = ""
    shorts_mp4: str = ""
    cover_png: str = ""
    lyrics_txt: str = ""
    lyrics_lrc: str = ""

    def existing(self) -> Dict[str, str]:
        return {k: v for k, v in asdict(self).items()
                if v and os.path.exists(v)}


def _copy_safe(src, dst) -> bool:
    try:
        if not src or not os.path.exists(src):
            return False
        os.makedirs(os.path.dirname(os.path.abspath(dst)) or ".", exist_ok=True)
        shutil.copy2(src, dst)
        return True
    except Exception as e:
        _safe_print(f"[dist_v11] copy fail: {e}")
        return False


def build_spotify_package(meta, files, out_dir):
    d = os.path.join(out_dir, "spotify_dsp")
    os.makedirs(d, exist_ok=True)
    copied = {}
    if _copy_safe(files.master_wav, os.path.join(d, "audio_master.wav")):
        copied["audio"] = "audio_master.wav"
    elif _copy_safe(files.mp3_320, os.path.join(d, "audio_master.mp3")):
        copied["audio"] = "audio_master.mp3"
    if _copy_safe(files.cover_png, os.path.join(d, "cover.png")):
        copied["cover"] = "cover.png"
    csv_path = os.path.join(d, "distrokid_manifest.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Field", "Value"])
        for row in [["Artist", meta.artist], ["Track title", meta.title],
                    ["Album", meta.album], ["Genre", meta.genre],
                    ["Sub-genre", meta.subgenre],
                    ["Language of vocals", meta.language],
                    ["Explicit", "Yes" if meta.explicit else "No"],
                    ["Release date", meta.release_date],
                    ["Label", meta.label], ["Copyright", meta.copyright],
                    ["Producer (P)", meta.p_line],
                    ["BPM", f"{meta.bpm:.1f}"], ["Key", meta.key],
                    ["Duration (sec)", f"{meta.duration_sec:.1f}"],
                    ["ISRC", meta.isrc or "(auto)"],
                    ["ISWC", meta.iswc or "(auto)"],
                    ["UPC", meta.upc or "(auto)"],
                    ["Tags", ", ".join(meta.tags)]]:
            w.writerow(row)
    json_path = os.path.join(d, "metadata.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"meta": asdict(meta), "files": copied},
                  f, ensure_ascii=False, indent=2)
    inst = os.path.join(d, "INSTRUCTIONS_SPOTIFY.md")
    with open(inst, "w", encoding="utf-8") as f:
        f.write(f"""# Spotify / Apple Music / Amazon Music

## Файлы
- `audio_master.wav` / `.mp3`, `cover.png` (≥1400×1400)
- `distrokid_manifest.csv`, `metadata.json`

## Дистрибьюторы
1. **DistroKid** ($19.99/год)
2. **TuneCore** ($9.99/сингл)
3. **Amuse Music** (бесплатно, ограничения)
4. **RouteNote** (бесплатно, 15% с продаж)

## RouteNote workflow (free path)
1. routenote.com → New Release → Single
2. Загрузи `audio_master.wav` + `cover.png`
3. Скопируй поля из CSV
4. Submit → 3-7 дней до Spotify/Apple/Amazon/Deezer/Tidal

Copyright: **{meta.copyright}**  •  {meta.title} — {meta.artist}
""")
    return {"dir": d, "csv": csv_path, "json": json_path, "instructions": inst}


def build_yandex_vk_package(meta, files, out_dir):
    d = os.path.join(out_dir, "yandex_vk_ru")
    os.makedirs(d, exist_ok=True)
    if not _copy_safe(files.mp3_320, os.path.join(d, "track.mp3")):
        _copy_safe(files.master_wav, os.path.join(d, "track.wav"))
    _copy_safe(files.cover_png, os.path.join(d, "cover.png"))
    if files.lyrics_txt:
        _copy_safe(files.lyrics_txt, os.path.join(d, "lyrics.txt"))
    csv_path = os.path.join(d, "release_ru.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Артист", "Название", "Альбом", "Жанр", "Язык",
                    "BPM", "Тональность", "Длительность", "Дата релиза",
                    "Лейбл", "Копирайт", "18+"])
        w.writerow([meta.artist, meta.title, meta.album, meta.genre,
                    "русский" if meta.language == "ru" else meta.language,
                    f"{meta.bpm:.1f}", meta.key,
                    f"{int(meta.duration_sec // 60):02d}:{int(meta.duration_sec % 60):02d}",
                    meta.release_date, meta.label, meta.copyright,
                    "да" if meta.explicit else "нет"])
    inst = os.path.join(d, "INSTRUCTIONS_YANDEX_VK.md")
    with open(inst, "w", encoding="utf-8") as f:
        f.write(f"""# Яндекс.Музыка + VK Music

## Файлы: track.mp3, cover.png, lyrics.txt, release_ru.csv

## Бесплатные пути
1. **Belieber** (belieber.io) — free tier, Яндекс+VK
2. **VK Music Loud** (loud.vk.com) — прямая заливка на VK Music
3. **Bandlink Distribution** (платно, +Ok.ru)

## VK Loud
1. loud.vk.com → «Загрузить релиз»
2. mp3 + cover.png + поля из CSV
3. 24-72ч → VK, Ok.ru, Boom

Артист: **{meta.artist}**  •  {meta.title}
""")
    return {"dir": d, "csv": csv_path, "instructions": inst}


def build_tiktok_package(meta, files, out_dir):
    d = os.path.join(out_dir, "tiktok")
    os.makedirs(d, exist_ok=True)
    if not _copy_safe(files.tiktok_mp4, os.path.join(d, "tiktok_edit.mp4")):
        _safe_print("[dist_v11] tiktok mp4 not found — copying fallback assets")
        _copy_safe(files.cover_png, os.path.join(d, "cover.png"))
    _copy_safe(files.cover_png, os.path.join(d, "thumbnail.png"))
    base_tags = ["#рэп", "#phonk", "#трек", "#новинка", "#music",
                 "#hiphop", "#russianrap", "#авто", "#едем", "#вайб"]
    user_tags = [t if t.startswith("#") else f"#{t}" for t in meta.tags[:6]]
    all_tags = user_tags + base_tags
    seen, hashtags = set(), []
    for t in all_tags:
        if t.lower() not in seen:
            seen.add(t.lower())
            hashtags.append(t)
    caption_path = os.path.join(d, "caption.txt")
    with open(caption_path, "w", encoding="utf-8") as f:
        f.write(f"{meta.title} — {meta.artist}\n\n")
        if meta.lyrics_en_hook:
            f.write(f"{meta.lyrics_en_hook.strip()[:100]}\n\n")
        f.write(" ".join(hashtags[:20]))
    json_path = os.path.join(d, "tiktok_studio.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "title": f"{meta.title} — {meta.artist}",
            "description": open(caption_path, encoding="utf-8").read(),
            "hashtags": hashtags[:20],
            "sound_title": meta.title, "sound_artist": meta.artist,
            "allow_duet": True, "allow_stitch": True, "privacy": "public",
        }, f, ensure_ascii=False, indent=2)
    inst = os.path.join(d, "INSTRUCTIONS_TIKTOK.md")
    with open(inst, "w", encoding="utf-8") as f:
        f.write(f"""# TikTok — Инструкция

## Файлы
- `tiktok_edit.mp4` (1080×1920, 15-30 сек)
- `thumbnail.png`, `caption.txt`, `tiktok_studio.json`

## Workflow
1. TikTok app / studio.tiktok.com → Upload
2. Загрузи tiktok_edit.mp4
3. Скопируй caption.txt в описание
4. **ВАЖНО**: после публикации → «Сохранить как звук» → «Доступ всем»
5. Duet + Stitch = включены

## Хэштеги (топ-{min(len(hashtags), 20)})
{" ".join(hashtags[:20])}

## Прокачка
- Постить 19:00-22:00 МСК
- Первые 3 часа — комментить с других акков
- Через 2-3 дня — снять эдит на свой же трек
""")
    return {"dir": d, "caption": caption_path, "json": json_path,
            "instructions": inst}


def build_youtube_package(meta, files, out_dir):
    d = os.path.join(out_dir, "youtube")
    os.makedirs(d, exist_ok=True)
    _copy_safe(files.shorts_mp4 or files.tiktok_mp4,
               os.path.join(d, "shorts.mp4"))
    _copy_safe(files.master_wav, os.path.join(d, "audio_master.wav"))
    _copy_safe(files.cover_png, os.path.join(d, "thumbnail.png"))
    if files.lyrics_txt:
        _copy_safe(files.lyrics_txt, os.path.join(d, "lyrics.txt"))
    desc_path = os.path.join(d, "description.txt")
    with open(desc_path, "w", encoding="utf-8") as f:
        f.write(f"""{meta.title} — {meta.artist}

🎧 Слушать:
Spotify: [ссылка]
Яндекс.Музыка: [ссылка]
VK Music: [ссылка]
Apple Music: [ссылка]

📝 Текст:
{meta.lyrics_ru[:500] if meta.lyrics_ru else '[скоро]'}

🎵 BPM: {meta.bpm:.0f}  •  Key: {meta.key or '—'}
📅 Релиз: {meta.release_date}

{meta.copyright}
{meta.p_line}

#{meta.genre.replace('/', '').replace(' ', '')} #{meta.artist.replace(' ', '')}
""")
    ytj = os.path.join(d, "youtube_studio.json")
    with open(ytj, "w", encoding="utf-8") as f:
        json.dump({
            "snippet": {
                "title": f"{meta.title} — {meta.artist} (Official Audio)",
                "description": open(desc_path, encoding="utf-8").read(),
                "tags": meta.tags[:20] + ["russian rap", "phonk",
                                          meta.artist, meta.title],
                "categoryId": "10", "defaultLanguage": meta.language,
            },
            "status": {"privacyStatus": "public",
                       "selfDeclaredMadeForKids": False, "license": "youtube"},
        }, f, ensure_ascii=False, indent=2)
    inst = os.path.join(d, "INSTRUCTIONS_YOUTUBE.md")
    with open(inst, "w", encoding="utf-8") as f:
        f.write(f"""# YouTube — Инструкция

## Файлы
- `shorts.mp4` (для Shorts, вертикально)
- `audio_master.wav` (для официального аудио)
- `thumbnail.png`, `description.txt`, `youtube_studio.json`

## Два ролика
1. YouTube Shorts (shorts.mp4, до 60 сек, title заканчивается на #Shorts)
2. Официальное аудио — собери через ffmpeg:
   ```
   ffmpeg -loop 1 -i thumbnail.png -i audio_master.wav -c:v libx264 \\
     -c:a aac -shortest -pix_fmt yuv420p -vf scale=1280:720 official_audio.mp4
   ```

Copyright: {meta.copyright}
""")
    return {"dir": d, "instructions": inst, "json": ytj}


def build_shazam_package(meta, out_dir):
    d = os.path.join(out_dir, "shazam_ready")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "shazam_metadata.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"title": meta.title, "artist": meta.artist,
                   "album": meta.album, "release_date": meta.release_date,
                   "isrc": meta.isrc, "iswc": meta.iswc,
                   "note": "Shazam автоматически распознает трек после "
                           "релиза на любом DSP."},
                  f, ensure_ascii=False, indent=2)
    return {"dir": d, "json": p}


def build_all_distribution_packages(meta, files, out_dir):
    meta.ensure()
    os.makedirs(out_dir, exist_ok=True)
    result = {
        "spotify_dsp": build_spotify_package(meta, files, out_dir),
        "yandex_vk_ru": build_yandex_vk_package(meta, files, out_dir),
        "tiktok": build_tiktok_package(meta, files, out_dir),
        "youtube": build_youtube_package(meta, files, out_dir),
        "shazam_ready": build_shazam_package(meta, out_dir),
    }
    manifest_path = os.path.join(out_dir, "distribution_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({"meta": asdict(meta), "files_used": files.existing(),
                   "packages": result,
                   "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                   "generator": "ZS Music Maker v11"},
                  f, ensure_ascii=False, indent=2)
    result["manifest"] = {"path": manifest_path}
    _safe_print(f"[dist_v11] all packages built at {out_dir}")
    return result


def _self_test():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        meta = TrackMetadata(title="Test", artist="ZS", bpm=140.0,
                             duration_sec=150.0,
                             tags=["car", "лето"],
                             lyrics_ru="test", lyrics_en_hook="test hook")
        for p in ["m.wav", "m.mp3", "c.png", "l.txt", "t.mp4"]:
            with open(os.path.join(tmp, p), "wb") as f:
                f.write(b"\0")
        files = ReleaseFiles(master_wav=os.path.join(tmp, "m.wav"),
                             mp3_320=os.path.join(tmp, "m.mp3"),
                             cover_png=os.path.join(tmp, "c.png"),
                             lyrics_txt=os.path.join(tmp, "l.txt"),
                             tiktok_mp4=os.path.join(tmp, "t.mp4"))
        res = build_all_distribution_packages(meta, files,
                                              os.path.join(tmp, "dist"))
        ok = all(k in res for k in ["spotify_dsp", "yandex_vk_ru", "tiktok",
                                    "youtube", "shazam_ready", "manifest"])
        ok &= os.path.exists(res["manifest"]["path"])
        return ok


if __name__ == "__main__":
    print("distribution_export_v11 self-test:",
          "OK" if _self_test() else "FAIL")
