# -*- coding: utf-8 -*-
"""modules.hit_factory._state — построение wizard_state (вынесено из generator для лимита 400 строк)."""
from __future__ import annotations

import random
from typing import Any

from modules.hit_factory.themes import pick_aggression, pick_bpm, pick_genre, pick_theme, trend_context


def build_wizard_state(
    adaptive_cfg: dict[str, Any],
    duration_sec_default: int,
    genre: str,
    theme: str,
    bpm_override: int | None,
    aggression: float | None,
    seed: int | None,
    duration_sec: int | None,
    rng: random.Random,
    adaptive: bool = True,
) -> dict[str, Any]:
    """Собирает wizard_state для run_full_pipeline."""
    g = genre or pick_genre(rng)
    t = theme or pick_theme(rng)
    if not theme:
        try:
            from modules.hit_factory.themes import enrich_theme_with_slang

            t = enrich_theme_with_slang(t, rng)
        except Exception as _exc:
            print(f"[hit_factory] ignored: {_exc}")
    bpm = pick_bpm(g, rng, bpm_override)
    agr = aggression if aggression is not None else pick_aggression(rng, g)
    if adaptive and adaptive_cfg.get("enhanced_dsp"):
        agr = max(agr, 0.75)
    s = int(seed if seed is not None else rng.randint(1, 1_000_000))
    dur = int(duration_sec or duration_sec_default or 120)

    try:
        tc = trend_context(t)
        hype_str = ", ".join((tc.get("hype_words") or [])[:6])
    except Exception:
        hype_str = ""

    beat_engine, engine_extras = _pick_beat_engine(adaptive, adaptive_cfg)
    # Голос: `pro` = свой микрофон/TTS+RVC; поле обязано попасть в рецепт, иначе
    # `build_recipe` подставит своё значение и решение потеряется.
    voice_mode = "pro"

    state: dict[str, Any] = {
        "genre": g,
        "theme": t,
        "preset": None,
        "bpm_override": bpm,
        "aggression": agr,
        "seed": s,
        "duration_sec": dur,
        "n_verses": 2,
        "voice_mode": voice_mode,
        "use_rvc": False,
        "use_vocal_fx": True,
        "export_stems": False,
        "bilingual": True,
        "quality_mode": "quality",
        "stands": ["streaming", "tiktok", "club"],
        "references": [],
        "trend_notes": hype_str,
        "artist": "ZS Producer",
        "adaptive_level": adaptive_cfg.get("level", 0) if adaptive else 0,
        "enhanced_dsp": bool(adaptive_cfg.get("enhanced_dsp", True)) if adaptive else True,
    }
    if beat_engine:
        state["beat_engine"] = beat_engine
        state.update(engine_extras)
    return state


def _pick_beat_engine(adaptive: bool, adaptive_cfg: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    """Какой движок бита выбрать: ACE-Step (сервер) → MusicGen → процедурный.

    MusicGen — настоящая нейросеть и на CPU (чанки 30 с), поэтому он идёт
    раньше процедурного пути. Если модель не загрузится, пайплайн честно
    покажет BLOCKED, а не подменит бит формулой.
    """
    if not adaptive:
        return None, {}
    if adaptive_cfg.get("use_acestep"):
        return "ace_step", {}
    if adaptive_cfg.get("use_musicgen"):
        return "musicgen", {
            "musicgen_model": adaptive_cfg.get("musicgen_model") or "facebook/musicgen-small",
            "musicgen_device": adaptive_cfg.get("musicgen_device") or "cpu",
        }
    return None, {}
