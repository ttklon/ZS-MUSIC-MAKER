# -*- coding: utf-8 -*-
"""
modules/release/export.py — экспорт релизного пакета с отпечатками файлов.

Пакет всегда содержит: master, тексты, метаданные с валидным ISRC, recipe,
release_notes и ZIP. У каждого артефакта считается SHA-256 — дистрибьютор
и проверяющий видят, что именно уехало в релиз.

Никаких фейковых плейсхолдеров ISRC: если валидный код получить нельзя,
поле остаётся пустым и в манифесте стоит `isrc_status: UNREGISTERED`.
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
    """Валидный ISRC или честный статус UNREGISTERED."""
    try:
        from app.core.isrc import get_isrc

        value = get_isrc(meta)
        return value, "REGISTERED" if value else "UNREGISTERED"
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
        f"- ISRC: {manifest['metadata']['isrc'] or 'не зарегистрирован'}",
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

        meta = {
            "title": title or project_name,
            "artist": _resolve_artist_name(artist_name),
            "genre": (recipe or {}).get("genre", ""),
            "bpm": (recipe or {}).get("bpm", ""),
            "key": (recipe or {}).get("key", ""),
            "duration_sec": (recipe or {}).get("duration_sec", ""),
        }
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
            "zip": archived,
        }
    except Exception as exc:  # noqa: BLE001 - отчёт о сбое важнее стека
        return {"ok": False, "engine": "modules.release.export", "reason": f"{type(exc).__name__}: {exc}"}


if __name__ == "__main__":  # pragma: no cover - ручная проверка
    print(json.dumps({"releases_dir": str(RELEASES_DIR)}, ensure_ascii=False, indent=2))
