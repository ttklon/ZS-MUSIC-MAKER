# -*- coding: utf-8 -*-
"""
modules.hit_factory.evolver — эволюционная петля hit_score.

mutate() — сдвигает BPM, aggression и seed, сохраняя заданную длительность
select_best() — выбирает лучшего по hit_score среди попыток.
"""
from __future__ import annotations

import random

from modules.hit_factory.readiness import attempt_rank, usable_score
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

    # Duration is a render budget/user constraint, not a quality mutation.
    # In particular a short requested clip must never turn into 120 seconds.

    # если слабые метрики указывают на low_end или стерео — чуть подвигаем aggression/жанр не трогаем
    # жанр оставляем тем же, чтобы не ломать expectation; смену жанра делает верхнеуровневый batch

    return nxt


def select_best(attempts: list[dict[str, Any]]) -> dict[str, Any] | None:
    """
    Выбирает завершённый рендер прежде неполного, затем по hit_score.
    Каждый attempt: {recipe, report, hit_score, verdict, master_path}
    """
    if not attempts:
        return None
    return max(attempts, key=attempt_rank)


def should_evolve(
    hit_score: float | None,
    verdict: str | None,
    min_score: float = 68.0,
) -> bool:
    if not usable_score(hit_score):
        return True
    return verdict not in ("chart_ready", "solid") or hit_score < min_score
