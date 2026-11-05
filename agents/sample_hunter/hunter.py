# -*- coding: utf-8 -*-
"""
agents/sample_hunter/hunter.py — публичный API поиска сэмплов.

`hunt()` отдаёт split-view local + online, `unified_search()` — полный отчёт
по стилевому вектору. Лицензионный фильтр применяется всегда и честно
сообщает статус в `license_filter`.
"""

from __future__ import annotations

import time

from agents.sample_hunter.license import _license_gate
from agents.sample_hunter.local import list_local
from agents.sample_hunter.planner import plan_queries
from agents.sample_hunter.web import (
    search_archive_org,
    search_freesound_web,
    search_pixabay,
    search_wikimedia,
)


def search_online(query, limit: int = 10) -> list[dict]:
    """Онлайн-поиск. Принимает строку или style_vector (тогда работает planner)."""
    if isinstance(query, dict):
        queries = plan_queries(query, max_queries=4)
    else:
        queries = [str(query)]
    hits: list[dict] = []
    for text in queries:
        for finder in (search_freesound_web, search_wikimedia, search_archive_org, search_pixabay):
            try:
                hits.extend(finder(text, limit=limit))
            except Exception:
                continue
    return _license_gate(hits)


def unified_search(
    style_vector: dict,
    include_local: bool = True,
    include_online: bool = True,
    max_total: int = 60,
) -> dict:
    result = {
        "queries": plan_queries(style_vector),
        "local": [],
        "online": [],
        "ts": time.time(),
    }
    if include_local:
        result["local"] = list_local()
    if include_online:
        result["online"] = search_online(style_vector, limit=max_total)
    result["total"] = len(result["local"]) + len(result["online"])
    return result


def hunt(
    query: str,
    max_results: int = 8,
    allow_online: bool = True,
    license_filter: bool = True,
) -> dict:
    """Главная точка: split-view local + online с лицензионным фильтром."""
    local = list_local(query)
    online = search_online(query, limit=max_results) if allow_online else []

    license_status: dict = {"ok": False, "status": "not_requested"}
    if license_filter:
        try:
            from app.core.license_manager import is_free_commercial

            online = [
                sample
                for sample in online
                if is_free_commercial(sample.get("license", "unknown"))
            ]
            license_status = {"ok": True, "status": "applied"}
        except Exception as exc:  # noqa: BLE001 - fail closed by design
            online = []
            license_status = {
                "ok": False,
                "status": "failed_closed",
                "error": f"{type(exc).__name__}: {exc}",
            }

    return {
        "ok": True,
        "query": query,
        "license_filter": license_status,
        "local": local[:max_results],
        "online": online[:max_results],
        "samples": local[:max_results] + online[:max_results],
        "provenance": [
            {
                "name": sample.get("name"),
                "source": sample.get("source"),
                "license": sample.get("license"),
                "url": sample.get("url") or sample.get("path", ""),
            }
            for sample in online
        ],
    }
