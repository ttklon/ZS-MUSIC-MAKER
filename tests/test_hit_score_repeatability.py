# -*- coding: utf-8 -*-
"""
Повторяемость мотива: доля, а не абсолютное число повторов.

Было:

    off = int(20 * sr / 1024)          # сдвиг ровно ~20 секунд
    repeats = (diag > 0.85).sum()
    score = min(100.0, repeats * 8.0 + 30.0)

Число повторов растёт с длиной трека: на 60-секундных мастерах движка их
96…280, и `min(100, …)` упирается в максимум у всех — замер дал **100,0 у
всех восьми жанров** независимо от того, возвращается мотив или нет.
Метрика с весом 1,3 (10 % итогового балла) стояла в максимуме всегда.

Теперь ищется лаг в диапазоне 4…30 секунд, на котором повторяемость
наибольшая, и берётся **доля** кадров, у которых через этот лаг есть похожий
кадр. Доля не зависит от длины. Замеры:

    один такт аккордов по кругу   1,00  → 100 баллов
    чирп без повторов             0,14  → 14
    живые биты движка             0,50…0,60 → 50…60
"""

from __future__ import annotations

import numpy as np

from modules.hit_scorer.hook_metrics import _hook_repeatability

SR = 22_050
SECONDS = 40


def _looping_motif() -> np.ndarray:
    """Один и тот же мотив из четырёх нот по кругу."""
    t = np.arange(SR * SECONDS) / SR
    notes = np.array([220.0, 220.0, 261.6, 293.7])
    freq = notes[(t * 2).astype(int) % 4]
    return 0.2 * np.sin(2 * np.pi * freq * t)


def _through_composed() -> np.ndarray:
    """Сплошной свип: ни одного повторяющегося места."""
    t = np.arange(SR * SECONDS) / SR
    freq = np.linspace(80.0, 2000.0, len(t))
    return 0.2 * np.sin(2 * np.pi * np.cumsum(freq) / SR)


def test_looping_motif_repeats_fully() -> None:
    score, share = _hook_repeatability(_looping_motif(), SR)

    assert share >= 0.8, share
    assert score >= 80.0, (score, share)


def test_through_composed_track_does_not_repeat() -> None:
    score, share = _hook_repeatability(_through_composed(), SR)

    assert share <= 0.3, share
    assert score <= 30.0, (score, share)


def test_share_does_not_depend_on_length() -> None:
    """Доля повторов у одного и того же материала не растёт с длиной."""
    short = _looping_motif()
    long = np.tile(short, 2)  # тот же материал, вдвое длиннее

    _, short_share = _hook_repeatability(short, SR)
    _, long_share = _hook_repeatability(long, SR)

    assert abs(long_share - short_share) <= 0.1, (long_share, short_share)


def test_short_clip_is_named_instead_of_scored_high() -> None:
    """На коротком фрагменте мотив не в чем повторять — балл не максимальный."""
    score, share = _hook_repeatability(_looping_motif()[: SR * 10], SR)

    assert 0.0 <= score <= 100.0
    assert score < 100.0, (score, share)
