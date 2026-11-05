# -*- coding: utf-8 -*-
"""modules/mix/reference.py — референс-матчинг микса с отчётом отклонений (4.5.4).

Два движка, оба честные:

1. **matchering** (если установлен) — «золотой» путь: он сравнивает трек с
   референсом в спектральной и динамической области;
2. **band_eq_match** — собственный адаптер: профиль по октавным полосам,
   разница (референс − микс), ограниченная ±9 дБ, применяется через
   комплементарные zero-phase фильтры (`apply_band_gains`). Это не «магия», а
   измеримая коррекция: до/после считается одна и та же метрика.

В отчёте всегда есть отклонения по полосам (дБ), по LUFS и по crest — до и
после. Профиль строится на перекрывающихся фильтрах и является приблизительным,
а не идеальным спектральным разделением. Гейт: после матчинга профиль ушёл от
референса не больше чем на 2.5 дБ по каждой измеряемой полосе; если часть
спектра вне общей полосы частот, полнота соответствия не подтверждена.
"""

from __future__ import annotations

import json
from pathlib import Path
from collections.abc import Sequence
from typing import Any

import numpy as np

from modules.dsp import filters, metrics

__all__ = [
    "BAND_EDGES_HZ",
    "band_profile",
    "apply_band_gains",
    "match_to_reference",
]

BAND_EDGES_HZ = (40.0, 80.0, 160.0, 320.0, 640.0, 1280.0, 2560.0, 5120.0, 10240.0)
MAX_CORRECTION_DB = 9.0
GATE_DEVIATION_DB = 2.5


def _load(path: str | Path) -> tuple[np.ndarray, int]:
    import soundfile as sf

    data, sr = sf.read(str(path), always_2d=True)
    audio = np.asarray(data, dtype=np.float64)
    if audio.shape[1] == 1:
        audio = np.repeat(audio, 2, axis=1)
    elif audio.shape[1] != 2:
        raise ValueError(f"unsupported channel count: {audio.shape[1]}")
    return audio, int(sr)


def _resample_for_analysis(audio: np.ndarray, input_rate: int, analysis_rate: int) -> np.ndarray:
    if input_rate == analysis_rate:
        return audio
    from math import gcd
    from scipy.signal import resample_poly

    divisor = gcd(input_rate, analysis_rate)
    return resample_poly(audio, analysis_rate // divisor, input_rate // divisor, axis=0)


def _iter_band_split(y: np.ndarray, sample_rate: int):
    """Yield complementary bands one at a time to limit peak memory."""
    audio = np.asarray(y, dtype=np.float64)
    if audio.ndim == 1:
        audio = audio[:, None]
    previous = np.zeros_like(audio)
    for edge in BAND_EDGES_HZ:
        # A cutoff at/above Nyquist is not a valid digital filter.
        low = audio if edge >= sample_rate / 2 else filters.split_bands(audio, sample_rate, edge)[0]
        yield low - previous
        previous = low
    yield audio - previous


def _band_split(y: np.ndarray, sample_rate: int) -> list[np.ndarray]:
    """Точное разложение на полосы: сумма полос равна исходному сигналу."""
    return list(_iter_band_split(y, sample_rate))


def band_profile(y: np.ndarray, sample_rate: int) -> np.ndarray:
    """RMS по полосам (дБ), без хранения всех полос в памяти."""
    return np.array([metrics.rms_dbfs(band) for band in _iter_band_split(y, sample_rate)], dtype=np.float64)


def apply_band_gains(y: np.ndarray, sample_rate: int, gains_db: np.ndarray) -> np.ndarray:
    """Apply zero-phase, complementary band gains without phase cancellation.

    Accumulating the low-pass differences uses constant memory rather than
    retaining ten full-length bands; forward/backward filtering can pre-ring.
    """
    from scipy.signal import butter, sosfiltfilt

    audio = np.asarray(y, dtype=np.float64)
    if audio.ndim == 1:
        audio = audio[:, None]
    gains = np.asarray(gains_db, dtype=np.float64)
    if len(gains) != len(BAND_EDGES_HZ) + 1 or not np.isfinite(gains).all():
        raise ValueError("invalid band gains")
    linear = 10.0 ** (gains / 20.0)
    out = audio * linear[-1]
    for index, edge in enumerate(BAND_EDGES_HZ):
        weight = linear[index] - linear[index + 1]
        if abs(weight) < 1e-12:
            continue
        if edge >= sample_rate / 2:
            low = audio
        else:
            sos = butter(3, edge, btype="low", fs=sample_rate, output="sos")
            low = sosfiltfilt(sos, audio, axis=0)
        out += low * weight
    return out


def _deviation_report(before: np.ndarray, after: np.ndarray, reference: np.ndarray) -> dict[str, Any]:
    def _bands(profile: np.ndarray) -> dict[str, float]:
        return {f"{int(edge)}Hz": round(float(value), 2) for edge, value in zip(BAND_EDGES_HZ + (20000.0,), profile)}

    deviation_before = reference - before
    deviation_after = reference - after
    return {
        "bands_hz": [int(edge) for edge in BAND_EDGES_HZ] + [20000],
        "profile_before_db": _bands(before),
        "profile_after_db": _bands(after),
        "reference_profile_db": _bands(reference),
        "deviation_before_db": [round(float(value), 2) for value in deviation_before],
        "deviation_after_db": [round(float(value), 2) for value in deviation_after],
        "max_deviation_before_db": round(float(np.max(np.abs(deviation_before))), 2),
        "max_deviation_after_db": round(float(np.max(np.abs(deviation_after))), 2),
    }


def _match_with_matchering(mix_wav: str, reference_wav: str, out_wav: str) -> dict[str, Any] | None:
    try:
        import matchering as mg
    except Exception:  # pragma: no cover - опциональная зависимость
        return None
    try:
        mg.process(target=mix_wav, reference=reference_wav, results=[mg.pcm24(out_wav)])
    except Exception as exc:  # pragma: no cover - matchering падает на нестандартных входах
        return {"ok": False, "reason": f"matchering failed: {type(exc).__name__}: {exc}"}
    if not Path(out_wav).exists():
        return {"ok": False, "reason": "matchering produced no output"}
    return {"ok": True, "engine": "matchering"}


def match_to_reference(
    mix_wav: str,
    reference_wav: str | Path | Sequence[str | Path],
    out_wav: str | None = None,
    *,
    max_correction_db: float = MAX_CORRECTION_DB,
    engine: str = "band_eq_match",
    strength: float = 1.0,
) -> dict[str, Any]:
    """Подогнать микс под референс и вернуть отчёт отклонений до/после."""
    if engine not in ("band_eq_match", "matchering"):
        return {"ok": False, "reason": f"unknown reference matcher: {engine}"}
    if not np.isfinite(strength) or not 0 <= strength <= 1 or not np.isfinite(max_correction_db) or max_correction_db < 0:
        return {"ok": False, "reason": "invalid correction strength or limit"}
    if not Path(mix_wav).is_file():
        return {"ok": False, "reason": f"mix not found: {mix_wav}"}
    paths = [reference_wav] if isinstance(reference_wav, (str, Path)) else list(reference_wav)
    if not paths:
        return {"ok": False, "reason": "no references provided"}
    for path in paths:
        if not Path(path).is_file():
            return {"ok": False, "reason": f"reference not found: {path}"}
    if engine == "matchering" and len(paths) != 1:
        return {"ok": False, "reason": "matchering requires exactly one reference"}
    if engine == "matchering" and strength != 1.0:
        return {"ok": False, "reason": "matchering does not support correction strength"}
    out_wav = out_wav or str(Path(mix_wav).with_name("mix_matched.wav"))
    output_path = Path(out_wav)
    inputs = [Path(mix_wav), *(Path(path) for path in paths)]
    if (output_path.resolve() in {path.resolve() for path in inputs}
            or (output_path.exists() and any(output_path.samefile(path) for path in inputs))):
        return {"ok": False, "reason": "reference match output must not overwrite an input"}
    try:
        import soundfile as sf
        rates = [int(sf.info(str(path)).samplerate) for path in paths]
        mix, sample_rate = _load(mix_wav)
        if sample_rate <= 0 or not mix.size or not np.isfinite(mix).all() or any(rate <= 0 for rate in rates):
            return {"ok": False, "reason": "invalid or empty audio"}
        if np.max(np.abs(mix)) < 1e-8:
            return {"ok": False, "reason": "mix is silent; reference matching unavailable"}
        analysis_rate = min(sample_rate, *rates)
        comparison_mix = _resample_for_analysis(mix, sample_rate, analysis_rate)
        before_profile = band_profile(comparison_mix, analysis_rate)
        profiles, reference_loudness, reference_crest = [], [], []
        for path, ref_rate in zip(paths, rates):
            audio, actual_rate = _load(path)
            if actual_rate != ref_rate or not audio.size or not np.isfinite(audio).all():
                return {"ok": False, "reason": f"invalid or empty reference: {path}"}
            if np.max(np.abs(audio)) < 1e-8:
                return {"ok": False, "reason": f"silent reference: {path}"}
            profiles.append(band_profile(_resample_for_analysis(audio, ref_rate, analysis_rate), analysis_rate))
            reference_loudness.append(metrics.integrated_lufs(audio, ref_rate)[0])
            reference_crest.append(metrics.crest_db(audio))
        # Equal weights in power, rather than an average of decibel magnitudes.
        reference_profile = 10.0 * np.log10(np.maximum(np.mean(10.0 ** (np.asarray(profiles) / 10.0), axis=0), 1e-24))
    except Exception as exc:  # noqa: BLE001 - malformed files and resampling must be explicit
        return {"ok": False, "reason": f"cannot analyze references: {type(exc).__name__}: {exc}"}
    correction = np.clip(reference_profile - before_profile, -max_correction_db, max_correction_db) * strength
    # No direct gain for a band straddling the reference Nyquist; overlapping
    # filters may still affect nearby frequencies, and coverage remains failed.
    if analysis_rate < sample_rate:
        correction = np.array([gain if upper <= analysis_rate / 2 else 0.0
                               for gain, upper in zip(correction, BAND_EDGES_HZ + (float("inf"),))])

    engine_used = "band_eq_match"
    fallback_used = False
    reason = None
    try:
        if engine == "matchering":
            matched = _match_with_matchering(mix_wav, str(paths[0]), out_wav)
            if matched and matched.get("ok"):
                engine_used = "matchering"
                written, output_rate = _load(out_wav)
                if output_rate != sample_rate:
                    return {"ok": False, "reason": "matchering changed sample rate"}
            else:
                fallback_used = True
                reason = (matched or {}).get("reason", "matchering unavailable")
                written = apply_band_gains(mix, sample_rate, correction)
                engine_used = "band_eq_match"
        else:
            written = apply_band_gains(mix, sample_rate, correction)

    except Exception as exc:  # noqa: BLE001 - DSP or backend error is an explicit failure
        return {"ok": False, "reason": f"reference correction failed: {type(exc).__name__}: {exc}"}

    # Страховка уровня: матчинг не должен «выстрелить» в клиппинг.
    peak = float(np.max(np.abs(written))) if written.size else 0.0
    if peak > 0.98:
        written = written / peak * 0.98

    out_path = Path(out_wav)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out_path), written.astype(np.float32), sample_rate)

    # Re-read the encoded WAV; report and gates must describe delivered bytes.
    written, written_rate = _load(out_path)
    if written_rate != sample_rate:
        return {"ok": False, "reason": "written output has unexpected sample rate"}

    after_profile = band_profile(_resample_for_analysis(written, sample_rate, analysis_rate), analysis_rate)
    deviation = _deviation_report(before_profile, after_profile, reference_profile)
    nyquist = analysis_rate / 2
    lower = (0.0,) + BAND_EDGES_HZ
    upper = BAND_EDGES_HZ + (nyquist,)
    deviation["band_intervals_hz"] = [
        [lo, min(hi, nyquist)] if lo < nyquist else None for lo, hi in zip(lower, upper)
    ]
    gates = {
        "profile_deviation": deviation["max_deviation_after_db"] <= GATE_DEVIATION_DB,
        "bandwidth_coverage": analysis_rate >= sample_rate,
        "true_peak": metrics.true_peak_dbtp(written) <= -1.0,
        "no_clipping": metrics.clipping_samples(written) == 0,
    }

    report: dict[str, Any] = {
        "ok": True,
        "out_wav": str(out_path),
        "engine": engine_used,
        "fallback_used": fallback_used,
        "reason": reason,
        "correction_db": {f"{int(edge)}Hz": round(float(value), 2) for edge, value in zip(BAND_EDGES_HZ + (20000.0,), correction)},
        "loudness": {
            "mix_lufs": round(float(metrics.integrated_lufs(mix, sample_rate)[0]), 2),
            "reference_lufs": round(float(np.mean(reference_loudness)), 2),
            "matched_lufs": round(float(metrics.integrated_lufs(written, sample_rate)[0]), 2),
        },
        "crest_db": {
            "mix": round(metrics.crest_db(mix), 2),
            "reference": round(float(np.mean(reference_crest)), 2),
            "matched": round(metrics.crest_db(written), 2),
        },
        "bands": deviation,
        "gates": gates,
        "gates_passed": all(gates.values()),
        "references": [str(path) for path in paths],
        "reference_sample_rates": rates,
        "analysis_sample_rate": analysis_rate,
        "analysis_nyquist_hz": analysis_rate / 2,
        "reference_aggregation": "equal_weight_mean_power",
        "reference_loudness_aggregation": "arithmetic_mean_lufs",
        "correction_strength": strength,
        "eq_filter": "zero_phase_complementary" if engine_used == "band_eq_match" else "matchering",
        "filter_note": "zero-phase filtering may pre-ring transients" if engine_used == "band_eq_match" else None,
        "unassessed_above_hz": analysis_rate / 2 if analysis_rate < sample_rate else None,
    }
    report_path = out_path.with_name("reference_match_report.json")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["report_path"] = str(report_path)
    return report
