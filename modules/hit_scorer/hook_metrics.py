# -*- coding: utf-8 -*-
"""
modules/hit_scorer/hook_metrics.py — метрики «хука»: энергия, повторяемость,
цепляемость припева, контраст дропа, TikTok-срез, танцевальность BPM.
"""

from __future__ import annotations

import math

from modules.hit_scorer.audio import HAS_LIBROSA, librosa, np
from modules.tempo import tempo_scalar


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
        # Абсолютное число повторов зависит от длины: на 60 с их сотни, и
        # `min(100, repeats*8 + 30)` упиралось в 100 у всех восьми мастеров
        # движка (96…280 повторов — все дают 100). Ищем лаг, на котором
        # повторяемость наибольшая (4…30 с), и берём долю кадров, у которых
        # через этот лаг есть похожий кадр: доля от длины не зависит.
        lo = max(int(4 * sr / 1024), 1)
        hi = min(int(30 * sr / 1024), ssm.shape[0] - 1)
        best_share, best_lag = 0.0, 0
        for off in range(lo, hi):
            diag = np.diagonal(ssm, offset=off)
            share = float((diag > 0.9).mean()) if diag.size else 0.0
            if share > best_share:
                best_share, best_lag = share, off
        if best_lag == 0:
            return 50.0, 0.0
        return round(min(100.0, best_share * 100.0), 2), round(best_share, 3)
    except Exception:
        return 50.0, 0.0


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
            "tempo": tempo_scalar(tempo, 0.0),
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


def _best_slice(y, sr) -> tuple[dict, float]:
    """Лучшее 25-секундное окно: уровень относительно трека и ровность.

    Возвращает `(лучшее окно, отношение энергии входа к окну)`. Вход — первые
    две секунды всего трека: у трека, который сразу бьёт, отношение около
    единицы, у трека с длинным вступлением — заметно ниже.
    """
    win_len = min(int(sr * 25), len(y))
    hop = max(int(sr * 2), 1)
    global_rms = _rms(y)
    best = {"score": -1.0, "start": 0, "level": 0.0, "steady": 0.0}
    for i in range(0, max(len(y) - win_len, 0) + 1, hop):
        seg = y[i : i + win_len]
        seg_rms = _rms(seg)
        if seg_rms <= 1e-9:
            continue
        level = seg_rms / global_rms
        chunks = np.array_split(seg, max(int(len(seg) / (sr * 0.5)), 1))
        chunk_rms = np.array([_rms(c) for c in chunks])
        median = float(np.median(chunk_rms))
        steady = float(np.mean(chunk_rms >= median * 0.5)) if median > 0 else 0.0
        score = 40.0 * steady + 30.0 * float(np.clip((level - 0.9) / 0.5, 0.0, 1.0))
        if score > best["score"]:
            best = {"score": score, "start": i, "level": level, "steady": steady}
    slice_rms = max(_rms(y[best["start"] : best["start"] + win_len]), 1e-9)
    head = _rms(y[: int(sr * 2)]) / slice_rms
    return best, head


def _tiktok_hookability(y, sr) -> tuple[float, dict]:
    """Оценивает 25-секундный кусок, который можно поставить в Reels.

    Что здесь измеряется (и чего не измеряется):

    * `уровень` — насколько лучший кусок громче среднего по треку;
    * `ровность` — доля полусекундных фрагментов, которые не проваливаются
      больше чем на 6 дБ относительно медианы куска: клип в Reels не должен
      провисать;
    * `вход` — энергия первых двух секунд относительно лучшего куска:
      работает ли трек сразу, без длинного вступления.

    Это **не** предсказание виральности. Ни одна из этих величин не говорит,
    «залетит» ли трек; она говорит, есть ли в нём громкий и ровный участок и
    начинается ли он сразу. Так и названо в отчёте.

    Прежняя версия считала `head_rms` по первым двум секундам каждого окна и
    требовала `head_rms > global_med * 0.9`: окно почти всегда начиналось в
    тишине, условие не выполнялось, и трек получал фолбэк `45 + 20 = 65,0` —
    одно и то же число на всех восьми мастерах движка и на нарезках от 20 до
    60 секунд. Метрика с весом 1,5 (11,5 % итогового балла) не измеряла
    ничего.
    """
    reason = "яркий и ровный участок; это не предсказание виральности"
    if np is None or len(y) < sr * 15:
        return 40.0, {
            "start_sec": 0.0,
            "end_sec": round(len(y) / sr, 2),
            "reason": "трек короткий: окна 25 с нет",
        }
    if _rms(y) <= 1e-9:
        return 0.0, {
            "start_sec": 0.0,
            "end_sec": round(min(int(sr * 25), len(y)) / sr, 2),
            "reason": "в файле нет энергии",
        }

    best, head = _best_slice(y, sr)
    # Вход: несут ли первые две секунды трека энергию относительно лучшего
    # куска. Раньше здесь стояло `head / global`, и у трека, который сразу
    # бьёт, это отношение упиралось в 1.0 — то есть «моментальный вход» никак
    # не отличался от обычного.
    total = best["score"] + 30.0 * float(np.clip((head - 0.8) / 0.5, 0.0, 1.0))
    start_sec = best["start"] / sr
    return round(min(100.0, max(0.0, total)), 2), {
        "start_sec": round(start_sec, 2),
        "end_sec": round(start_sec + min(int(sr * 25), len(y)) / sr, 2),
        "reason": reason,
        "level_ratio": round(best["level"], 3),
        "steady_share": round(best["steady"], 3),
        "head_ratio": round(head, 3),
    }


def _bpm_dance_fitness(y, sr) -> tuple[float, float]:
    if not HAS_LIBROSA:
        return 60.0, 0.0
    try:
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        t = tempo_scalar(tempo, 0.0)
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
