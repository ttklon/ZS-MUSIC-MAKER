# -*- coding: utf-8 -*-
"""
modules/artist_dossier/storage.py — персистентные записи досье на диске.

Один артист = каталог `<root>/<slug>/`, в нём `artist.json` и `tracks/*.json`.
Сохранение досье артиста валидирует схему: невалидное досье не пишется молча —
оно либо отвергается, либо помечается как `deferred` при чтении legacy-файла.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from modules.artist_dossier.models import ArtistEntry, TrackEntry
from modules.artist_dossier.schema import (
    is_deferred_artist_dossier,
    normalize_artist_dossier,
    validate_artist_dossier,
)


def _artist_path(root: Path, slug: str) -> Path:
    return Path(root) / slug / "artist.json"


def _track_path(root: Path, slug: str, track_id: str) -> Path:
    return Path(root) / slug / "tracks" / f"{track_id}.json"


def save_artist(root: Path, entry: ArtistEntry) -> None:
    if entry.dossier and not is_deferred_artist_dossier(entry.dossier):
        entry.dossier = normalize_artist_dossier(entry.dossier)
        quality = validate_artist_dossier(entry.dossier)
        if not quality["ok"]:
            raise ValueError(
                "artist dossier save rejected: " + str(quality["reason"])
            )
    path = _artist_path(root, entry.slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(entry), ensure_ascii=False, indent=2), encoding="utf-8"
    )


def load_artist(root: Path, slug: str) -> Optional[ArtistEntry]:
    path = _artist_path(root, slug)
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.setdefault("tracks", [])
    payload.setdefault("dossier", {})
    payload.setdefault("added_at", 0.0)
    payload.setdefault("updated_at", 0.0)
    if payload["dossier"] and not is_deferred_artist_dossier(payload["dossier"]):
        payload["dossier"] = normalize_artist_dossier(payload["dossier"])
        quality = validate_artist_dossier(payload["dossier"])
        if not quality["ok"]:
            # Legacy-досье не удаляем и не притворяемся, что оно валидно.
            payload["dossier"] = {
                "note": "legacy artist dossier deferred: " + str(quality["reason"]),
                "deferred": True,
                "migration_from_schema": payload["dossier"].get("schema_version", 0),
            }
    return ArtistEntry(**payload)


def save_track(root: Path, slug: str, entry: TrackEntry) -> None:
    path = _track_path(root, slug, entry.track_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(entry), ensure_ascii=False, indent=2), encoding="utf-8"
    )


def load_track(root: Path, slug: str, track_id: str) -> Optional[TrackEntry]:
    path = _track_path(root, slug, track_id)
    if not path.exists():
        return None
    return TrackEntry(**json.loads(path.read_text(encoding="utf-8")))
