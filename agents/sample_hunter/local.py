# -*- coding: utf-8 -*-
"""
agents/sample_hunter/local.py — локальная библиотека пользователя и manifest.

Локальные сэмплы не проверяются лицензионным gate: это его собственная
коллекция. Manifest фиксирует происхождение каждого скачанного сэмпла.
"""

from __future__ import annotations

import json
import time

from agents.sample_hunter.config import AUDIO_EXT, CACHE, LOCAL_LIB, MANIFEST_DIR


def list_local(query: str = "") -> list[dict]:
    """Сэмплы пользователя из `samples_cache/` (фильтр по подстроке имени)."""
    if not LOCAL_LIB.exists():
        return []
    needle = (query or "").lower()
    items: list[dict] = []
    for path in sorted(LOCAL_LIB.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in AUDIO_EXT:
            continue
        if needle and needle not in path.name.lower():
            continue
        size_bytes = path.stat().st_size
        items.append(
            {
                "name": path.name,
                "path": str(path),
                "size": size_bytes,
                "size_kb": round(size_bytes / 1024, 1),
                "source": "local",
                "license": "user_supplied",
                "url": None,
            }
        )
    return items


def download_to_cache(item: dict) -> str | None:
    """Скачать онлайн-сэмпл в `samples_cache/` и вернуть локальный путь."""
    if item.get("source") == "local":
        return item.get("path")
    url = item.get("url")
    if not url:
        return None
    from app.core.security_utils import download_file, safe_hash

    CACHE.mkdir(parents=True, exist_ok=True)
    digest = safe_hash(url)[:10]
    raw_name = f"{item.get('source', 'online')}_{digest}_{item.get('name', 'sample')[:30]}"
    safe_name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in raw_name)
    target = CACHE / safe_name
    if target.exists():
        return str(target)
    if download_file(url, str(target)):
        return str(target)
    return None


def save_manifest(items: list[dict], project_id: str) -> str:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    path = MANIFEST_DIR / f"{project_id}_samples.json"
    payload = {
        "project_id": project_id,
        "ts": time.time(),
        "total": len(items),
        "items": items,
        "notice": "Все сэмплы — CC0 / CC-BY / PD или локальная библиотека пользователя.",
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)
