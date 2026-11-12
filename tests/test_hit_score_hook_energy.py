# -*- coding: utf-8 -*-
"""
Контраст припева и куплета: шкала не должна упираться в потолок.

Было: `ratio = peak_4s / median_4s`, `score = min(100, (ratio - 1) * 200)`.
Припев громче куплета на 30–60 % по амплитуде — это +2,3…+4,1 дБ, то есть
ratio 1,3–1,6, а `(1,6 − 1) · 200` уже даёт 120 → потолок 100. Замер на
восьми мастерах движка: ratio 1,40…1,75, то есть **семь из восьми в
максимуме**, и разница между «припев на +3 дБ» и «на +5 дБ» не видна.

Вторая беда: медиана по всем окнам ничего не говорит о том, есть ли у трека
секции. Трек, у которого громкий кусок один и короткий, получает высокий
ratio, хотя припева как секции в нём нет.

Теперь считаются два измеримых числа: насколько самый громкий участок выше
медианы (в дБ) и насколько различаются громкая и тихая половины трека
(Q75/Q25 в дБ). Первое — «есть ли пик», второе — «есть ли секции».
"""

from __future__ import annotations

import numpy as np

from modules.hit_scorer.hook_metrics import _hook_energy

SR = 22_050
SECONDS = 60


def _beat_with_lift(lift_db: float, seconds: int = SECONDS) -> np.ndarray:
    """Ровный бит, у которого вторая половина громче на заданное число дБ."""
    t = np.arange(SR * seconds) / SR
    rng = np.random.RandomState(9)
    base = 0.2 * np.sin(2 * np.pi * 55 * t) + 0.1 * np.sin(2 * np.pi * 220 * t)
    base += 0.02 * rng.randn(len(t)) * (np.sin(2 * np.pi * 4 * t) > 0)
    gain = np.ones_like(base)
    gain[t >= seconds / 2] = 10.0 ** (lift_db / 20.0)
    return base * gain


def test_flat_track_has_no_chorus() -> None:
    score, raw = _hook_energy(_beat_with_lift(0.0), SR)

    assert score <= 35.0, (score, raw)


def test_score_grows_with_the_lift() -> None:
    """Каждые следующие 3 дБ контраста — выше балл, без упора в 100."""
    scores = [_hook_energy(_beat_with_lift(d), SR)[0] for d in (0.0, 3.0, 6.0, 9.0)]

    assert scores == sorted(scores), scores
    assert scores[0] < scores[1] < scores[2] <= scores[3], scores
    assert scores[-1] <= 100.0


def test_scale_is_not_saturated_at_engine_values() -> None:
    """Живые биты движка дают +2,9…+4,9 дБ — это не потолок шкалы."""
    scores = [_hook_energy(_beat_with_lift(d), SR)[0] for d in (3.0, 4.0, 5.0)]

    assert len(set(round(s, 3) for s in scores)) == 3, scores
    assert max(scores) < 100.0, scores


def test_loud_span_is_not_a_chorus() -> None:
    """Один короткий громкий кусок — это не припев, секций в треке нет."""
    y = _beat_with_lift(0.0)
    start = int(SR * 20)
    y[start : start + int(SR * 4)] *= 6.0

    score_span, _ = _hook_energy(y, SR)
    score_sections, _ = _hook_energy(_beat_with_lift(3.0), SR)

    assert score_sections > score_span, (score_sections, score_span)
