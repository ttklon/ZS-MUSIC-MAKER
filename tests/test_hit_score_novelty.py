# -*- coding: utf-8 -*-
"""
Новизна: «неформульность» должна быть измеримой, а не всегда максимальной.

Было:

    combined_var = (col_var + row_var * 0.1) / 1.1
    score = min(100.0, combined_var * 8e5 + 40.0)

На настоящем сигнале дисперсия спектра — величина порядка 10 (у мастеров
движка сырое значение 13,6…15,2), поэтому `var * 8e5` уходит в миллионы и
`min(100, ...)` всегда даёт **100,0**. Замер: 100,0 у всех восьми мастеров
разных жанров, 100,0 у чистого синуса 440 Гц и 100,0 у «одного клика в
тишине» (это ловилось только сторожем тишины, отдельно).

То есть метрика с весом 0,8 (6 % итогового балла) стояла в максимуме всегда.
Сработать она могла только на сигнале тише −40 dBFS — то есть никогда на
музыке.

Теперь новизна — это спектральное разнообразие в человеческих единицах:
сколько разных «красок» (спектральных профилей) реально встречается в треке,
а не дисперсия абсолютных амплитуд STFT.
"""

from __future__ import annotations

import numpy as np

from modules.hit_scorer.mix_metrics import _novelty

SR = 22_050
SECONDS = 20


def _tone(freq: float, seconds: int = SECONDS) -> np.ndarray:
    t = np.arange(SR * seconds) / SR
    return 0.3 * np.sin(2 * np.pi * freq * t)


def _varying_mix() -> np.ndarray:
    """Микс, который меняется: фильтр-свип, смена аккордов, удары."""
    rng = np.random.RandomState(41)
    t = np.arange(SR * SECONDS) / SR
    sweep = 220.0 + 180.0 * np.sin(2 * np.pi * 0.07 * t)
    sig = 0.2 * np.sin(2 * np.pi * np.cumsum(sweep) / SR)
    chords = np.zeros_like(t)
    for i, freq in enumerate((110.0, 165.0, 196.0, 247.0)):
        mask = ((t >= i * SECONDS / 4) & (t < (i + 1) * SECONDS / 4)).astype(float)
        chords += mask * 0.15 * np.sin(2 * np.pi * freq * t)
    hits = 0.25 * rng.randn(len(t)) * (np.sin(2 * np.pi * 3 * t) > 0.9)
    return sig + chords + hits


def test_pure_tone_is_not_novel() -> None:
    """Один синус не может быть «на 100 из 100 уникальным»."""
    score, raw = _novelty(_tone(440.0), SR)

    assert score <= 45.0, (score, raw)


def test_varying_mix_beats_pure_tone() -> None:
    tone, tone_raw = _novelty(_tone(220.0), SR)
    mix, mix_raw = _novelty(_varying_mix(), SR)

    assert mix > tone, (mix, tone)
    assert mix - tone >= 20.0, (mix, tone)
    assert mix_raw != tone_raw


def test_repetitive_loop_is_less_novel_than_changing_track() -> None:
    """Один и тот же такт по кругу — это формула, и метрика должна это видеть."""
    rng = np.random.RandomState(43)
    bar = 0.2 * np.sin(2 * np.pi * 110 * np.arange(SR) / SR)
    loop = np.tile(bar, SECONDS)
    assert len(loop) == SR * SECONDS

    loop_score, _ = _novelty(loop, SR)
    mix_score, _ = _novelty(_varying_mix(), SR)

    assert mix_score > loop_score, (mix_score, loop_score)


def test_score_stays_inside_scale() -> None:
    for sig in (_tone(55.0), _tone(8800.0), _varying_mix(), _tone(220.0) * 0.01):
        score, _ = _novelty(sig, SR)
        assert 0.0 <= score <= 100.0, score
