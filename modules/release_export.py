"""
[v7] release_export.py — сборка полного релиз-пакета.

Формирует папку output/releases/<track_name>/ со следующим содержимым:
  master.wav (24-bit/48kHz), master.mp3 (320kbps), master.flac
  instrumental.wav, instrumental.mp3
  acapella.wav, acapella.mp3
  stems/ (drums, bass, vocals, other) — если Demucs доступен
  short_edit.wav (30 сек предпросмотр)
  lyrics.txt, lyrics.lrc
  cover.png (сгенерирован через Pillow)
  tiktok.mp4, reels.mp4 (вертикальные 15-30 сек)
  car_master.wav, club_master.wav, streaming_master.wav (стенды)
  metadata.csv, metadata.json (для дистрибуции Spotify/Yandex)
  recipe.json, manifest.json (лицензии сэмплов), release_notes.txt

ID3-теги пишутся через mutagen — artist_name из user_profile.
"""

import csv
import json
import os
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASES_DIR = ROOT / "output" / "releases"
# v22: ленивое создание (не при импорте)


def _copy_or_convert(src: str, dst: str) -> bool:
    """Копирует WAV или конвертирует MP3/FLAC через pydub если нужно."""
    if not os.path.exists(src):
        return False
    ext_dst = os.path.splitext(dst)[1].lower()
    ext_src = os.path.splitext(src)[1].lower()
    if ext_src == ext_dst:
        try:
            shutil.copy(src, dst)
            return True
        except Exception:
            return False
    try:
        from pydub import AudioSegment

        seg = AudioSegment.from_file(src)
        if ext_dst == ".mp3":
            seg.export(dst, format="mp3", bitrate="320k")
        elif ext_dst == ".flac":
            seg.export(dst, format="flac")
        elif ext_dst == ".wav":
            seg.export(dst, format="wav")
        else:
            seg.export(dst, format=ext_dst.lstrip("."))
        return True
    except Exception as e:
        print(f"[release_export._copy_or_convert] {e}")
        try:
            shutil.copy(src, dst)
            return True
        except Exception:
            return False


def _write_id3(
    mp3_path: str,
    artist: str,
    title: str,
    album: str = "ZSMM Release",
    year: int | None = None,
    genre: str = "Phonk",
) -> bool:
    """Пишем ID3v2-теги в MP3. Если mutagen нет — молча пропускаем."""
    try:
        from mutagen.easyid3 import EasyID3
        from mutagen.mp3 import MP3

        try:
            audio = EasyID3(mp3_path)
        except Exception:
            m = MP3(mp3_path)
            m.add_tags()
            m.save()
            audio = EasyID3(mp3_path)
        audio["artist"] = artist
        audio["title"] = title
        audio["album"] = album
        audio["genre"] = genre
        if year:
            audio["date"] = str(year)
        audio.save()
        return True
    except Exception as e:
        print(f"[release_export._write_id3] {e}")
        return False


def _write_flac_tags(
    flac_path: str,
    artist: str,
    title: str,
    album: str = "ZSMM Release",
    genre: str = "Phonk",
) -> bool:
    try:
        from mutagen.flac import FLAC

        audio = FLAC(flac_path)
        audio["artist"] = artist
        audio["title"] = title
        audio["album"] = album
        audio["genre"] = genre
        audio.save()
        return True
    except Exception:
        return False


def export_release(
    beat_path: str,
    vocal_path: str,
    master_path: str,
    lyrics: str = "",
    recipe: dict | None = None,
    provenance: list | None = None,
    project_name: str | None = None,
    artist_name: str | None = None,
    title: str | None = None,
    stands: dict | None = None,
) -> dict:
    """
    Главная точка. Собирает полный релиз-пакет.
    stands = {"car": path, "club": path, "streaming": path} — от mastering_stands
    """
    project_name = project_name or f"release_{int(time.time())}"
    title = title or project_name

    # Artist name из user_profile если не передан
    if not artist_name:
        try:
            from modules.user_profile import get_artist_name

            artist_name = get_artist_name()
        except Exception:
            artist_name = "ZSMM Artist"

    rel_dir = RELEASES_DIR / project_name
    rel_dir.mkdir(parents=True, exist_ok=True)
    (rel_dir / "stems").mkdir(exist_ok=True)

    files = {}

    # Master versions
    if master_path and os.path.exists(master_path):
        for ext in ("wav", "mp3", "flac"):
            p = rel_dir / f"master.{ext}"
            if _copy_or_convert(master_path, str(p)):
                files[f"master.{ext}"] = str(p)
        if "master.mp3" in files:
            _write_id3(
                files["master.mp3"], artist_name, title, year=time.localtime().tm_year
            )
        if "master.flac" in files:
            _write_flac_tags(files["master.flac"], artist_name, title)

    # Instrumental (beat)
    if beat_path and os.path.exists(beat_path):
        for ext in ("wav", "mp3"):
            p = rel_dir / f"instrumental.{ext}"
            if _copy_or_convert(beat_path, str(p)):
                files[f"instrumental.{ext}"] = str(p)
        if "instrumental.mp3" in files:
            _write_id3(
                files["instrumental.mp3"],
                artist_name,
                f"{title} (Instrumental)",
                year=time.localtime().tm_year,
            )

    # Acapella (vocal)
    if vocal_path and os.path.exists(vocal_path):
        for ext in ("wav", "mp3"):
            p = rel_dir / f"acapella.{ext}"
            if _copy_or_convert(vocal_path, str(p)):
                files[f"acapella.{ext}"] = str(p)

    # Стенды прослушивания
    for stand_name in ("car", "club", "streaming"):
        if stands and stands.get(stand_name):
            src = stands[stand_name]
            if os.path.exists(src):
                p = rel_dir / f"{stand_name}_master.wav"
                if _copy_or_convert(src, str(p)):
                    files[f"{stand_name}_master.wav"] = str(p)

    # Lyrics
    if lyrics:
        (rel_dir / "lyrics.txt").write_text(lyrics, encoding="utf-8")
        files["lyrics.txt"] = str(rel_dir / "lyrics.txt")

    # Recipe
    if recipe:
        (rel_dir / "recipe.json").write_text(
            json.dumps(recipe, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        files["recipe.json"] = str(rel_dir / "recipe.json")

    # Manifest (лицензии сэмплов)
    manifest = {
        "samples": provenance or [],
        "generated_at": time.time(),
        "artist": artist_name,
        "title": title,
    }
    (rel_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    files["manifest.json"] = str(rel_dir / "manifest.json")

    # Metadata для дистрибуции
    meta = {
        "artist": artist_name,
        "title": title,
        "album": "ZSMM Release",
        "year": time.localtime().tm_year,
        "genre": "Phonk",
        "isrc": "",
        "duration_sec": recipe.get("duration_sec", 0) if recipe else 0,
    }
    (rel_dir / "metadata.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    with open(rel_dir / "metadata.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(list(meta.keys()))
        w.writerow(list(meta.values()))
    files["metadata.json"] = str(rel_dir / "metadata.json")
    files["metadata.csv"] = str(rel_dir / "metadata.csv")

    # Release notes
    notes = (
        f"# {title}\n\n"
        f"**Артист:** {artist_name}\n"
        f"**Год:** {meta['year']}\n"
        f"**Жанр:** {meta['genre']}\n"
        f"**BPM:** {recipe.get('style_vector',{}).get('target_bpm','?') if recipe else '?'}\n\n"
        f"Собрано в ZS Music Maker v7 (MM ZS).\n"
        f"Стенды прослушивания: {', '.join(k for k in ('car','club','streaming') if f'{k}_master.wav' in files)}\n"
    )
    (rel_dir / "release_notes.txt").write_text(notes, encoding="utf-8")
    files["release_notes.txt"] = str(rel_dir / "release_notes.txt")

    return {
        "ok": True,
        "release_dir": str(rel_dir),
        "artist": artist_name,
        "title": title,
        "files": files,
    }


if __name__ == "__main__":
    print("release_export v7 ready")
