# -*- coding: utf-8 -*-
"""modules/beat/spectrum.py — измерение баланса полос готового микса.

Зачем отдельный модуль: «низ не съедает середину» и «верх не режет уши» были
описанием в документации, а не измерением. Окно (`desktop/src/core/audio/analysis.js
::spectrumReport`) уже мерило полосы, но пайплайн — нет, и проверить трек,
собранный через `main.py`, было нечем.

Формулы и границы полос намеренно те же, что в окне: low < 120 Гц,
mid 120–5 кГц, high > 10 кГц. Один и тот же трек должен давать один и тот же
отчёт в обоих путях — иначе «два движка» разъедутся в числах.

Никакого «на глаз»: пороги взяты из измерения готовых миксов этого движка
(низ 0.36–0.60 при сбалансированном миксе) и из физики — 10 кГц это то, ниже
чего «глухо», а 0.62 низа в полосе 0–120 Гц означает маскировку середины.
"""

from __future__ import annotations

from typing import Any

import numpy as np

WINDOW = 4096
LOW_HZ = 120.0
MID_HZ = 5000.0
HIGH_HZ = 10_000.0
LOW_HEAVY = 0.62
DULL = 0.002
MAX_FRAMES = 64


def spectrum_report(y: Any, sample_rate: int) -> dict[str, Any]:
    """Доли энергии в трёх полосах + честные флаги «низ перевесил» и «глухо»."""
    audio = np.asarray(y, dtype=np.float64)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if audio.size < WINDOW:
        return {"ok": False, "bands": None,
                "reason": f"signal too short for a spectrum measurement ({audio.size} < {WINDOW} samples)"}

    window = np.hanning(WINDOW)
    frames = min(MAX_FRAMES, audio.size // WINDOW)
    step = max(1, (audio.size - WINDOW) // max(1, frames - 1))
    band = np.zeros(3, dtype=np.float64)  # low, mid, high
    freqs = np.fft.rfftfreq(WINDOW, 1.0 / sample_rate)
    masks = (freqs < LOW_HZ, (freqs >= LOW_HZ) & (freqs < MID_HZ), freqs >= HIGH_HZ)
    for index in range(frames):
        start = min(audio.size - WINDOW, index * step)
        spectrum = np.abs(np.fft.rfft(audio[start:start + WINDOW] * window)) ** 2
        for position, mask in enumerate(masks):
            band[position] += float(spectrum[mask].sum())

    total = float(band.sum())
    if not total > 0:
        return {"ok": False, "bands": None, "reason": "signal has no measurable energy"}
    share = {"low": round(float(band[0] / total), 3),
             "mid": round(float(band[1] / total), 3),
             "high": round(float(band[2] / total), 3)}
    low_heavy = share["low"] > LOW_HEAVY
    dull = share["high"] < DULL
    if low_heavy:
        reason = "low end dominates: the mid is masked and the track will sound boomy"
    elif dull:
        reason = "almost no energy above 10 kHz: the mix sounds dull"
    else:
        reason = "balanced"
    return {"ok": True, "bands": share, "low_heavy": low_heavy, "dull": dull,
            "frames": frames, "reason": reason}
