# -*- coding: utf-8 -*-
"""
modules/hit_scorer/hook_metrics.py — метрики «хука»: энергия, повторяемость,
цепляемость припева, контраст дропа, TikTok-срез, танцевальность BPM.
"""

from __future__ import annotations

import math

from modules.hit_scorer.audio import HAS_LIBROSA, librosa, np


def _rms(y) -> float:
    if np is None or y is None or len(y) == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(y)) + 1e-12))


def _db(x: float) -> float:
    return float(20.0 * math.log10(max(x, 1e-9)))


# ============================================================ metrics
def _hook_energy(y, sr) -> tuple[float, float]:
    """Ищем сегмент с максимальной локальной громкостью — это предполагаемый припев."""
    if np is None or len(y) < sr * 8:
        return 50.0, _rms(y)
    win = int(sr * 4)
    hop = int(sr * 1)
    rms_curve = []
    for i in range(0, len(y) - win, hop):
        rms_curve.append(_rms(y[i : i + win]))
    if not rms_curve:
        return 50.0, 0.0
    peak = max(rms_curve)
    median = sorted(rms_curve)[len(rms_curve) // 2]
    ratio = peak / max(median, 1e-6)
    # Хит-припев обычно на +30-60% громче медианы
    score = min(100.0, max(0.0, (ratio - 1.0) * 200.0))
    return score, ratio


def _hook_repeatability(y, sr) -> tuple[float, int]:
    """Повторяемость главного мотива.

    v26 FIX (P1): короткие треки (<20 с) раньше всегда получали 55.0/0
    (ложный нейтрал) и не теряли баллы, но не давали сигнала к улучшению.
    Теперь считаем AC RMS-огибающей даже без librosa — честный signal.
    """
    if not HAS_LIBROSA or len(y) < sr * 20:
        if np is None or len(y) < sr * 2:
            return 55.0, 0
        try:
            win = int(sr * 0.5)
            hop = int(sr * 0.25)
            rms_curve = np.array(
                [_rms(y[i : i + win]) for i in range(0, len(y) - win, hop)],
                dtype="float32",
            )
            if len(rms_curve) < 8:
                return 55.0, 0
            rms_curve = rms_curve - rms_curve.mean()
            _norm = float(np.sum(rms_curve * rms_curve)) + 1e-9
            _peaks = 0
            for lag in range(4, min(len(rms_curve) - 1, 32)):
                ac = float(np.sum(rms_curve[:-lag] * rms_curve[lag:])) / _norm
                if ac > 0.5:
                    _peaks += 1
            score = min(100.0, 40.0 + _peaks * 6.0)
            return score, _peaks
        except Exception:
            return 55.0, 0
    try:
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=1024)
        ssm = np.dot(chroma.T, chroma)
        ssm /= (
            np.linalg.norm(chroma, axis=0)[:, None]
            * np.linalg.norm(chroma, axis=0)[None, :]
            + 1e-9
        )
        off = int(20 * sr / 1024)
        if off >= ssm.shape[0]:
            off = int(4 * sr / 1024)
            if off >= ssm.shape[0] - 1 or off < 1:
                return 50.0, 0
        diag = np.diagonal(ssm, offset=off)
        repeats = int((diag > 0.85).sum())
        score = min(100.0, repeats * 8.0 + 30.0)
        return score, repeats
    except Exception:
        return 50.0, 0


def _chorus_catchiness(y, sr) -> tuple[float, dict]:
    """Комбинация: гармоническая простота (мажор/минор readable) + ритмическая регулярность."""
    if not HAS_LIBROSA:
        return 55.0, {}
    try:
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
        # Регулярность: sharpness пиков огибающей
        peaks = librosa.util.peak_pick(
            onset_env, pre_max=3, post_max=3, pre_avg=5, post_avg=5, delta=0.5, wait=10
        )
        regularity = min(100.0, len(peaks) * 0.6 + 40.0)
        # Гармоническая простота — chroma variance (низкая = простая гармония)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_var = float(np.mean(np.var(chroma, axis=1)))
        harmonic_simplicity = max(0.0, min(100.0, 100.0 - chroma_var * 400.0))
        score = 0.6 * regularity + 0.4 * harmonic_simplicity
        return score, {
            "tempo": float(tempo),
            "peaks": len(peaks),
            "chroma_var": chroma_var,
        }
    except Exception:
        return 55.0, {}


def _drop_impact(y, sr) -> tuple[float, float]:
    """Ищем самый резкий скачок RMS — drop. Хит-drop даёт +6..+9 dB."""
    if np is None or len(y) < sr * 8:
        return 50.0, 0.0
    win = int(sr * 2)
    hop = int(sr * 0.5)
    rms_curve = np.array([_rms(y[i : i + win]) for i in range(0, len(y) - win, hop)])
    if len(rms_curve) < 4:
        return 50.0, 0.0
    diff = np.diff(rms_curve)
    max_jump = float(diff.max())
    baseline = float(np.median(np.abs(diff)))
    ratio = max_jump / max(baseline, 1e-6)
    score = min(100.0, ratio * 12.0)
    return score, ratio


def _tiktok_hookability(y, sr) -> tuple[float, dict]:
    """Находит 15-30 сек кусок с моментальным входом (energy>median в первые 2 сек)."""
    if np is None or len(y) < sr * 15:
        return 40.0, {"start_sec": 0.0, "end_sec": 15.0, "reason": "трек короткий"}
    win_len = int(sr * 25)  # 25 sec — sweet spot TikTok
    hop = int(sr * 2)
    best = {"score": 0.0, "start": 0}
    global_med = _rms(y)
    for i in range(0, len(y) - win_len, hop):
        seg = y[i : i + win_len]
        head_rms = _rms(seg[: int(sr * 2)])
        overall = _rms(seg)
        # Хороший TikTok-slice: сразу громко + держит уровень
        if head_rms > global_med * 0.9 and overall > global_med:
            score = (head_rms / max(global_med, 1e-6)) * 30.0 + (
                overall / max(global_med, 1e-6)
            ) * 20.0
            if score > best["score"]:
                best["score"] = score
                best["start"] = i
    if best["score"] == 0.0:
        # fallback: самый громкий 25-сек кусок
        rms_c = [_rms(y[i : i + win_len]) for i in range(0, len(y) - win_len, hop)]
        idx = int(np.argmax(rms_c)) if rms_c else 0
        best["start"] = idx * hop
        best["score"] = 45.0
    start_sec = best["start"] / sr
    return min(100.0, best["score"] + 20.0), {
        "start_sec": round(start_sec, 2),
        "end_sec": round(start_sec + 25.0, 2),
        "reason": "immediate hook + sustained energy",
    }


def _bpm_dance_fitness(y, sr) -> tuple[float, float]:
    if not HAS_LIBROSA:
        return 60.0, 0.0
    try:
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        t = float(tempo)
        # Sweet spots
        best_ranges = [(120, 140, 100), (70, 95, 90), (95, 120, 75), (140, 160, 80)]
        score = 40.0
        for lo, hi, s in best_ranges:
            if lo <= t <= hi:
                score = float(s)
                break
        return score, t
    except Exception:
        return 60.0, 0.0
