# -*- coding: utf-8 -*-
"""
modules/mastering.py — мастеринг под стенды (numpy-DSP, без тяжёлых зависимостей).

  • per-stand EQ (однополюсные полки),
  • soft-knee tanh-limiter с итеративной dBFS-компенсацией,
  • целевая громкость по стендам,
  • pyloudnorm ITU-BS.1770, если установлен (иначе честная dBFS-оценка),
  • master_one / master_all_stands — сохранение стерео, без mono-downmix.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

try:  # опционально: точный LUFS по ITU-BS.1770
    import pyloudnorm as pyln  # type: ignore

    _HAS_PYLN = True
except Exception:  # pragma: no cover
    pyln = None
    _HAS_PYLN = False

# Целевые уровни стендов (dBFS RMS-эквивалент; v26: +0.5dB под живые плееры)
STAND_TARGET_DBFS: dict[str, float] = {
    "streaming": -13.5,
    "car": -12.0,
    "club": -11.0,
    "tiktok": -12.5,
    "airpods": -14.0,
    "bluetooth": -14.5,
    "headphones": -13.5,
    "monitors": -13.5,
}

ALL_STANDS = list(STAND_TARGET_DBFS.keys())
_LOG = logging.getLogger(__name__)


def _one_pole_shelf(y: np.ndarray, sr: int, cutoff: float, gain_db: float,
                    band: str) -> np.ndarray:
    """Простейший shelving EQ на однополюсном фильтре (low/high band)."""
    rc = 1.0 / (2.0 * np.pi * cutoff)
    dt = 1.0 / float(sr)
    g = 10.0 ** (gain_db / 20.0)
    if y.ndim == 1:
        y = y[:, None]
        squeeze = True
    else:
        squeeze = False
    # lowpass для выделения полосы
    a_lp = dt / (rc + dt)
    low = np.zeros_like(y)
    prev = np.zeros(y.shape[1], dtype=np.float64)
    for n in range(len(y)):
        prev = prev + a_lp * (y[n] - prev)
        low[n] = prev
    high = y - low
    if band == "low":
        out = low * g + high
    else:
        out = low + high * g
    return out[:, 0] if squeeze else out


def _apply_stand_eq(y: np.ndarray, sr: int, stand: str) -> np.ndarray:
    """Характер стенда: низ/верх под сценарий прослушивания."""
    eq = {
        "streaming": ((150, 0.5, "low"), (8000, 1.0, "high")),
        "car": ((120, 2.0, "low"), (6500, 1.5, "high")),
        "club": ((100, 2.5, "low"), (9000, 0.5, "high")),
        "tiktok": ((200, 1.0, "low"), (7500, 2.0, "high")),
        "airpods": ((250, 1.0, "low"), (8000, 1.5, "high")),
        "bluetooth": ((180, 1.5, "low"), (7000, 1.0, "high")),
        "headphones": ((150, 0.5, "low"), (9000, 0.5, "high")),
        "monitors": ((150, 0.0, "low"), (10000, 0.0, "high")),
    }
    for cutoff, gdb, band in eq.get(stand, eq["streaming"]):
        if abs(gdb) > 1e-6:
            y = _one_pole_shelf(y, sr, cutoff, gdb, band)
    return y


def _loudness_dbfs(y: np.ndarray) -> float:
    rms = float(np.sqrt(np.mean(y**2)) + 1e-12)
    return 20.0 * np.log10(max(rms, 1e-12))


def _measure_lufs(y: np.ndarray, sr: int) -> tuple[float, dict[str, str]]:
    """Измеряет LUFS и раскрывает fallback точной метрики, если он случился."""
    fallback = _loudness_dbfs(y) - 3.0
    if not _HAS_PYLN:
        return fallback, {"lufs_engine": "dbfs_estimate", "lufs_status": "unavailable"}
    try:
        meter = pyln.Meter(sr)
        mono = y.mean(axis=1) if y.ndim > 1 else y
        return float(meter.integrated_loudness(mono)), {"lufs_engine": "pyloudnorm"}
    except Exception as exc:
        _LOG.warning("pyloudnorm measurement failed; using dBFS estimate: %s", exc)
        return fallback, {
            "lufs_engine": "dbfs_estimate",
            "lufs_status": "failed",
            "lufs_error": f"{type(exc).__name__}: {exc}",
        }


def _loudness_lufs(y: np.ndarray, sr: int) -> float:
    """Совместимый числовой LUFS API с документированным dBFS fallback."""
    return _measure_lufs(y, sr)[0]


def _tanh_limit(y: np.ndarray, drive: float = 1.0, ceiling: float = 0.98) -> np.ndarray:
    """Soft-knee tanh limiter: glue + защита от клиппинга."""
    return np.tanh(y * drive) / np.tanh(drive) * ceiling


def _try_numpy_dsp(y: np.ndarray, sr: int, stand: str) -> tuple[np.ndarray, dict]:
    """Основной DSP-путь мастеринга (честный, fallback_used=False):
    EQ → итеративная loudness-компенсация → tanh-limiter."""
    info: dict[str, Any] = {"fallback_used": False, "engine": "numpy_dsp"}
    y = _apply_stand_eq(y, sr, stand)
    target = STAND_TARGET_DBFS.get(stand, -13.5)
    # tanh-limiter поднимает RMS на ~+3.1dB после насыщения — компенсируем,
    # чтобы итог попадал в целевой dBFS, а не улетал в +3dB (v27 FIX loudness).
    target = target - 3.1
    # 3 итерации: gain → limit → измерение → докомпенсация
    for _ in range(3):
        cur = _loudness_dbfs(y)
        delta = target - cur
        y = y * (10.0 ** (delta / 20.0))
        y = _tanh_limit(y, drive=1.4)
    final_lufs, lufs_info = _measure_lufs(y, sr)
    info["target_dbfs"] = target + 3.1
    info["final_dbfs"] = round(_loudness_dbfs(y), 2)
    info["final_lufs"] = round(final_lufs, 2)
    info.update(lufs_info)
    return y, info


def master_one(mix_wav: str, out_wav: str, stand: str = "streaming") -> dict[str, Any]:
    """Мастеринг одного WAV под конкретный стенд. Сохраняет стерео."""
    try:
        y, sr = sf.read(mix_wav, always_2d=True)  # (N, C) — стерео сохраняется
    except Exception as e:
        return {"ok": False, "reason": f"read failed: {type(e).__name__}: {e}"}
    if y.shape[1] < 2:  # если вошло моно — делаем dual-mono стерео
        y = np.repeat(y, 2, axis=1)
    try:
        y2, info = _try_numpy_dsp(y, sr, stand)
        os.makedirs(os.path.dirname(out_wav) or ".", exist_ok=True)
        sf.write(out_wav, y2.astype(np.float32), sr)
        return {
            "ok": True,
            "path": out_wav,
            "stand": stand,
            "channels": int(y2.shape[1]),
            **info,
        }
    except Exception as e:
        return {"ok": False, "reason": f"dsp failed: {type(e).__name__}: {e}"}


def master_all_stands(
    mix_wav: str, out_dir: str, stands: list[str] | None = None
) -> dict[str, Any]:
    """Мастеринг под все запрошенные стенды.

    Возвращает {"ok", "masters": {stand: path}, "summary": {...}} —
    контракт, который ждёт orchestrator._stage_mastering.
    """
    stands = stands or ALL_STANDS
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    masters: dict[str, str] = {}
    fallback = 0
    errors: dict[str, str] = {}
    for stand in stands:
        out_wav = str(out / f"master_{stand}.wav")
        r = master_one(mix_wav, out_wav, stand=stand)
        if r.get("ok"):
            masters[stand] = out_wav
            if r.get("fallback_used"):
                fallback += 1
        else:
            errors[stand] = str(r.get("reason", "unknown"))
    return {
        "ok": bool(masters),
        "masters": masters,
        "summary": {
            "total": len(stands),
            "done": len(masters),
            "fallback": fallback,
            "errors": errors,
        },
        "engine": "mastering (numpy_dsp + optional pyloudnorm)",
    }


if __name__ == "__main__":  # быстрый self-check
    import sys

    if len(sys.argv) > 2:
        print(master_all_stands(sys.argv[1], sys.argv[2]))
    else:
        print("usage: python -m modules.mastering <mix.wav> <out_dir>")
