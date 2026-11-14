# -*- coding: utf-8 -*-
"""
app/cli/hitfactory.py — CLI обработчик для --hit-factory
"""
from __future__ import annotations

from app.cli.env import safe_print


def run_hit_factory(args) -> int:
    try:
        from modules.hit_factory.generator import HitFactory
    except Exception as exc:  # noqa: BLE001
        safe_print(f"[hit-factory] import failed: {exc}")
        return 2

    count = int(getattr(args, "hit_count", 1) or 1)
    genre = getattr(args, "hit_genre", "") or None
    theme = getattr(args, "hit_theme", "") or None
    seed = getattr(args, "hit_seed", None)
    duration = getattr(args, "hit_duration", None)
    min_score = float(getattr(args, "hit_min_score", 68.0) or 68.0)
    evolve = not bool(getattr(args, "hit_no_evolve", False))

    if genre == "":
        genre = None
    if theme == "":
        theme = None

    factory = HitFactory(min_score=min_score, evolve=evolve, verbose=True)
    try:
        if count <= 1:
            hit = factory.make_one(genre=genre, theme=theme, seed=seed, duration_sec=duration)
            safe_print(f"[hit-factory] done: {hit.get('project_id')} score={hit.get('hit_score')} verdict={hit.get('verdict')}")
            return 0 if hit.get("master_path") else 1
        batch = factory.make_batch(count=count, genre=genre, theme=theme, seed=seed, duration_sec=duration)
        ok = sum(1 for r in batch if r.get("master_path"))
        safe_print(f"[hit-factory] batch done: {ok}/{len(batch)} masters")
        return 0 if ok else 1
    except Exception as exc:  # noqa: BLE001
        safe_print(f"[hit-factory] failed: {type(exc).__name__}: {exc}")
        return 2
