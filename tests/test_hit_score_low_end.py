# -*- coding: utf-8 -*-
"""
Метрика низа должна различать хороший саб и утопленный.

Замер на настоящем мастере движка (phonk, 20 с, стенд streaming). Значение
`low_end_power` при этом не менялось вообще:

    как есть            ratio 6,60   70,0
    низ +12 дБ          ratio 20,45  70,0
    низ +24 дБ          ratio 18,33  70,0
    только саб          ratio 1826   70,0   ← 1826, и всё равно 70
    без низа < 60 Гц    ratio 1,43   70,0
    без низа < 120 Гц   ratio 0,05   45,0   ← единственный случай, который ловился

Шкала была вырождена: любое отношение низа к середине больше 1,3 получало
ровно 70,0. А у живых битов это отношение 6,6–7,5 у шести жанров подряд, то
есть ветка `ratio > 1.3` — не исключение, а обычный путь. «Утопил саб в
ноль» и «выкрутил саб на +24 дБ» оценка считала одним и тем же.

Новая шкала смотрит не на сырое отношение (линейный STFT и разная ширина
полос делают его произвольным), а на долю низа в общей энергии и на середину
диапазона, где у хитов dance/trap и лежит 808.
"""

from __future__ import annotations

import numpy as np

from modules.hit_scorer.mix_metrics import _low_end_power

SR = 22_050
SECONDS = 20


def _mix(bass_gain: float, mid_gain: float = 1.0) -> np.ndarray:
    """Живой микс: саб 40–70 Гц, середина 220–1500 Гц, немного шума сверху."""
    rng = np.random.RandomState(11)
    t = np.arange(SR * SECONDS) / SR
    bass = bass_gain * (
        0.5 * np.sin(2 * np.pi * 45 * t) + 0.4 * np.sin(2 * np.pi * 62 * t)
    )
    mid = mid_gain * (
        0.12 * np.sin(2 * np.pi * 220 * t)
        + 0.1 * np.sin(2 * np.pi * 440 * t)
        + 0.08 * np.sin(2 * np.pi * 1500 * t)
    )
    # Хэты — ударами, а не ровным шумом: ровный шум кладёт половину энергии
    # ниже 120 Гц и делает микс «басовым» сам по себе.
    hats = 0.06 * rng.randn(len(t)) * (np.sin(2 * np.pi * 8 * t) > 0)
    return bass + mid + hats


def test_healthy_low_end_is_not_punished() -> None:
    """Нормальный саб должен получать хорошую оценку, а не 70 из жалости."""
    score, raw = _low_end_power(_mix(0.15), SR)

    assert 0.10 <= raw <= 0.70, raw
    assert score >= 82.0, (score, raw)


def test_drowned_sub_and_boosted_sub_score_differently() -> None:
    """Утопленный саб и выкрученный на +12 дБ — разные оценки."""
    drowned, drowned_raw = _low_end_power(_mix(0.03), SR)
    boosted, boosted_raw = _low_end_power(_mix(3.0), SR)

    assert boosted_raw > drowned_raw * 3, (boosted_raw, drowned_raw)
    assert drowned < 60.0, (drowned, drowned_raw)
    assert boosted < 60.0, (boosted, boosted_raw)
    assert abs(boosted - drowned) > 6.0, (boosted, drowned)


def test_mid_only_mix_has_no_low_end() -> None:
    """Микс без саба вообще не должен получать баллы за низ."""
    score, raw = _low_end_power(_mix(0.0), SR)

    assert raw < 0.04, raw
    assert score < 35.0, (score, raw)


def test_flat_top_of_scale_is_gone() -> None:
    """Раньше всё от 1,3 до бесконечности давало ровно 70,0 — проверяем, что нет."""
    scores = [
        _low_end_power(_mix(gain), SR)[0] for gain in (0.0, 0.03, 0.15, 0.5, 3.0)
    ]

    assert len(set(round(s, 3) for s in scores)) >= 3, scores
    assert max(scores) - min(scores) > 40.0, scores
