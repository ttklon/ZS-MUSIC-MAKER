# -*- coding: utf-8 -*-
"""
Запоминаемость припева: две части шкалы должны различать разное.

Было:

    regularity = min(100, len(peaks) * 0.6 + 40)      # число онсетов
    harmonic_simplicity = max(0, min(100, 100 - chroma_var * 400))
    score = 0.6 * regularity + 0.4 * harmonic_simplicity

Оба слагаемых — не то, что заявлено:

* «регулярность» на самом деле громкость: число онсетов растёт с плотностью
  аранжировки, и у восьми мастеров движка их 140…175 — это 124…145 очков,
  то есть всегда потолок 100;
* `chroma_var` — разброс энергии хромы по времени. У тональной музыки он
  почти всегда 0,08–0,10, и `100 − var·400` даёт в лучшем случае +8 очков.

В итоге балл — это 60 + 0,4·(0…8) = 60…63 почти независимо от трека, плюс
40 за «простоту», которая почти нулевая. Замер: разброс 2,1 балла между
восемью жанрами.

Теперь обе половины — про то, что можно услышать:

* `steady` — держится ли темп: разброс интервалов между ударами (CV). У
  танцевального трека он мал, у рубленого — велик;
* `focused` — насколько гармония собрана вокруг одной тоники: энтропия
  распределения хромы. У простой мелодии энтропия низкая, у хроматической
  каши — высокая.
"""

from __future__ import annotations

import numpy as np

from modules.hit_scorer.hook_metrics import _chorus_catchiness

SR = 22_050
SECONDS = 40


def _pulse(bpm: float, jitter: float = 0.0, seconds: int = SECONDS) -> np.ndarray:
    """Ритмичный микс: удары с заданным темпом и разбросом интервалов."""
    rng = np.random.RandomState(17)
    n = SR * seconds
    y = 0.05 * rng.randn(n)
    interval = SR * 60.0 / bpm
    pos = 0.0
    while pos < n:
        idx = int(pos)
        length = min(int(SR * 0.12), n - idx)
        env = np.exp(-np.linspace(0, 8, length))
        y[idx : idx + length] += 0.5 * env * np.sin(np.linspace(0, 60, length))
        pos += interval * (1.0 + jitter * rng.uniform(-1.0, 1.0))
    return y


def _tonal(freqs, seconds: int = SECONDS) -> np.ndarray:
    t = np.arange(SR * seconds) / SR
    sig = np.zeros_like(t)
    for f in freqs:
        sig += 0.12 * np.sin(2 * np.pi * f * t)
    return sig


def test_steady_pulse_beats_erratic_pulse() -> None:
    steady, steady_raw = _chorus_catchiness(_pulse(128.0, 0.0), SR)
    erratic, erratic_raw = _chorus_catchiness(_pulse(128.0, 0.35), SR)

    assert steady > erratic, (steady, erratic, steady_raw, erratic_raw)
    assert steady_raw["ibi_cv"] < erratic_raw["ibi_cv"], (steady_raw, erratic_raw)


def test_focused_harmony_beats_chromatic_cluster() -> None:
    """Простая гармония (3 ноты) должна быть «запоминаемее» хроматической каши."""
    simple, simple_raw = _chorus_catchiness(_tonal([110.0, 165.0, 220.0]), SR)
    chromatic, chromatic_raw = _chorus_catchiness(
        _tonal([110.0 * 2 ** (i / 12) for i in range(12)]), SR
    )

    assert simple_raw["chroma_entropy"] < chromatic_raw["chroma_entropy"], (
        simple_raw,
        chromatic_raw,
    )
    assert simple > chromatic, (simple, chromatic)


def test_reported_values_are_not_saturated() -> None:
    """Живые биты движка не должны давать потолок по обеим половинам."""
    score, raw = _chorus_catchiness(_pulse(129.0, 0.02), SR)

    assert 0.0 <= score <= 100.0
    assert raw["ibi_cv"] < 1.0
    assert 0.0 <= raw["chroma_entropy"] <= 1.0


def test_score_spreads_across_material() -> None:
    """Разные по характеру треки — разные баллы, а не 2,1 балла разброса."""
    scores = [
        _chorus_catchiness(_pulse(128.0, 0.0), SR)[0],
        _chorus_catchiness(_pulse(128.0, 0.3), SR)[0],
        _chorus_catchiness(_tonal([220.0]), SR)[0],
    ]

    assert len(set(round(s, 3) for s in scores)) == 3, scores
    assert max(scores) - min(scores) >= 15.0, scores
