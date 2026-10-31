# -*- coding: utf-8 -*-
"""
app/ai/quality/metadata.py — проверка метаданных релиза (ID3-контракт).
"""

from __future__ import annotations

from typing import Any


METADATA_FORBIDDEN_TERMS = ("as an ai", "chatgpt", "language model", "нейросеть", "нейра-говно")


def validate_metadata_json(payload: Any) -> dict[str, Any]:
    """Validate release metadata lengths, tag uniqueness and AI-filler exclusion."""
    if not isinstance(payload, dict):
        return {"ok": False, "reason": "metadata response is not an object", "metrics": {}}
    title = str(payload.get("title") or "").strip()
    descriptions = {
        key: str(payload.get(key) or "").strip()
        for key in ("spotify_desc", "youtube_desc")
    }
    tags = [
        str(tag).strip().lstrip("#").lower()
        for key, value in payload.items()
        if key.startswith("tags_") and isinstance(value, list)
        for tag in value
        if str(tag).strip()
    ]
    invalid: list[str] = []
    if not 3 <= len(title) <= 80:
        invalid.append("title")
    if any(not 20 <= len(value) <= 400 for value in descriptions.values()):
        invalid.append("description")
    if not tags:
        invalid.append("hashtags")
    elif len(tags) > 8:
        invalid.append("hashtags_count")
    elif len(set(tags)) != len(tags):
        invalid.append("hashtags_unique")
    text = " ".join((title, *descriptions.values())).lower()
    forbidden_hits = [term for term in METADATA_FORBIDDEN_TERMS if term in text]
    if forbidden_hits:
        invalid.append("forbidden_terms")
    metrics = {
        "keys": len(payload),
        "tags": len(tags),
        "unique_tags": len(set(tags)),
        "title_length": len(title),
        "description_lengths": {key: len(value) for key, value in descriptions.items()},
        "forbidden_hits": forbidden_hits,
    }
    if invalid:
        return {
            "ok": False,
            "reason": "invalid metadata fields: " + ", ".join(invalid),
            "metrics": metrics,
        }
    return {"ok": True, "reason": None, "metrics": metrics}
