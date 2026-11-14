# -*- coding: utf-8 -*-
"""
modules.hit_factory.themes — выбор темы / жанра / BPM.

Использует trend_scout (live + offline fallback 2026) и локальный THEME_POOL.
Полностью бесплатно: без сети — работает offline-ветка.
"""
from __future__ import annotations

import random
import time
from typing import Any

from modules.hit_factory.config import BPM_MAP, HIT_GENRE_WEIGHTS, THEME_POOL


def _weighted_choice(weights: dict[str, float], rng: random.Random) -> str:
    items = list(weights.items())
    total = sum(w for _, w in items)
    r = rng.random() * total
    acc = 0.0
    for k, w in items:
        acc += w
        if r <= acc:
            return k
    return items[-1][0]


def pick_genre(rng: random.Random | None = None, genre_pool: dict[str, float] | None = None) -> str:
    rng = rng or random
    pool = genre_pool or HIT_GENRE_WEIGHTS
    # фильтруем только существующие пресеты: если жанра нет в data/genre_presets — пропускаем
    # но для factory считаем, что все из weights валидны (beat fallback сработает)
    return _weighted_choice(pool, rng)


def pick_theme(
    rng: random.Random | None = None,
    base_theme: str | None = None,
    use_trends: bool = True,
) -> str:
    rng = rng or random
    if base_theme and base_theme.strip():
        return base_theme.strip()

    # 1) пробуем trend_scout (live+offline), но не падаем если сети нет
    if use_trends:
        try:
            from agents.trend_scout import scout

            scout_data = scout(theme=rng.choice(THEME_POOL), offline_only=False)
            pool = []
            pool.extend(scout_data.get("themes", [])[:3])
            pool.extend(scout_data.get("punchlines", [])[:2])
            pool.extend(scout_data.get("hooks_en", [])[:1])
            if pool:
                # смешаем тренд с пулом
                base = rng.choice(pool)
                addon = rng.choice(THEME_POOL)
                # 50% вернуть тренд как есть, 50% — гибрид
                if rng.random() < 0.5:
                    return str(base).strip()
                return f"{base}, {addon}".strip()
        except Exception:
            pass
        # fallback ветка trend_scout без сети — пробуем offline_only
        try:
            from agents.trend_scout import scout as scout_offline

            data = scout_offline(theme="лето", offline_only=True)
            if data.get("themes"):
                return rng.choice(data["themes"])
        except Exception:
            pass

    # 2) чистый offline
    return rng.choice(THEME_POOL)


def pick_bpm(
    genre: str,
    rng: random.Random | None = None,
    base_bpm: int | None = None,
) -> int:
    rng = rng or random
    if base_bpm is not None:
        return int(base_bpm)
    info = BPM_MAP.get(genre) or BPM_MAP.get("default")
    lo, hi = info["range"]
    # иногда берём alt trap range (half-time feel)
    if info.get("alt") and rng.random() < 0.2:
        lo2, hi2 = info["alt"]
        return rng.randint(lo2, hi2)
    return rng.randint(lo, hi)


def pick_aggression(rng: random.Random | None = None, genre: str | None = None) -> float:
    rng = rng or random
    # phonk/rage/drift — выше агрессия, lofi/house — ниже
    if genre in ("drift_phonk", "phonk", "memphis_phonk", "rage", "drill", "uk_drill"):
        return round(rng.uniform(0.65, 0.92), 2)
    if genre in ("lofi", "witch_house", "cinematic"):
        return round(rng.uniform(0.3, 0.55), 2)
    if genre in ("house", "deep_house", "tech_house", "afro_house"):
        return round(rng.uniform(0.55, 0.78), 2)
    return round(rng.uniform(0.5, 0.85), 2)


def pick_duration(rng: random.Random | None = None, preset: str | None = None) -> int:
    rng = rng or random
    if preset == "tiktok":
        return 65
    if preset == "short":
        return 90
    if preset == "full":
        return 120
    # рандом взвешенно: 60% full, 25% short, 15% tiktok
    r = rng.random()
    if r < 0.6:
        return 120
    if r < 0.85:
        return 90
    return 65


def enrich_theme_with_slang(theme: str, rng: random.Random | None = None) -> str:
    """Подмешивает 1-2 сленговых слова в тему для вирусности (бесплатно)."""
    rng = rng or random
    try:
        from agents.trend_scout import FALLBACK_2026

        hype = FALLBACK_2026.get("hype_words", [])
        if hype and rng.random() < 0.55:
            extra = rng.choice(hype)
            if extra not in theme:
                return f"{theme}, {extra}"
    except Exception:
        pass
    return theme


def build_random_recipe_overrides(
    rng: random.Random | None = None,
    genre: str | None = None,
    theme: str | None = None,
    seed: int | None = None,
    duration_preset: str | None = None,
) -> dict[str, Any]:
    """Собирает случайные overrides для build_recipe (genre/theme/bpm/aggression/seed/duration)."""
    rng = rng or random
    g = genre or pick_genre(rng)
    t = theme or pick_theme(rng)
    t = enrich_theme_with_slang(t, rng)
    bpm = pick_bpm(g, rng)
    agr = pick_aggression(rng, g)
    dur = pick_duration(rng, duration_preset)
    s = int(seed if seed is not None else rng.randint(1, 1_000_000))
    return {
        "genre": g,
        "theme": t,
        "bpm_override": bpm,
        "aggression": agr,
        "duration_sec": dur,
        "seed": s,
        "n_verses": rng.choice([2, 2, 3]),
    }


def trend_context(theme: str) -> dict:
    """Возвращает контекст трендов для логирования/промпта (offline-safe)."""
    try:
        from agents.trend_scout import scout

        data = scout(theme or "лето", offline_only=True)
        return {
            "hype_words": data.get("hype_words", [])[:6],
            "punchlines": data.get("punchlines", [])[:3],
            "hooks_en": data.get("hooks_en", [])[:2],
            "source": "trend_scout_offline",
        }
    except Exception:
        return {"hype_words": [], "punchlines": [], "hooks_en": [], "source": "fallback_pool"}
