# -*- coding: utf-8 -*-
"""
agents/sample_hunter/planner.py — превращает стилевой вектор в поисковые запросы.
"""

from __future__ import annotations

from agents.sample_hunter.config import GENRE_KEYWORDS


def plan_queries(style_vector: dict, max_queries: int = 8) -> list[str]:
    """Разложить style_vector на пачку целевых поисковых запросов."""
    style = style_vector or {}
    genre = style.get("genre_hint") or style.get("genre") or "generic hit"
    bpm = int(round(float(style.get("bpm", 130.0) or 130.0)))
    base = GENRE_KEYWORDS.get(genre, GENRE_KEYWORDS["generic hit"])[:]
    bpm_queries = [f"loop {bpm} bpm", f"drum loop {bpm} bpm", f"bass {bpm} bpm sample"]
    merged = list(dict.fromkeys(base + bpm_queries))
    if len(merged) <= max_queries:
        return merged
    # Раньше bpm-запросы просто отрезались: у «phonk / drift» десять базовых
    # ключевых слов, и при max_queries=8 (значение по умолчанию) ни один
    # запрос с темпом не доходил до поиска. А темп — единственное, что здесь
    # берётся из style_vector, то есть адаптация к референсу терялась целиком.
    keep_bpm = bpm_queries[: max(1, min(2, max_queries // 3))]
    keep_base = [q for q in base if q not in keep_bpm][: max_queries - len(keep_bpm)]
    return (keep_base + keep_bpm)[:max_queries]
