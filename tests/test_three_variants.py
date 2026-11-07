"""T13: «три варианта» — это три аранжировки, а не три громкости.

Кнопка «3 варианта» подменяла `aggression` (0.4/0.6/0.8) и выставляла
`variant=1..3`. Само поле `variant` до аранжировки не доезжало, поэтому
варианты отличались только громкостью — то есть отсутствие вариантов
маскировалось изменением агрессии.
"""

from __future__ import annotations

import pytest

from app.core.recipe import arrangement_style, build_recipe, resolve_style_vector
from app.core.stages.prep import _stage_arrangement
from modules import arrangement_engine as ae


STYLE = {"target_bpm": 128, "target_mode": "minor", "key_root": "A", "genre": "drift_phonk", "seed": 7}


def _plan(variant: int) -> dict:
    result = _stage_arrangement(None, style=dict(STYLE), total_seconds=150, variant=variant)
    assert result["ok"] is True
    return result["plan"]


def test_variant_changes_the_plan() -> None:
    plans = [_plan(variant) for variant in (1, 2, 3)]

    assert len({plan["variant"] for plan in plans}) == 3
    energies = [
        [section["energy"] for section in plan["sections"]] for plan in plans
    ]
    assert energies[0] != energies[1] or energies[1] != energies[2], (
        "варианты отличаются только полем variant, но не содержанием"
    )


def test_variant_is_recorded_in_the_plan() -> None:
    assert _plan(3)["variant"] == 3


def test_recipe_variant_reaches_style_vector() -> None:
    recipe = build_recipe({"genre": "drift_phonk", "variant": 2, "seed": 7})

    style = resolve_style_vector(recipe, None)

    assert style["variant"] == 2
    assert arrangement_style(style)["genre_hint"] == "drift_phonk"


def test_variant_from_style_is_used_when_not_passed() -> None:
    """Вариант приходит из рецепта, а не только аргументом стадии."""
    result = _stage_arrangement(
        None, style={**STYLE, "variant": 2}, total_seconds=120, variant=0
    )

    assert result["plan"]["variant"] == 2


def test_aggression_is_not_used_as_variant_proxy() -> None:
    """Агрессия пользователя не переписывается ради «вариантов»."""
    for variant in (1, 2, 3):
        plan = _plan(variant)
        assert "aggression" not in plan or plan["aggression"] is None


@pytest.mark.parametrize("variant", [0, 1, 2])
def test_engine_is_deterministic_per_variant(variant: int) -> None:
    first = ae.build_arrangement(dict(STYLE), total_seconds=100, variant=variant)
    second = ae.build_arrangement(dict(STYLE), total_seconds=100, variant=variant)

    assert first["sections"] == second["sections"]
