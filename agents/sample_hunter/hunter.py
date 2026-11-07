# -*- coding: utf-8 -*-
"""
agents/sample_hunter/hunter.py — публичный API поиска сэмплов.

`hunt()` отдаёт split-view local + online, `unified_search()` — полный отчёт
по стилевому вектору. Лицензионный фильтр применяется всегда и честно
сообщает статус в `license_filter`.
"""

from __future__ import annotations

import inspect
import time

from app.core.net_policy import network_allowed, offline_reason
from agents.sample_hunter.license import _license_gate
from agents.sample_hunter.local import list_local
from agents.sample_hunter.planner import plan_queries
# Источники берутся через модуль во время вызова: иначе подмена функции
# (`web.search_* = ...`) в тестах и экспериментах молча игнорировалась бы.
from agents.sample_hunter import web as web_sources


def search_online(query, limit: int = 10, diagnostics_out: dict | None = None) -> list[dict]:
    """Онлайн-поиск. Принимает строку или style_vector (тогда работает planner).

    Сбой источника не роняет поиск, но и не исчезает: причина складывается в
    `diagnostics_out` по имени источника (как в `trend_scout`). Раньше
    `except Exception: continue` скрывал даже `NameError` из-за пропущенных
    импортов, и пустая выдача выглядела как «ничего не нашлось».
    """
    if isinstance(query, dict):
        queries = plan_queries(query, max_queries=4)
    else:
        queries = [str(query)]
    diagnostics: dict = diagnostics_out if diagnostics_out is not None else {}
    hits: list[dict] = []
    # Имя источника в диагностике совпадает с полем `source` в результатах,
    # иначе оператору приходится сопоставлять их вручную.
    finders = (
        ("freesound_cc0", "search_freesound_web"),
        ("wikimedia", "search_wikimedia"),
        ("archive.org", "search_archive_org"),
        ("pixabay", "search_pixabay"),
    )
    for text in queries:
        for name, attribute in finders:
            try:
                hits.extend(getattr(web_sources, attribute)(text, limit=limit))
            except Exception as exc:  # noqa: BLE001 - источник не должен ронять поиск
                diagnostics[name] = {
                    "ok": False,
                    "query": text,
                    "error": f"{type(exc).__name__}: {exc}",
                }
    if not diagnostics:
        diagnostics["status"] = "all sources answered"
    return _license_gate(hits)


def _search_online_with_diagnostics(query, limit: int, diagnostics: dict) -> list[dict]:
    """Позвать `search_online`, передав диагностику, если функция её принимает.

    Тесты и внешние вызовы подменяют `search_online` простой функцией
    `(query, limit)`; безусловная передача лишнего аргумента ломала такие
    подмены. Сигнатура проверяется заранее, поэтому подменённая функция
    вызывается ровно один раз.
    """
    try:
        accepts = "diagnostics_out" in inspect.signature(search_online).parameters
    except (TypeError, ValueError):  # встроенная или неинтроспектируемая подмена
        accepts = False
    if accepts:
        return search_online(query, limit=limit, diagnostics_out=diagnostics)
    diagnostics["status"] = "diagnostics unavailable: search_online override"
    return search_online(query, limit=limit)


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
    allow_online: bool = False,
    license_filter: bool = True,
) -> dict:
    """Главная точка: split-view local + online с лицензионным фильтром.

    Сеть по умолчанию выключена: онлайн-поиск требует явного `allow_online=True`
    или настройки `network.online=true`. В результате видно `offline`.
    """
    local = list_local(query)
    diagnostics: dict = {}
    online_enabled_now = network_allowed(allow_online)
    online = (
        _search_online_with_diagnostics(query, max_results, diagnostics)
        if online_enabled_now
        else []
    )
    if not online_enabled_now:
        diagnostics["status"] = offline_reason(allow_online)

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

    samples = local[:max_results] + online[:max_results]
    return {
        "ok": True,
        "query": query,
        "offline": not online_enabled_now,
        "license_filter": license_status,
        "diagnostics": diagnostics,
        "local": local[:max_results],
        "online": online[:max_results],
        "samples": samples,
        # `total` был только у unified_search; потребители hunt() падали на KeyError
        "total": len(samples),
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
