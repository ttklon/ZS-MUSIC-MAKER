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
import hashlib
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


def _write_release_documents(
    release_dir: Path,
    files: dict[str, str],
    lyrics: str,
    recipe: dict | None,
    provenance: list | None,
    artist_name: str,
    title: str,
) -> dict:
    """Write release texts and metadata, returning the manifest payload."""
    if lyrics:
        lyrics_path = release_dir / "lyrics.txt"
        lyrics_path.write_text(lyrics, encoding="utf-8")
        files["lyrics.txt"] = str(lyrics_path)
    if recipe:
        recipe_path = release_dir / "recipe.json"
        recipe_path.write_text(json.dumps(recipe, ensure_ascii=False, indent=2), encoding="utf-8")
        files["recipe.json"] = str(recipe_path)

    manifest = {
        "samples": provenance or [],
        "generated_at": time.time(),
        "artist": artist_name,
        "title": title,
    }
    manifest_path = release_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    files["manifest.json"] = str(manifest_path)

    from app.core.isrc import get_isrc

    metadata = {
        "artist": artist_name,
        "title": title,
        "album": "ZSMM Release",
        "year": time.localtime().tm_year,
        "genre": "Phonk",
        "isrc": get_isrc(
            {"title": title, "artist": artist_name, "year": time.localtime().tm_year},
            fallback="",
        ),
        "duration_sec": recipe.get("duration_sec", 0) if recipe else 0,
    }
    metadata_path = release_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    with open(release_dir / "metadata.csv", "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(list(metadata.keys()))
        writer.writerow(list(metadata.values()))
    files["metadata.json"] = str(metadata_path)
    files["metadata.csv"] = str(release_dir / "metadata.csv")

    notes = (
        f"# {title}\n\n"
        f"**Артист:** {artist_name}\n"
        f"**Год:** {metadata['year']}\n"
        f"**Жанр:** {metadata['genre']}\n"
        f"**BPM:** {recipe.get('style_vector',{}).get('target_bpm','?') if recipe else '?'}\n\n"
        f"Собрано в ZS Music Maker v7 (MM ZS).\n"
        f"Стенды прослушивания: {', '.join(key for key in ('car','club','streaming') if f'{key}_master.wav' in files)}\n"
    )
    notes_path = release_dir / "release_notes.txt"
    notes_path.write_text(notes, encoding="utf-8")
    files["release_notes.txt"] = str(notes_path)
    return manifest


def _archive_release(release_dir: Path, files: dict[str, str], manifest: dict) -> None:
    """Persist artifact fingerprints and add the release ZIP to the file map."""
    fingerprints = {}
    for key, file_path in files.items():
        path = Path(file_path)
        if path.is_file():
            fingerprints[key] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest["artifacts_sha256"] = fingerprints
    (release_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    files["release.zip"] = shutil.make_archive(str(release_dir), "zip", root_dir=str(release_dir))


def _resolve_artist_name(artist_name: str | None) -> str:
    """Return supplied artist identity or the compatible profile/default fallback."""
    if artist_name:
        return artist_name
    try:
        from modules.user_profile import get_artist_name

        return get_artist_name()
    except Exception:
        return "ZSMM Artist"


def _copy_variant_formats(
    source_path: str,
    prefix: str,
    extensions: tuple[str, ...],
    release_dir: Path,
    files: dict[str, str],
) -> None:
    """Copy or transcode an existing source into the requested release formats."""
    if not source_path or not os.path.exists(source_path):
        return
    for extension in extensions:
        target = release_dir / f"{prefix}.{extension}"
        if _copy_or_convert(source_path, str(target)):
            files[f"{prefix}.{extension}"] = str(target)


def _export_master_variants(
    source_path: str, release_dir: Path, files: dict[str, str], artist_name: str, title: str
) -> None:
    """Package master formats and their available metadata tags."""
    _copy_variant_formats(source_path, "master", ("wav", "mp3", "flac"), release_dir, files)
    if "master.mp3" in files:
        _write_id3(files["master.mp3"], artist_name, title, year=time.localtime().tm_year)
    if "master.flac" in files:
        _write_flac_tags(files["master.flac"], artist_name, title)


def _export_instrumental_variants(
    source_path: str, release_dir: Path, files: dict[str, str], artist_name: str, title: str
) -> None:
    """Package instrumental formats and their available MP3 tag."""
    _copy_variant_formats(source_path, "instrumental", ("wav", "mp3"), release_dir, files)
    if "instrumental.mp3" in files:
        _write_id3(
            files["instrumental.mp3"], artist_name, f"{title} (Instrumental)",
            year=time.localtime().tm_year,
        )


def _export_acapella_variants(source_path: str, release_dir: Path, files: dict[str, str]) -> None:
    """Package available vocal source as WAV and MP3 acapella variants."""
    _copy_variant_formats(source_path, "acapella", ("wav", "mp3"), release_dir, files)


def _export_listening_stands(stands: dict | None, release_dir: Path, files: dict[str, str]) -> None:
    """Copy available car, club and streaming mastering-stand files."""
    for stand_name in ("car", "club", "streaming"):
        source_path = (stands or {}).get(stand_name)
        if source_path and os.path.exists(source_path):
            target = release_dir / f"{stand_name}_master.wav"
            if _copy_or_convert(source_path, str(target)):
                files[f"{stand_name}_master.wav"] = str(target)


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

    artist_name = _resolve_artist_name(artist_name)

    rel_dir = RELEASES_DIR / project_name
    rel_dir.mkdir(parents=True, exist_ok=True)
    (rel_dir / "stems").mkdir(exist_ok=True)

    files = {}

    _export_master_variants(master_path, rel_dir, files, artist_name, title)
    _export_instrumental_variants(beat_path, rel_dir, files, artist_name, title)
    _export_acapella_variants(vocal_path, rel_dir, files)
    _export_listening_stands(stands, rel_dir, files)

    manifest = _write_release_documents(
        rel_dir, files, lyrics, recipe, provenance, artist_name, title
    )
    _archive_release(rel_dir, files, manifest)

    return {
        "ok": True,
        "release_dir": str(rel_dir),
        "artist": artist_name,
        "title": title,
        "files": files,
    }


if __name__ == "__main__":
    print("release_export v7 ready")
