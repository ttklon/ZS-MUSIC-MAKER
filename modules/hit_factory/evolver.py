# -*- coding: utf-8 -*-
"""
modules.hit_factory.evolver — эволюционная петля hit_score.

mutate() — слегка сдвигает recipe (BPM ±5, aggression ±0.15, seed+1, duration вариант)
select_best() — выбирает лучшего по hit_score среди попыток.
"""
from __future__ import annotations

import random
from typing import Any

from modules.hit_factory.config import BPM_MAP, MUTATION_RANGES


def mutate(
    recipe: dict[str, Any],
    hit_report: dict[str, Any] | None = None,
    rng: random.Random | None = None,
) -> dict[str, Any]:
    """
    Мутирует recipe для следующей попытки.
    Учитывает слабые метрики из hit_report.actions если они есть.
    """
    rng = rng or random.Random(recipe.get("seed", 42) + 1)
    nxt = dict(recipe)
    cur_seed = int(nxt.get("seed", 42) or 42)
    nxt["seed"] = cur_seed + MUTATION_RANGES["seed_step"] + rng.randint(0, 7)

    # BPM мутация
    genre = str(nxt.get("genre") or "trap")
    info = BPM_MAP.get(genre) or BPM_MAP.get("default")
    lo, hi = info["range"]
    cur_bpm = int(nxt.get("bpm_override") or info["center"])
    delta = rng.randint(-MUTATION_RANGES["bpm_delta"], MUTATION_RANGES["bpm_delta"])
    # если tiktok_hookability низкая — сдвигаем BPM сильнее к центру dance
    weak = set()
    if isinstance(hit_report, dict):
        for a in hit_report.get("actions") or []:
            low = a.lower()
            if "bpm" in low:
                weak.add("bpm")
            if "tiktok" in low or "интро" in low:
                weak.add("hook_timing")
    if "bpm" in weak:
        # тянем к центру sweet spot
        target = info["center"]
        nxt["bpm_override"] = max(lo, min(hi, target + rng.randint(-2, 2)))
    else:
        nxt["bpm_override"] = max(lo, min(hi, cur_bpm + delta))
        # иногда прыгаем к альтернативному диапазону trap half-time
        if info.get("alt") and rng.random() < 0.15:
            alo, ahi = info["alt"]
            nxt["bpm_override"] = rng.randint(alo, ahi)

    # aggression мутация
    cur_agr = float(nxt.get("aggression", 0.7) or 0.7)
    dagr = rng.uniform(-MUTATION_RANGES["aggression_delta"], MUTATION_RANGES["aggression_delta"])
    nxt["aggression"] = round(max(0.3, min(0.95, cur_agr + dagr)), 2)

    # duration — иногда меняем длину (tiktok vs full влияет на структуру)
    if rng.random() < 0.25:
        nxt["duration_sec"] = rng.choice(MUTATION_RANGES["duration_variants"])

    # если слабые метрики указывают на low_end или стерео — чуть подвигаем aggression/жанр не трогаем
    # жанр оставляем тем же, чтобы не ломать expectation; смену жанра делает верхнеуровневый batch

    return nxt


def select_best(attempts: list[dict[str, Any]]) -> dict[str, Any] | None:
    """
    Выбирает лучшую попытку по hit_score.
    Каждый attempt: {recipe, report, hit_score, verdict, master_path}
    """
    if not attempts:
        return None
    # фильтр: у кого есть hit_score
    scored = [a for a in attempts if isinstance(a.get("hit_score"), (int, float))]
    if not scored:
        return attempts[0]
    return max(scored, key=lambda a: float(a["hit_score"]))


def should_evolve(
    hit_score: float | None,
    verdict: str | None,
    min_score: float = 68.0,
) -> bool:
    if hit_score is None:
        return True
    if verdict in ("chart_ready", "solid") and hit_score >= min_score:
        return False
    return hit_score < min_score
