# -*- coding: utf-8 -*-
"""
agents/sample_hunter — единый поиск сэмплов: локальная библиотека + онлайн.

Источники (все бесплатные, без платных ключей): локальный `samples_cache/`,
Freesound (CC0), Wikimedia Commons (CC-BY-SA / PD), archive.org (CC / PD),
Pixabay (при наличии ключа).

Лицензии: в результаты и manifest попадают только CC0 / PD / CC-BY /
Royalty-Free; каждый онлайн-хит проходит `app.core.license_manager.
is_free_commercial`. Если валидатор недоступен — поиск **fail closed**.

Раскладка: `config` (пути/словари), `planner`, `local`, `web`, `license`,
`hunter` (публичный API).
"""

from agents.sample_hunter.hunter import hunt, search_online, unified_search  # noqa: F401
from agents.sample_hunter.license import _license_gate  # noqa: F401
from agents.sample_hunter.local import (  # noqa: F401
    download_to_cache,
    list_local,
    save_manifest,
)
from agents.sample_hunter.planner import plan_queries  # noqa: F401

__all__ = [
    "download_to_cache",
    "hunt",
    "list_local",
    "plan_queries",
    "save_manifest",
    "search_online",
    "unified_search",
]
