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
    return (base + bpm_queries)[:max_queries]
