"""T5: стадия аранжировки делает настоящий план, а не пустую заглушку.

До доработки `_stage_arrangement` отдавала `{"ok": True, "plan": {"sections": []}}`:
статус OK, отчёт зелёный, движок `modules/arrangement_engine.py` (341 строка,
жанровые шаблоны, drum-паттерны, TikTok-хук) не вызывался никогда.

Проверяется контракт стадии: непустые секции, согласованная длительность,
воспроизводимость по seed и честный BLOCKED вместо фальшивого OK.
"""

from __future__ import annotations

import pytest

from app.core.recipe import arrangement_style, build_arrangement_plan, resolve_style_vector
from app.core.stages.prep import _stage_arrangement
from app.pipeline import StageStatus, classify
from modules import arrangement_engine as ae


STYLE = {"target_bpm": 140, "target_mode": "minor", "key_root": "F", "genre": "drift_phonk", "seed": 42}


# ------------------------------------------------------------------ адаптер
def test_arrangement_style_translates_recipe_vocabulary() -> None:
    style = arrangement_style(STYLE)

    assert style["bpm"] == 140
    assert style["key"] == "F"
    assert style["mode"] == "minor"
    assert style["genre_hint"] == "drift_phonk"
    assert style["seed"] == 42


def test_arrangement_style_is_tolerant_to_missing_fields() -> None:
    style = arrangement_style({})

    assert style["bpm"] == 128
    assert style["mode"] == "minor"
    # seed не выдумывается: детерминизм должен быть явным
    assert "seed" not in style or style["seed"] is None


def test_resolved_style_vector_reaches_arrangement_style() -> None:
    recipe = {"genre": "phonk", "preset": None, "seed": 7}
    resolved = resolve_style_vector(recipe, {"bpm": 132, "mode": "minor", "key_root": "A"})

    style = arrangement_style(resolved)

    assert style["bpm"] == 132
    assert style["key"] == "A"
    assert style["seed"] == 7


# ------------------------------------------------------------------ движок
def test_engine_seed_is_reproducible_and_seconds_add_up() -> None:
    first = ae.build_arrangement({"bpm": 140, "genre_hint": "phonk / drift"}, total_seconds=150, seed=42)
    second = ae.build_arrangement({"bpm": 140, "genre_hint": "phonk / drift"}, total_seconds=150, seed=42)

    assert first["sections"] == second["sections"]
    assert len(first["sections"]) >= 6
    total = sum(section["duration_sec"] for section in first["sections"])
    assert abs(total - first["total_sec"]) < 0.01


def test_engine_without_seed_is_still_reproducible() -> None:
    """Неявный `time.time()` делал план невоспроизводимым между прогонами."""
    first = ae.build_arrangement({"bpm": 140}, total_seconds=120)
    second = ae.build_arrangement({"bpm": 140}, total_seconds=120)

    assert first["sections"] == second["sections"]
    assert first["seeded"] is False


def test_tiktok_hook_window_is_bounded() -> None:
    plan = ae.build_arrangement({"bpm": 140}, total_seconds=150, seed=42)

    hook = plan["tiktok_hook"]
    assert 0 <= hook["start_sec"] <= plan["total_sec"]
    assert hook["end_sec"] - hook["start_sec"] <= 25.0001


# ------------------------------------------------------------------ стадия
def test_stage_returns_a_real_plan() -> None:
    result = _stage_arrangement(
        {"bpm": 132, "mode": "minor", "key_root": "A"},
        style=STYLE,
        total_seconds=150,
        variant=0,
    )

    assert result["ok"] is True
    plan = result["plan"]
    assert len(plan["sections"]) >= 6
    assert plan["bpm"] == 140
    assert plan["key"] == "F"
    assert plan["total_sec"] > 0
    assert "tiktok_hook" in plan


def test_stage_is_reproducible_for_same_seed() -> None:
    args = ({"bpm": 132}, STYLE, 150, 0)

    first = _stage_arrangement(args[0], style=args[1], total_seconds=args[2], variant=args[3])
    second = _stage_arrangement(args[0], style=args[1], total_seconds=args[2], variant=args[3])

    assert first["plan"]["sections"] == second["plan"]["sections"]


def test_stage_reports_failure_instead_of_fake_success(monkeypatch) -> None:
    """Сбой движка — это FAILED с причиной, а не OK с пустым планом."""

    def boom(*args, **kwargs):
        raise RuntimeError("engine exploded")

    monkeypatch.setattr(ae, "build_arrangement", boom)

    result = _stage_arrangement({"bpm": 132}, style=STYLE, total_seconds=150, variant=0)

    assert result["ok"] is False
    assert "engine exploded" in result["reason"]
    assert classify(result, name="_stage_arrangement").status is StageStatus.FAILED


def test_empty_plan_from_engine_is_blocked_not_ok(monkeypatch) -> None:
    monkeypatch.setattr(ae, "build_arrangement", lambda *a, **k: {"sections": []})

    result = _stage_arrangement({"bpm": 132}, style=STYLE, total_seconds=150, variant=0)

    assert result["blocked"] is True
    assert "empty section list" in result["reason"]
    assert classify(result, name="_stage_arrangement").status is StageStatus.BLOCKED


# ------------------------------------------------------------------ рецепт
def test_build_arrangement_plan_keeps_sections_and_user_fields() -> None:
    plan = ae.build_arrangement(STYLE, total_seconds=150, seed=42)
    recipe = {"duration_sec": 120, "aggression": 0.8, "n_verses": 3}

    merged = build_arrangement_plan(recipe, plan, None)

    assert merged["duration_sec"] == 120
    assert merged["aggression"] == 0.8
    assert merged["n_verses"] == 3
    assert merged["sections"] == plan["sections"]
    assert merged["tiktok_hook"] == plan["tiktok_hook"]


@pytest.mark.parametrize("genre", ["drift_phonk", "phonk", "phonk / drift", "hardstyle"])
def test_stage_handles_user_genre_names(genre: str) -> None:
    result = _stage_arrangement(
        {"bpm": 132}, style={**STYLE, "genre_hint": genre}, total_seconds=150, variant=0
    )

    assert result["ok"] is True
    assert result["plan"]["sections"]
