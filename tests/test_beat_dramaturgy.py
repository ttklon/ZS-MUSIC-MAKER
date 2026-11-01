# -*- coding: utf-8 -*-
"""
Гейты драматургии (Этап 4.3): длина 2:30–3:30, хук в первые 15 секунд,
контраст дропа и потолок плотности.

Задача этих тестов — не дать вернуться к «лупу на три минуты»: структура
обязана быть осмысленной, а куплет не должен звучать так же плотно, как припев.
"""

from __future__ import annotations

import random

import numpy as np

from modules.beat.dramaturgy import (
    HOOK_WITHIN_SEC,
    TARGET_MAX_SEC,
    TARGET_MIN_SEC,
    hook_position,
    hook_within_limit,
    layers_for_section,
    plan_sections,
    structure_report,
    total_seconds,
)
from modules.beat_constructor import BeatConstructor


def test_plan_fills_the_target_length_without_stretching_the_hook() -> None:
    plans = plan_sections(bpm=128, duration_sec=180)

    assert TARGET_MIN_SEC <= total_seconds(plans, 128) <= TARGET_MAX_SEC
    assert [plan.name for plan in plans][0] == "intro"
    assert [plan.name for plan in plans][-1] == "outro"
    assert sum(1 for plan in plans if plan.name == "hook") >= 2
    assert all(plan.bars >= 2 for plan in plans)


def test_short_request_is_still_a_song_not_a_loupe() -> None:
    plans = plan_sections(bpm=130, duration_sec=15, include_intro=False, include_outro=False)
    bar_sec = 240.0 / 130

    # Секция короче двух тактов не читается, поэтому короткий заказ может
    # выйти на пару тактов длиннее; итоговый файл всё равно обрезается ровно.
    assert total_seconds(plans, 130) <= 15.0 + 4 * bar_sec
    assert all(plan.bars >= 2 for plan in plans)
    assert any(plan.name == "hook" for plan in plans)


def test_hook_motif_is_audible_within_fifteen_seconds() -> None:
    plans = plan_sections(bpm=128, duration_sec=180)

    assert hook_within_limit(plans, 128) is True
    assert HOOK_WITHIN_SEC == 15.0
    assert hook_position(plans, 128) > 15.0, "припев позже, но мотив уже звучит"


def test_drop_contrast_and_layer_cap() -> None:
    report = structure_report(plan_sections(bpm=128, duration_sec=180), 128)

    assert report["drop_contrast"] >= 0.3, "хук обязан быть заметно плотнее куплета"
    assert report["max_layers"] <= 7
    verse = next(section for section in report["sections"] if section["name"] == "verse")
    hook = next(section for section in report["sections"] if section["name"] == "hook")
    assert hook["gain_db"] - verse["gain_db"] >= 4.0, "разница хук/куплет ≥4 дБ"


def test_layers_do_not_turn_sections_into_mush() -> None:
    intro = layers_for_section("intro", 0.42)
    verse = layers_for_section("verse", 0.62)
    hook = layers_for_section("hook", 1.0)

    assert "hook_lead" in intro, "мотив обязан звучать с первых тактов"
    assert "hook_lead" not in verse, "в куплете мотив хука молчит"
    assert len(verse) < len(hook)
    assert "hook_lead" in hook and "fx" in hook


def test_rendered_track_reports_dramaturgy_and_keeps_duration() -> None:
    np.random.seed(21)
    random.seed(21)
    constructor = BeatConstructor(bpm=128, genre="drift phonk", groove={"hihat_density": 0.4}, seed=21)

    result = constructor.build_track(duration_sec=180, out_name="dramaturgy_gate.wav")
    report = result["dramaturgy"]

    assert report["hook_within_15s"] is True
    assert report["hook_motif_start_sec"] <= 15.0
    assert 145.0 <= result["duration_sec"] <= 215.0
    assert [section["name"] for section in result["sections"]][0] == "intro"
