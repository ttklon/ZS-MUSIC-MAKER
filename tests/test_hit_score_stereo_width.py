# -*- coding: utf-8 -*-
"""
Ширина стерео: шкала должна различать «широко» и «слишком широко».

Старая шкала:

    corr < 0.55            → 70.0   «слишком широко»
    0.55 … 0.85            → 90.0   норма
    0.85 … 0.95            → 65.0
    corr ≥ 0.95            → 40.0   почти моно

Всё, что шире 0,55 корреляции, получало одну и ту же 70,0 — от «широко, но
живо» до «каналы в противофазе». Замер на восьми мастерах движка: у всех
corr 0.852…0.874, то есть все попали в один узкий коридор и получили 65,0 —
метрика не различала ничего. Это та же болезнь, что у низа, только с
обратной стороны: наказывается и слишком узкая, и слишком широкая картинка,
а промежуточных оценок нет.
"""

from __future__ import annotations

import numpy as np
import soundfile as sf

from modules.hit_scorer.mix_metrics import _stereo_width

SR = 44_100
SECONDS = 5


def _stereo_with_correlation(path, corr: float) -> str:
    """Стерео-файл с заданной корреляцией каналов (шум + общая часть)."""
    rng = np.random.RandomState(19)
    n = SR * SECONDS
    common = rng.randn(n)
    # Для L = common и R = w·common + noise (обе части нормированы по дисперсии):
    # corr = w / sqrt(1 + w²), отсюда w = corr / sqrt(1 − corr²).
    weight = corr / np.sqrt(max(1.0 - corr * corr, 1e-6))
    left = common
    right = weight * common + rng.randn(n)
    left = left / np.abs(left).max() * 0.5
    right = right / np.abs(right).max() * 0.5
    sf.write(str(path), np.stack([left, right], axis=1).astype(np.float32), SR)
    measured = float(np.corrcoef(left, right)[0, 1])
    assert abs(measured - corr) < 0.05, (measured, corr)
    return str(path)


def test_healthy_width_scores_best(tmp_path) -> None:
    score, corr = _stereo_width(_stereo_with_correlation(tmp_path / "w.wav", 0.70))

    assert 0.6 <= corr <= 0.8, corr
    assert score >= 85.0, (score, corr)


def test_wide_is_better_than_too_wide(tmp_path) -> None:
    """Широко, но в фазе — не то же самое, что «каналы разъехались»."""
    healthy, _ = _stereo_width(_stereo_with_correlation(tmp_path / "a.wav", 0.70))
    wide, _ = _stereo_width(_stereo_with_correlation(tmp_path / "b.wav", 0.40))
    very_wide, _ = _stereo_width(_stereo_with_correlation(tmp_path / "c.wav", 0.10))

    assert healthy > wide > very_wide, (healthy, wide, very_wide)
    assert wide - very_wide >= 8.0, (wide, very_wide)


def test_near_mono_is_punished(tmp_path) -> None:
    score, corr = _stereo_width(_stereo_with_correlation(tmp_path / "m.wav", 0.99))

    assert corr > 0.95, corr
    assert score <= 45.0, (score, corr)


def test_mono_file_is_not_a_wide_mix(tmp_path) -> None:
    """Один канал — это не «стерео», и оценка должна это сказать числом."""
    mono = np.zeros((SR * SECONDS, 1), dtype=np.float32)
    mono[:, 0] = 0.3 * np.sin(2 * np.pi * 220 * np.arange(len(mono)) / SR)
    path = tmp_path / "mono.wav"
    sf.write(str(path), mono, SR)

    score, corr = _stereo_width(str(path))

    assert corr >= 0.99, corr
    assert score <= 45.0, (score, corr)
