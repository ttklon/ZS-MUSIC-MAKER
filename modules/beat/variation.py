# -*- coding: utf-8 -*-
"""modules/beat/variation.py — микро-вариативность повторов и метрика формульности.

План 4.7.1 и 4.7.3.

**Проблема.** Один и тот же такт, повторённый 8 раз, слышится как машина, даже
если каждый удар чуть «человечен»: человеческое исполнение меняет не только
микротайминг, но и *сам рисунок* — где-то хэт не сыгран, где-то добавлена
ghost-нота, где-то открытый хэт вместо закрытого.

**Решение.** `bar_variant()` детерминированно (по RNG конструктора) выбирает
изменения для каждого такта. Все изменения — в пределах ±1 удара, никогда не
ломают кик и не трогают сильные доли: грув остаётся узнаваемым.

**Измерение.** `repetition_report()` считает энтропию типов тактов по четырём
признакам (RMS, спектральный центроид, баланс низ/верх, плотность атак) и
среднее сходство соседних тактов. Это и есть тест «формульности»: одинаковые
такты → энтропия 0; живой трек с развитием → 0.5 и выше.
"""

from __future__ import annotations

import math
from typing import Callable

import numpy as np

__all__ = [
    "BAR_FEATURES",
    "MIN_ENTROPY",
    "bar_variant",
    "bar_features",
    "repetition_report",
]

BAR_FEATURES = ("rms_db", "centroid_hz", "low_high_ratio_db", "onset_density")
MIN_ENTROPY = 0.35  # ниже — рисунок повторяется «формулой»

# Сильные доли: их не трогаем никогда — иначе поедет сам грув.
ANCHOR_STEPS = frozenset({0, 4, 8, 12})
# Слабые шаги, где допустима вариация хэта.
HAT_STEPS = (2, 6, 10, 14, 3, 7, 11, 15)
GHOST_SNARE_STEPS = (7, 9, 15)


def bar_variant(
    random: Callable[[], float],
    uniform: Callable[[float, float], float],
    bar: int,
    section: str,
    *,
    strength: float = 1.0,
) -> dict[str, object]:
    """Изменения рисунка для конкретного такта (детерминированно).

    Возвращает:
      * `skip_hat_steps` — шаги, где хэт промолчит (0–1 на такт);
      * `extra_hat_steps` — добавленные офф-бит хэты;
      * `ghost_snare_steps` — тихие ghost-ноты малого;
      * `bar_gain_db` — ±0.3 дБ «дыхания» такта;
      * `signature` — короткая строка для отчёта/дебага.
    """
    strength = max(0.0, float(strength))
    skip: tuple[int, ...] = ()
    extra: tuple[int, ...] = ()
    ghost: tuple[int, ...] = ()
    gain_db = 0.0

    # Вариация включается не в каждом такте: рисунок должен «дышать», а не
    # сыпаться. Вероятность тем выше, чем сильнее запрос.
    if random() < 0.55 * strength:
        candidates = [s for s in HAT_STEPS if s not in ANCHOR_STEPS]
        skip = (candidates[int(random() * len(candidates))],)

    if random() < 0.35 * strength:
        extra_pool = [s for s in (7, 15) if s not in skip]
        if extra_pool:
            extra = (extra_pool[int(random() * len(extra_pool))],)

    if section in ("verse", "hook", "chorus", "pre_chorus") and random() < 0.22 * strength:
        ghost_pool = [s for s in GHOST_SNARE_STEPS if s not in skip]
        if ghost_pool:
            ghost = (ghost_pool[int(random() * len(ghost_pool))],)

    # Каждый четвёртый такт фразы — чуть тише или чуть громче (дыхание фразы).
    if bar % 8 == 7:
        gain_db = float(uniform(-0.35, 0.15))
    elif random() < 0.5:
        gain_db = float(uniform(-0.15, 0.15))

    return {
        "skip_hat_steps": skip,
        "extra_hat_steps": extra,
        "ghost_snare_steps": ghost,
        "bar_gain_db": round(gain_db, 2),
        "signature": f"b{bar}:{'s' if skip else '-'}{'x' if extra else '-'}{'g' if ghost else '-'}",
    }


def _bar_features(mono: np.ndarray, sample_rate: int) -> np.ndarray:
    """Признаки одного такта: уровень, яркость, баланс полос, плотность атак."""
    if mono.size < 16:
        return np.zeros(len(BAR_FEATURES))
    rms = float(np.sqrt(np.mean(mono**2)) + 1e-12)
    rms_db = 20.0 * math.log10(max(rms, 1e-9))

    spectrum = np.abs(np.fft.rfft(mono * np.hanning(mono.size)))
    freqs = np.fft.rfftfreq(mono.size, 1.0 / sample_rate)
    total = float(spectrum.sum()) + 1e-12
    centroid = float((spectrum * freqs).sum() / total)

    low = float((spectrum * (freqs < 150)).sum())
    high = float((spectrum * (freqs >= 150)).sum()) + 1e-12
    low_high_db = 20.0 * math.log10(max(low, 1e-9) / high)

    envelope = np.abs(mono)
    flux = np.diff(envelope)
    threshold = 3.0 * float(np.std(flux)) if flux.size else 0.0
    onsets = int(np.count_nonzero(flux > threshold)) if threshold > 0 else 0
    onset_density = onsets / max(mono.size / sample_rate, 1e-6)

    return np.array([rms_db, centroid / 1000.0, low_high_db, onset_density])


def _cluster_types(features: np.ndarray, max_types: int = 8) -> list[int]:
    """Разбить такты на типы: k-средних с детерминированной инициализацией."""
    n = features.shape[0]
    if n == 0:
        return []
    k = min(max_types, max(1, n // 2))
    # инициализация: равномерно по треку — без случайности
    centers = features[np.linspace(0, n - 1, k).astype(int)].copy()
    labels = np.zeros(n, dtype=int)
    for _ in range(12):
        distances = ((features[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
        labels = distances.argmin(axis=1)
        for index in range(k):
            members = features[labels == index]
            if members.size:
                centers[index] = members.mean(axis=0)
    return labels.tolist()


def bar_features(y: np.ndarray, sample_rate: int, bpm: float) -> np.ndarray:
    """Матрица признаков по тактам (4/4, один такт = 4 доли)."""
    audio = np.asarray(y, dtype=np.float64)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    bar_samples = int(round(4 * 60.0 / max(bpm, 1.0) * sample_rate))
    if bar_samples <= 0 or audio.size < bar_samples:
        return np.zeros((0, len(BAR_FEATURES)))
    n_bars = audio.size // bar_samples
    return np.vstack(
        [_bar_features(audio[i * bar_samples : (i + 1) * bar_samples], sample_rate) for i in range(n_bars)]
    )


def repetition_report(
    y: np.ndarray, sample_rate: int, bpm: float, *, max_types: int = 8
) -> dict[str, float | int | bool]:
    """Отчёт «формульности»: энтропия типов тактов и сходство соседей."""
    features = bar_features(y, sample_rate, bpm)
    if features.shape[0] < 4:
        return {
            "bars": int(features.shape[0]),
            "distinct_types": 0,
            "entropy": 0.0,
            "entropy_normalized": 0.0,
            "bar_similarity": 1.0,
            "formulaic": True,
            "reason": "too few bars to measure",
        }

    scale = features.std(axis=0)
    scale[scale < 1e-9] = 1.0
    normalized = (features - features.mean(axis=0)) / scale
    labels = _cluster_types(normalized, max_types=max_types)

    counts = np.bincount(np.asarray(labels), minlength=max(labels) + 1)
    probabilities = counts[counts > 0] / float(len(labels))
    entropy = float(-(probabilities * np.log2(probabilities)).sum())
    entropy_normalized = float(entropy / math.log2(len(labels))) if len(labels) > 1 else 0.0

    # Сходство соседних тактов по нормированным признакам (косинус).
    # Полностью одинаковые такты дают нулевой вектор после z-нормировки —
    # для них сходство равно 1.0 по определению (а не 0 из-за деления на 0).
    norms = np.linalg.norm(normalized, axis=1)
    unit = np.divide(
        normalized, norms[:, None], out=np.zeros_like(normalized), where=norms[:, None] > 1e-9
    )
    similarities = np.sum(unit[:-1] * unit[1:], axis=1)
    identical_pairs = (norms[:-1] < 1e-9) & (norms[1:] < 1e-9)
    if np.any(identical_pairs):
        similarities[identical_pairs] = 1.0
    similarity = float(np.mean(similarities))

    return {
        "bars": int(features.shape[0]),
        "distinct_types": int(len(set(labels))),
        "entropy": round(entropy, 3),
        "entropy_normalized": round(entropy_normalized, 3),
        "bar_similarity": round(similarity, 3),
        "formulaic": bool(entropy_normalized < MIN_ENTROPY),
        "min_entropy": MIN_ENTROPY,
    }
