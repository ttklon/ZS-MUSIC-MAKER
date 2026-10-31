# -*- coding: utf-8 -*-
"""
modules/artist_dossier/schema.py — пути досье, идентификаторы и нормализация.

Досье артиста версионируется схемой `data/artist_dossier/schema.json`; здесь
же живёт миграция legacy-алиасов (`core_themes` ↔ `themes`, `lexicon` ↔
`slang`) и проверка «deferred»-профилей, которые нельзя выдавать за готовые.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[2]
DOSSIER_ROOT = ROOT / "data" / "artist_dossier"
DOSSIER_SCHEMA_PATH = DOSSIER_ROOT / "schema.json"
DOSSIER_ROOT.mkdir(parents=True, exist_ok=True)


def _slug(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9а-яА-ЯёЁ_-]+", "_", (name or "unknown").strip()).strip("_")
    return s.lower() or "unknown"


def _track_id(title: str, url: str = "") -> str:
    base = (title or "") + "|" + (url or "")
    return _slug(title)[:32] + "_" + hashlib.md5(base.encode("utf-8")).hexdigest()[:8]


def artist_dossier_schema() -> Dict[str, Any]:
    """Load the versioned schema so persisted content and schema drift together."""
    return json.loads(DOSSIER_SCHEMA_PATH.read_text(encoding="utf-8"))


def normalize_artist_dossier(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate compatible pre-v1 aliases without fabricating required content."""
    dossier = dict(payload)
    dossier["schema_version"] = 1
    dossier.setdefault("themes", list(dossier.get("core_themes") or []))
    dossier.setdefault("slang", list(dossier.get("lexicon") or []))
    dossier.setdefault("core_themes", list(dossier.get("themes") or []))
    dossier.setdefault("lexicon", list(dossier.get("slang") or []))
    dossier.setdefault("signature_tricks", [])
    dossier.setdefault("avoid", [])
    return dossier


def is_deferred_artist_dossier(payload: Dict[str, Any]) -> bool:
    """Deferred/no-model metadata is not misclassified as a completed dossier."""
    return bool(payload.get("note") or payload.get("deferred")) and not payload.get("bio")


def validate_artist_dossier(payload: Any) -> Dict[str, Any]:
    """Validate a complete artist dossier against the versioned v1 contract."""
    if not isinstance(payload, dict):
        return {"ok": False, "reason": "artist dossier is not an object", "metrics": {}}
    schema = artist_dossier_schema()
    required = tuple(schema.get("required", ()))
    missing = [key for key in required if key not in payload]
    if missing:
        return {"ok": False, "reason": "missing artist dossier fields: " + ", ".join(missing), "metrics": {"missing": len(missing)}}
    if payload.get("schema_version") != 1:
        return {"ok": False, "reason": "unsupported artist dossier schema_version", "metrics": {}}
    text_fields = ("bio", "flow")
    list_fields = ("themes", "slang", "analogs", "core_themes", "lexicon", "signature_tricks", "avoid")
    invalid = [key for key in text_fields if not isinstance(payload.get(key), str) or not payload[key].strip()]
    invalid.extend(key for key in list_fields if not isinstance(payload.get(key), list) or not all(isinstance(item, str) for item in payload[key]))
    for key in ("themes", "analogs", "core_themes"):
        if not payload.get(key):
            invalid.append(key)
    if invalid:
        return {"ok": False, "reason": "invalid artist dossier fields: " + ", ".join(sorted(set(invalid))), "metrics": {"invalid": len(set(invalid))}}
    return {"ok": True, "reason": None, "metrics": {"required": len(required), "keys": len(payload)}}
