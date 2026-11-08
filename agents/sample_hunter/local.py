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
    from app.core.security_utils import download_file, safe_hash, safe_identifier

    CACHE.mkdir(parents=True, exist_ok=True)
    digest = safe_hash(url)[:10]
    raw_name = f"{item.get('source', 'online')}_{digest}_{item.get('name', 'sample')[:30]}"
    # Имя собиралось вручную и могло содержать "..": правила безопасности
    # должны быть одни на проект. НО `safe_identifier` убирает точку, поэтому
    # санитизируется только основа, а аудио-расширение переносится отдельно —
    # иначе скачанный файл терял `.wav` и пропадал из `list_local` (там фильтр
    # по AUDIO_EXT), оставаясь на диске невидимым для пользователя.
    stem, dot, ext = raw_name.rpartition(".")
    if dot and f".{ext.lower()}" in AUDIO_EXT:
        safe_name = f"{safe_identifier(stem, fallback=f'sample_{digest}')}.{ext.lower()}"
    else:
        safe_name = safe_identifier(raw_name, fallback=f"sample_{digest}")
    target = CACHE / safe_name
    if target.exists():
        return str(target)
    if download_file(url, str(target)):
        # `download_file` возвращает True/False, но пустой ответ или сбой
        # записи могут оставить нулевой файл: путь отдаём только за реальный.
        if target.exists() and target.stat().st_size > 0:
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
