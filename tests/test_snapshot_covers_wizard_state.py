"""Переоткрытие проекта: любое поле `wizard_state` обязано попадать в снапшот.

Регрессия из 42.0.11: `_state.build_wizard_state` клал в состояние
`adaptive_level` и `enhanced_dsp`, а `RECIPE_KEYS` их не знал. Из-за этого
`snapshot_recipe` бросал ValueError, в `report.json` появлялись
предупреждения «project recipe not saved; reopening unavailable», и проект
нельзя было открыть повторно — при том что именно эти два поля меняют
готовый мастер (`adaptive.py` → `_runner._enhance_master`).

Тест перебирает ветки `_pick_beat_engine` (MusicGen добавляет ещё два поля),
а не только текущую среду: на машине без `torch`/MusicGen ветка не
исполняется, и дыра осталась бы незамеченной до первого пользователя с GPU.
"""

from __future__ import annotations

import random

import pytest

from app.core.project_snapshot import RECIPE_KEYS, restore_recipe, snapshot_recipe
from modules.hit_factory._state import build_wizard_state

_ADAPTIVE_CONFIGS = [
    # процедурный путь — то, что видит этот песочный ящик
    {"level": 0, "enhanced_dsp": True},
    # ACE-Step: серверный движок бита
    {"level": 1, "enhanced_dsp": True, "use_acestep": True},
    # MusicGen: единственная ветка, добавляющая поля в само состояние
    {
        "level": 2,
        "enhanced_dsp": True,
        "use_musicgen": True,
        "musicgen_model": "facebook/musicgen-small",
        "musicgen_device": "cpu",
    },
    # ultra_light: enhanced_dsp выключен — значение обязано сохраниться как False
    {"level": 0, "enhanced_dsp": False},
]


@pytest.mark.parametrize("adaptive_cfg", _ADAPTIVE_CONFIGS)
@pytest.mark.parametrize("adaptive", [True, False])
def test_wizard_state_is_always_snapshotable(adaptive_cfg: dict, adaptive: bool) -> None:
    state = build_wizard_state(
        adaptive_cfg=adaptive_cfg,
        duration_sec_default=20,
        genre="trap",
        theme="город спит",
        bpm_override=None,
        aggression=None,
        seed=777,
        duration_sec=20,
        rng=random.Random(1),
        adaptive=adaptive,
    )
    unknown = sorted(set(state) - RECIPE_KEYS)
    assert not unknown, f"поля wizard_state отсутствуют в RECIPE_KEYS: {unknown}"

    snapshot = snapshot_recipe(state)
    assert restore_recipe({"desktop_recipe_snapshot": snapshot}) == state


def test_adaptive_dsp_choices_survive_reopening() -> None:
    """Решение о DSP не должно подменяться умолчанием при переоткрытии."""
    state = build_wizard_state(
        adaptive_cfg={"level": 0, "enhanced_dsp": False},
        duration_sec_default=20,
        genre="trap",
        theme="x",
        bpm_override=None,
        aggression=None,
        seed=1,
        duration_sec=20,
        rng=random.Random(1),
    )
    restored = restore_recipe({"desktop_recipe_snapshot": snapshot_recipe(state)})
    assert restored["enhanced_dsp"] is False
    assert restored["adaptive_level"] == 0
