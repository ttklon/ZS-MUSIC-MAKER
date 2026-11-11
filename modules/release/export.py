# -*- coding: utf-8 -*-
"""
modules/release/export.py — экспорт релизного пакета с отпечатками файлов.

Пакет содержит мастер, текст, метаданные, рецепт, release_notes и ZIP.
ISRC включается только при явном вводе, его присвоение не проверяется. У каждого артефакта считается SHA-256 — дистрибьютор
и проверяющий видят, что именно уехало в релиз.

Никаких сгенерированных ISRC: без введённого кода поле пустое и стоит
`UNREGISTERED`; введённый код помечается `USER_SUPPLIED_UNVERIFIED`.
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:  # тегирование — необязательная зависимость, отказ обязан быть виден
    from mutagen.wave import WAVE

    HAS_MUTAGEN = True
except Exception:  # pragma: no cover - окружение без mutagen
    WAVE = None
    HAS_MUTAGEN = False

ROOT = Path(__file__).resolve().parents[2]
RELEASES_DIR = ROOT / "output" / "releases"


def sha256_file(path: str | Path, chunk: int = 1 << 20) -> str:
    """SHA-256 файла потоком: большие WAV не читаются в память целиком."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


def _resolve_artist_name(artist_name: str | None) -> str:
    return (artist_name or "ZS Music Maker").strip() or "ZS Music Maker"


def _isrc_for(meta: dict[str, Any]) -> tuple[str, str]:
    """Только введённый код; синтаксис не подтверждает присвоение."""
    try:
        from app.core.isrc import get_isrc

        value = get_isrc(meta)
        return value, "USER_SUPPLIED_UNVERIFIED" if value else "UNREGISTERED"
    except Exception:
        return "", "UNREGISTERED"


def _release_notes(meta: dict[str, Any], manifest: dict[str, Any]) -> str:
    lines = [
        f"# {meta.get('title') or 'Untitled'} — {meta.get('artist') or 'Unknown artist'}",
        "",
        f"- Жанр: {meta.get('genre') or 'n/a'}",
        f"- BPM: {meta.get('bpm') or 'n/a'}",
        f"- Тональность: {meta.get('key') or 'n/a'}",
        f"- Длительность: {meta.get('duration_sec') or 'n/a'} с",
        f"- ISRC: {manifest['metadata']['isrc'] or 'не указан'} ({manifest['metadata']['isrc_status']})",
        f"- Артефактов в пакете: {len(manifest['artifacts_sha256'])}",
        "",
        "## Что внутри",
        "",
    ]
    for name in sorted(manifest["artifacts_sha256"]):
        lines.append(f"- `{name}` — sha256 `{manifest['artifacts_sha256'][name][:16]}…`")
    lines.append("")
    lines.append("Пакет собран ZS Music Maker; мастер-файл — единственный источник звука.")
    return "\n".join(lines) + "\n"


def _metadata_rows(meta: dict[str, Any], isrc: str) -> list[dict[str, str]]:
    return [
        {"field": "title", "value": str(meta.get("title") or "")},
        {"field": "artist", "value": str(meta.get("artist") or "")},
        {"field": "album", "value": str(meta.get("album") or "")},
        {"field": "genre", "value": str(meta.get("genre") or "")},
        {"field": "bpm", "value": str(meta.get("bpm") or "")},
        {"field": "key", "value": str(meta.get("key") or "")},
        {"field": "isrc", "value": isrc},
        {"field": "language", "value": str(meta.get("language") or "ru")},
        {"field": "year", "value": str(meta.get("year") or datetime.now(timezone.utc).year)},
    ]


def _archive_release(release_dir: Path, zip_path: Path) -> bool:
    """ZIP без вложенного самого себя: релиз должен открываться в один клик."""
    try:
        release_dir = release_dir.resolve()
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(release_dir.rglob("*")):
                if path.is_dir() or path.resolve() == zip_path.resolve():
                    continue
                archive.write(path, path.relative_to(release_dir))
        return True
    except Exception:
        return False


def refresh_zip(release_dir: str | Path) -> bool:
    """Пересобирает ZIP после того, как пакет дописали (манифест, каналы, стемы).

    Без этого в архиве остаётся устаревший `manifest.json` — пользователь
    открывает ZIP и видит не то, что реально лежит в папке релиза.
    """
    release_dir = Path(release_dir)
    zip_path = release_dir / "release.zip"
    if zip_path.exists():
        try:
            zip_path.unlink()
        except OSError:
            return False
    return _archive_release(release_dir, zip_path)


def tag_release_master(path: str | Path, meta: dict[str, Any]) -> dict[str, Any]:
    """Проставить ID3-теги файлу релизного пакета (никогда — мастеру проекта).

    WAV-теги пишутся через `mutagen.wave.WAVE` + ID3-кадры: `EasyID3` работает
    с файлами, у которых уже есть контейнер ID3, поэтому «с нуля» используется
    `WAVE.add_tags()`. Ошибка или отсутствие `mutagen` — честный
    `{"ok": False, "reason": ...}`, а не тихий пропуск.
    """
    target = Path(path)
    if not HAS_MUTAGEN:
        return {
            "ok": False,
            "reason": "mutagen is not installed; release master has no ID3 tags",
            "engine": "mutagen",
        }
    if target.suffix.lower() != ".wav":
        return {
            "ok": False,
            "reason": f"ID3 tagging is only wired for WAV, got {target.suffix or 'no suffix'}",
            "engine": "mutagen",
        }

    values = {
        "title": str(meta.get("title") or "").strip(),
        "artist": str(meta.get("artist") or "").strip(),
        "album": str(meta.get("album") or meta.get("title") or "").strip(),
        "genre": str(meta.get("genre") or "").strip(),
        "date": str(meta.get("year") or datetime.now(timezone.utc).year),
        "tracknumber": str(meta.get("track_number") or 1),
    }
    frames = {
        "title": "TIT2",
        "artist": "TPE1",
        "album": "TALB",
        "genre": "TCON",
        "date": "TDRC",
        "tracknumber": "TRCK",
    }
    try:
        audio = WAVE(str(target))
        try:
            audio.add_tags()
        except Exception:
            # контейнер уже есть — перезаписываем существующие кадры
            pass
        written: dict[str, str] = {}
        for key, frame in frames.items():
            value = values[key]
            if not value:
                continue
            from mutagen import id3 as id3_frames

            audio.tags.delall(frame)
            audio.tags.add(id3_frames.__dict__[frame](encoding=3, text=[value]))
            written[key] = value
        audio.save()
        return {
            "ok": True,
            "engine": "mutagen.wave",
            "tags": written,
            "file": str(target),
            "note": "tags are written to the release copy only",
        }
    except Exception as exc:  # noqa: BLE001 - причина важнее стека
        return {
            "ok": False,
            "engine": "mutagen.wave",
            "reason": f"{type(exc).__name__}: {exc}",
            "file": str(target),
        }


def _wav_duration_sec(path: str | Path | None) -> float:
    """Длительность WAV по заголовку: RIFF → fmt (каналы, частота) → data.

    Читаем только заголовок, без numpy и librosa: выпуск релиза не должен
    требовать тяжёлых зависимостей ради одного числа. Нужна точность до
    сэмпла, а не анализ — площадка получает `duration` в структурированных
    данных, и «PT0S» там означает битый файл.
    """
    import struct

    if not path:
        return 0.0
    try:
        with open(path, "rb") as handle:
            header = handle.read(12)
            if len(header) < 12 or header[:4] != b"RIFF" or header[8:12] != b"WAVE":
                return 0.0
            channels = sample_rate = bits = 0
            data_size = 0
            while True:
                chunk = handle.read(8)
                if len(chunk) < 8:
                    break
                chunk_id = chunk[:4]
                size = struct.unpack("<I", chunk[4:])[0]
                if chunk_id == b"fmt ":
                    fmt = handle.read(size)
                    if len(fmt) >= 16:
                        channels = struct.unpack("<H", fmt[2:4])[0]
                        sample_rate = struct.unpack("<I", fmt[4:8])[0]
                        bits = struct.unpack("<H", fmt[14:16])[0]
                    if size % 2:
                        handle.seek(1, 1)
                elif chunk_id == b"data":
                    data_size = size
                    break
                else:
                    handle.seek(size + (size % 2), 1)
        if channels and sample_rate and bits and data_size:
            frames = data_size / max(1, channels * (bits // 8))
            return round(frames / sample_rate, 3)
    except OSError:
        return 0.0
    return 0.0


def _resolve_key(meta: dict[str, Any]) -> str:
    """Тональность одной строкой: «A minor».

    Оркестратор кладёт в рецепт корень и лад отдельными полями (`key_root`,
    `mode`, лад приходит как `target_mode`), а площадки ждут одну строку.
    Раньше в `metadata.json` оставалась пустая строка при известной тональности.
    """
    key = str(meta.get("key") or "").strip()
    if key:
        return key
    root = str(meta.get("key_root") or "").strip()
    mode = str(
        meta.get("mode") or meta.get("target_mode") or meta.get("scale") or ""
    ).strip().lower()
    if not root:
        return ""
    return f"{root} {mode}".strip() if mode else root


def fill_missing_facts(meta: dict[str, Any], master_path: str | Path | None) -> dict[str, Any]:
    """Дописать в метаданные то, что знает сам мастер: длительность и тональность.

    Пакет каналов собирается раньше экспорта, поэтому обе точки входа зовут
    этот помощник: иначе `shazam.jsonld` утверждал `"duration": "PT0S"`.
    """
    if not meta.get("duration_sec"):
        meta["duration_sec"] = _wav_duration_sec(master_path)
    if not meta.get("key"):
        meta["key"] = _resolve_key(meta)
    return meta


# Открытые имена для `pack.py`.
wav_duration_sec = _wav_duration_sec
resolve_key = _resolve_key


def export_release(
    beat_path: str,
    vocal_path: str,
    master_path: str,
    lyrics: str = "",
    recipe: dict[str, Any] | None = None,
    project_name: str = "release",
    artist_name: str | None = None,
    title: str = "",
    out_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Собирает релизный пакет и возвращает пути + отпечатки артефактов."""
    try:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in project_name)
        release_dir = Path(out_dir) if out_dir else RELEASES_DIR / f"{safe_name}_{stamp}"
        release_dir.mkdir(parents=True, exist_ok=True)

        source = dict(recipe or {})
        meta = fill_missing_facts({
            "title": title or project_name,
            "artist": _resolve_artist_name(artist_name),
            "genre": source.get("genre", ""),
            "bpm": source.get("bpm", ""),
            "key": _resolve_key(source),
            "duration_sec": source.get("duration_sec", ""),
            "isrc": source.get("isrc", ""),
        }, master_path)
        isrc, isrc_status = _isrc_for(meta)
        meta["isrc"] = isrc
        meta["isrc_status"] = isrc_status

        files: dict[str, str] = {}
        artifacts: dict[str, str] = {}

        for key, source in (("beat", beat_path), ("vocal", vocal_path), ("master", master_path)):
            if not source or not Path(source).is_file():
                continue
            name = "master.wav" if key == "master" else f"{key}.wav"
            destination = release_dir / name
            if Path(source).resolve() != destination.resolve():
                shutil.copy(source, destination)
            files[name] = str(destination)
            artifacts[name] = sha256_file(destination)

        # Теги ставим только на копию в релизном пакете: мастер проекта
        # остаётся бит-в-бит тем же (это проверяется тестом по SHA-256).
        id3_report: dict[str, Any] = {"ok": False, "reason": "no master in release package"}
        if "master.wav" in files:
            id3_report = tag_release_master(release_dir / "master.wav", meta)
            if id3_report.get("ok"):
                artifacts["master.wav"] = sha256_file(release_dir / "master.wav")

        lyrics_text = lyrics or ""
        (release_dir / "lyrics.txt").write_text(lyrics_text, encoding="utf-8")
        files["lyrics.txt"] = str(release_dir / "lyrics.txt")

        (release_dir / "recipe.json").write_text(
            json.dumps(recipe or {}, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        files["recipe.json"] = str(release_dir / "recipe.json")

        (release_dir / "metadata.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
        )
        files["metadata.json"] = str(release_dir / "metadata.json")

        with open(release_dir / "metadata.csv", "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["field", "value"])
            writer.writeheader()
            writer.writerows(_metadata_rows(meta, isrc))
        files["metadata.csv"] = str(release_dir / "metadata.csv")

        manifest: dict[str, Any] = {
            "project": safe_name,
            "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "metadata": meta,
            "artifacts_sha256": artifacts,
            "id3": id3_report,
        }
        # SHA-256 остальных текстовых артефактов: манифест должен покрывать всё.
        for name in ("lyrics.txt", "recipe.json", "metadata.json", "metadata.csv"):
            path = release_dir / name
            if path.is_file():
                artifacts[name] = sha256_file(path)

        (release_dir / "release_notes.txt").write_text(
            _release_notes(meta, manifest), encoding="utf-8"
        )
        files["release_notes.txt"] = str(release_dir / "release_notes.txt")

        (release_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
        )
        files["manifest.json"] = str(release_dir / "manifest.json")

        zip_path = release_dir / "release.zip"
        archived = _archive_release(release_dir, zip_path)
        if archived:
            files["release.zip"] = str(zip_path)

        return {
            "ok": True,
            "engine": "modules.release.export",
            "release_dir": str(release_dir),
            "files": files,
            "manifest": manifest,
            "isrc": isrc,
            "isrc_status": isrc_status,
            "id3": id3_report,
            "zip": archived,
        }
    except Exception as exc:  # noqa: BLE001 - отчёт о сбое важнее стека
        return {"ok": False, "engine": "modules.release.export", "reason": f"{type(exc).__name__}: {exc}"}


if __name__ == "__main__":  # pragma: no cover - ручная проверка
    print(json.dumps({"releases_dir": str(RELEASES_DIR)}, ensure_ascii=False, indent=2))
