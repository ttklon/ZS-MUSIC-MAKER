# -*- coding: utf-8 -*-
"""
modules/hit_scorer/mix_metrics.py — метрики микса и формы: громкость (LUFS с
честной прованс-диагностикой), стерео-ширина, низ, читаемость вокала,
читаемость структуры и новизна звучания.
"""

from __future__ import annotations

import logging

from modules.hit_scorer.audio import (
    HAS_LIBROSA,
    HAS_PYLOUDNORM,
    HAS_SF,
    librosa,
    np,
    pyln,
    sf,
)
from modules.hit_scorer.hook_metrics import (
    _bpm_dance_fitness,
    _chorus_catchiness,
    _db,
    _drop_impact,
    _hook_energy,
    _hook_repeatability,
    _rms,
    _tiktok_hookability,
)

_LOG = logging.getLogger("modules.hit_scorer")


def _loudness_rms_estimate(y) -> tuple[float, float]:
    """Возвращает существующую RMS-based pseudo-LUFS оценку."""
    rms = _rms(y)
    dbfs = _db(rms)
    if -14.0 <= dbfs <= -10.0:
        score = 95.0
    elif -17.0 <= dbfs < -14.0:
        score = 75.0
    elif -10.0 < dbfs <= -7.0:
        score = 80.0
    elif -7.0 < dbfs <= -4.0:
        score = 60.0
    else:
        score = 40.0
    return score, dbfs


def _loudness_lufs_status(y, sr) -> tuple[tuple[float, float], dict[str, str]]:
    """Возвращает loudness score и provenance optional pyloudnorm метрики."""
    if np is None:
        return (60.0, -14.0), {"engine": "default_estimate", "status": "unavailable"}
    if HAS_PYLOUDNORM:
        try:
            # y is mono from _load_audio
            meter = pyln.Meter(sr)
            lufs = float(meter.integrated_loudness(y))
            # Для LUFS таргет обычно -14..-9
            if -14.0 <= lufs <= -9.0:
                score = 98.0
            elif -16.0 <= lufs < -14.0:
                score = 80.0
            elif -9.0 < lufs <= -7.0:
                score = 85.0
            else:
                score = 50.0
            return (score, lufs), {"engine": "pyloudnorm"}
        except Exception as exc:
            _LOG.warning("pyloudnorm analysis failed; using RMS estimate: %s", exc)
            estimate = _loudness_rms_estimate(y)
            return estimate, {
                "engine": "rms_estimate",
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
            }
    return _loudness_rms_estimate(y), {"engine": "rms_estimate", "status": "unavailable"}


def _loudness_lufs(y, sr) -> tuple[float, float]:
    """Совместимый loudness API без изменения score/raw tuple контракта."""
    return _loudness_lufs_status(y, sr)[0]


def _stereo_width(path: str) -> tuple[float, float]:
    """Требуется стерео-файл. Считает корреляцию каналов."""
    if not HAS_SF or np is None:
        return 60.0, 1.0
    try:
        y, _ = sf.read(path, always_2d=True)
        if y.shape[1] < 2:
            return 30.0, 1.0
        l, r = y[:, 0], y[:, 1]
        corr = float(np.corrcoef(l, r)[0, 1])
        # width = 1 - corr; хиты обычно 0.15..0.4 → corr 0.6..0.85
        if 0.55 <= corr <= 0.85:
            score = 90.0
        elif corr < 0.55:
            score = 70.0  # слишком широко
        elif corr < 0.95:
            score = 65.0
        else:
            score = 40.0  # почти моно
        return score, corr
    except Exception:
        return 60.0, 1.0


def _low_end_power(y, sr) -> tuple[float, float]:
    if not HAS_LIBROSA:
        return 60.0, 0.0
    try:
        S = np.abs(librosa.stft(y, n_fft=2048))
        freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
        low_mask = (freqs >= 20) & (freqs <= 80)
        mid_mask = (freqs >= 200) & (freqs <= 2000)
        low_energy = float(S[low_mask, :].mean())
        mid_energy = float(S[mid_mask, :].mean())
        ratio = low_energy / max(mid_energy, 1e-9)
        # Хиты dance/trap: low/mid ≈ 0.6..1.2
        if 0.55 <= ratio <= 1.3:
            score = 92.0
        elif 0.3 <= ratio < 0.55:
            score = 68.0
        elif ratio > 1.3:
            score = 70.0
        else:
            score = 45.0
        return score, ratio
    except Exception:
        return 60.0, 0.0


def _distortion(y, sr) -> tuple[float, float]:
    """Сколько сэмплов упёрлось в потолок: клиппинг — это брак, а не стиль.

    Замер на настоящем бите: `клиппинг ×6` давал −0,12 балла к оценке хита,
    то есть трек, вдавленный в потолок, проходил как чистый. Здесь считается
    доля сэмплов у потолка и «плоских» верхушек: у клиппированного сигнала
    соседние сэмплы равны максимуму, у чистого — нет.
    """
    if np is None or y is None or len(y) == 0:
        return 60.0, {"clipped_share": 0.0, "flat_top_share": 0.0}
    peak = float(np.max(np.abs(y)))
    if peak <= 0.0:
        return 60.0, {"clipped_share": 0.0, "flat_top_share": 0.0}
    # Потолок — это 0 dBFS (−0.2 дБ), а не максимум файла. Считать от
    # максимума нельзя: `librosa.load` ресемплит на 22050, и кольцевые
    # артефакты передискретизации уходят выше 1.0 (замер: пик 1.25 у
    # клиппированного бита). Тогда «потолок» уезжал вместе с ними, и реальный
    # клиппинг давал долю 1e-05 вместо 0.63.
    ceiling = min(0.977, peak * 0.977)
    at_ceiling = np.abs(y) >= ceiling
    clipped_share = float(np.mean(at_ceiling))
    # Плоские верхушки: два сэмпла подряд на потолке. В чистом сигнале такое
    # почти не встречается, у клиппированного — на каждом пике.
    flat = at_ceiling[1:] & at_ceiling[:-1]
    flat_share = float(np.mean(flat)) if flat.size else 0.0
    bad = max(clipped_share - 0.005, 0.0) + flat_share
    score = float(max(0.0, min(100.0, 100.0 - bad * 900.0)))
    return score, {"clipped_share": round(clipped_share, 5), "flat_top_share": round(flat_share, 5)}


def _vocal_presence(y, sr) -> tuple[float, float]:
    if not HAS_LIBROSA:
        return 60.0, 0.0
    try:
        S = np.abs(librosa.stft(y, n_fft=2048))
        freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
        voc_mask = (freqs >= 2000) & (freqs <= 5000)
        all_energy = float(S.mean())
        voc_energy = float(S[voc_mask, :].mean())
        ratio = voc_energy / max(all_energy, 1e-9)
        score = min(100.0, ratio * 90.0 + 25.0)
        return score, ratio
    except Exception:
        return 60.0, 0.0


def _structure_clarity(y, sr) -> tuple[float, int]:
    if not HAS_LIBROSA or len(y) < sr * 30:
        return 55.0, 0
    try:
        # segmentation по chroma+mfcc через spectral clustering — простая версия
        rms = librosa.feature.rms(y=y, hop_length=1024)[0]
        # normalize
        rms = (rms - rms.mean()) / (rms.std() + 1e-9)
        # найдём точки сильного изменения
        changes = np.where(np.abs(np.diff(rms)) > 1.2)[0]
        # ожидаем 3-6 крупных секций
        n = len(changes)
        if 3 <= n <= 8:
            score = 90.0
        elif n < 3:
            score = 50.0
        else:
            score = 70.0
        return score, n
    except Exception:
        return 55.0, 0


def _novelty(y, sr) -> tuple[float, float]:
    """Насколько трек «неформульный» — вариативность спектра во времени."""
    if not HAS_LIBROSA:
        return 60.0, 0.0
    try:
        S = np.abs(librosa.stft(y, n_fft=2048))
        col_var = float(np.mean(np.var(S, axis=1)))
        row_var = float(np.mean(np.var(S, axis=0)))
        # v26: Используем и col_var (время), и row_var (частоты)
        combined_var = (col_var + row_var * 0.1) / 1.1
        score = min(100.0, combined_var * 8e5 + 40.0) if combined_var > 0 else 40.0
        return score, combined_var
    except Exception:
        return 60.0, 0.0


def _metric_set(path: str, y, sr) -> dict:
    """Все метрики, которые не зависят от сборки отчёта.

    Вынесено из `score_track`: функция упиралась в бюджет 60 строк, а это
    ровно список независимых измерений — ему место рядом с самими метриками.
    Значения — `(score, raw)` или просто score, как их отдают функции выше.
    """
    tt_score, tt_slice = _tiktok_hookability(y, sr)
    loudness_result, loudness_provenance = _loudness_lufs_status(y, sr)
    return {
        "hook_energy": _hook_energy(y, sr),
        "hook_repeatability": _hook_repeatability(y, sr),
        "chorus_catchiness": _chorus_catchiness(y, sr),
        "drop_impact": _drop_impact(y, sr),
        "tiktok_hookability": (tt_score, tt_slice),
        "bpm_dance_fitness": _bpm_dance_fitness(y, sr),
        "loudness_lufs": loudness_result,
        "stereo_width": _stereo_width(path),
        "low_end_power": _low_end_power(y, sr),
        "vocal_presence": _vocal_presence(y, sr),
        "structure_clarity": _structure_clarity(y, sr),
        "novelty": _novelty(y, sr),
        "distortion": _distortion(y, sr),
        "_provenance": {"loudness_lufs": loudness_provenance},
        "_slice": tt_slice,
    }
