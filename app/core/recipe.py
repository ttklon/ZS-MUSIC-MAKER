# -*- coding: utf-8 -*-
"""
app/core/recipe.py — рецепт трека из состояния визарда.

Единственное место, где входные данные пользователя (пресет, BPM, жанр,
агрессия, число куплетов, вокальный режим, стенды, свои строки) превращаются
в нормализованный рецепт пайплайна. Раньше это было размазано по первой сотне
строк `run_full_pipeline`, и любое новое поле визарда молча терялось.
"""

from __future__ import annotations

from typing import Any

QUALITY_PROFILES: dict[str, dict[str, int]] = {
    "fast": {"rvc_epochs": 20, "mastering_iterations": 1},
    "quality": {"rvc_epochs": 100, "mastering_iterations": 3},
    "max": {"rvc_epochs": 300, "mastering_iterations": 5},
}

VOICE_MODES = ("pro", "lazy", "off")


def _as_int(value: Any, default: int | None = None) -> int | None:
    try:
        return int(value) if value not in (None, "") else default
    except (TypeError, ValueError):
        return default


def _as_float(value: Any, default: float | None = None) -> float | None:
    try:
        return float(value) if value not in (None, "") else default
    except (TypeError, ValueError):
        return default


def _preset_style_vector(preset_key: str | None) -> dict[str, Any]:
    """Стилевой вектор пресета; пустой dict, если пресета нет или он битый."""
    if not preset_key:
        return {}
    try:
        from modules import presets

        preset = presets.get_preset(preset_key)
        if isinstance(preset, dict) and "error" not in preset:
            return presets.preset_to_style_vector(preset_key) or {}
    except Exception:  # noqa: BLE001 - пресет не критичен для запуска
        return {}
    return {}


def build_recipe(wizard_state: dict[str, Any] | None) -> dict[str, Any]:
    """Нормализовать состояние визарда в рецепт пайплайна.

    Своя запись с микрофона (`own_vocal_wav`) — основной вокальный путь,
    поэтому передаётся как есть; TTS/RVC работают только как fallback.

    Все поля проверяются и приводятся к допустимым значениям: неизвестный
    `voice_mode` становится `pro`, `n_verses` зажимается в 1..4, стенды —
    всегда список. Свободный промпт пользователя подмешивается в тему.
    """
    state = dict(wizard_state or {})
    preset_key = state.get("preset")
    preset_sv = _preset_style_vector(preset_key)

    theme = str(state.get("theme") or "лето, тачки, движ")
    extra_prompt = str(state.get("user_extra_prompt") or "").strip()
    if extra_prompt and extra_prompt not in theme:
        theme = f"{theme}; {extra_prompt}"

    voice_mode = str(state.get("voice_mode") or "pro").strip().lower()
    if voice_mode not in VOICE_MODES:
        voice_mode = "pro"

    stands = state.get("stands") or []
    if isinstance(stands, str):
        stands = [stands]
    elif isinstance(stands, (list, tuple, set)):
        stands = [str(stand) for stand in stands if stand]
    else:
        stands = []

    quality_mode = str(state.get("quality_mode") or "quality").strip().lower()
    if quality_mode not in QUALITY_PROFILES:
        quality_mode = "quality"

    aggression = _as_float(state.get("aggression"))
    if aggression is not None:
        aggression = max(0.0, min(1.0, aggression))

    n_verses = _as_int(state.get("n_verses"), 2) or 2
    user_lines = [str(line) for line in (state.get("user_lyrics_lines") or []) if str(line).strip()]

    return {
        "project_id": state.get("project_id"),
        "refs": [str(r) for r in (state.get("references") or [])],
        "theme": theme,
        "genre": state.get("genre") or preset_key or "drift_phonk",
        "artist": state.get("artist") or state.get("artist_name") or "ZS Producer",
        "preset": preset_key,
        "preset_style_vector": preset_sv,
        "bpm_override": _as_int(state.get("bpm_override")),
        "aggression": aggression,
        "duration_sec": _as_int(state.get("duration_sec")),
        "user_lyrics_lines": user_lines,
        "voice_mode": voice_mode,
        "stands": stands,
        "n_verses": max(1, min(4, n_verses)),
        "quality_mode": quality_mode,
        "quality_profile": dict(QUALITY_PROFILES[quality_mode]),
        "extra_prompt": extra_prompt,
        "seed": _as_int(state.get("seed")),
        "own_vocal_wav": state.get("own_vocal_wav") or state.get("vocal_wav"),
    }


def resolve_style_vector(recipe: dict[str, Any], analysis: Any) -> dict[str, Any]:
    """Собрать стилевой вектор стадии бита: пресет → анализ → ручной BPM.

    Приоритет явный: пользовательский BPM перекрывает анализ, анализ
    перекрывает пресет, пресет — дефолт.
    """
    style: dict[str, Any] = {"target_bpm": 128, "target_mode": "minor"}
    preset_sv = recipe.get("preset_style_vector") or {}
    if isinstance(preset_sv, dict):
        if preset_sv.get("target_bpm"):
            style["target_bpm"] = int(preset_sv["target_bpm"])
        if preset_sv.get("target_mode"):
            style["target_mode"] = preset_sv["target_mode"]
        if preset_sv.get("prompt_hint"):
            style["prompt_hint"] = preset_sv["prompt_hint"]
    if isinstance(analysis, dict):
        if analysis.get("bpm"):
            style["target_bpm"] = int(analysis["bpm"])
        if analysis.get("mode"):
            style["target_mode"] = analysis["mode"]
    if recipe.get("bpm_override"):
        style["target_bpm"] = int(recipe["bpm_override"])
        if isinstance(analysis, dict):
            analysis["bpm"] = recipe["bpm_override"]
    return style


def build_arrangement_plan(recipe: dict[str, Any], plan: Any, analysis: Any) -> dict[str, Any]:
    """Дополнить план аранжировки параметрами пользователя (длительность, агрессия, куплеты)."""
    result = dict(plan) if isinstance(plan, dict) else {}
    if recipe.get("duration_sec"):
        result["duration_sec"] = recipe["duration_sec"]
    aggression = recipe.get("aggression")
    if aggression is not None:
        result["aggression"] = aggression
    elif isinstance(analysis, dict) and analysis.get("aggression") is not None:
        result.setdefault("aggression", float(analysis.get("aggression", 0.7)))
    result["n_verses"] = recipe.get("n_verses", 2)
    return result
