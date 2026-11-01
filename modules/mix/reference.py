# -*- coding: utf-8 -*-
"""modules/mix/reference.py — референс-матчинг микса с отчётом отклонений (4.5.4).

Два движка, оба честные:

1. **matchering** (если установлен) — «золотой» путь: он сравнивает трек с
   референсом в спектральной и динамической области;
2. **band_eq_match** — собственный адаптер: профиль по октавным полосам,
   разница (референс − микс), ограниченная ±9 дБ, применяется как точная
   реконструкция набора полос (`apply_band_gains`). Это не «магия», а
   измеримая коррекция: до/после считается одна и та же метрика.

В отчёте всегда есть отклонения по полосам (дБ), по LUFS и по crest — до и
после. Гейт: после матчинга профиль ушёл от референса не больше чем на 2.5 дБ
по каждой полосе.
"""

from __future__ import annotations

import json
from pathlib import Path
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
    return audio, int(sr)


def _band_split(y: np.ndarray, sample_rate: int) -> list[np.ndarray]:
    """Точное разложение на полосы: сумма полос равна исходному сигналу."""
    audio = np.asarray(y, dtype=np.float64)
    if audio.ndim == 1:
        audio = audio[:, None]
    bands: list[np.ndarray] = []
    previous = np.zeros_like(audio)
    for edge in BAND_EDGES_HZ:
        low = filters.split_bands(audio, sample_rate, edge)[0]
        bands.append(low - previous)
        previous = low
    bands.append(audio - previous)
    return bands


def band_profile(y: np.ndarray, sample_rate: int) -> np.ndarray:
    """RMS по полосам (дБ) — профиль «характера» микса."""
    return np.array(
        [metrics.rms_dbfs(band) for band in _band_split(y, sample_rate)], dtype=np.float64
    )


def apply_band_gains(y: np.ndarray, sample_rate: int, gains_db: np.ndarray) -> np.ndarray:
    """Применить усиление по полосам с точной реконструкцией полос."""
    audio = np.asarray(y, dtype=np.float64)
    bands = _band_split(audio, sample_rate)
    out = np.zeros_like(audio if audio.ndim == 2 else audio[:, None])
    for band, gain_db in zip(bands, gains_db):
        out = out + band * (10.0 ** (float(gain_db) / 20.0))
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
    reference_wav: str,
    out_wav: str | None = None,
    *,
    max_correction_db: float = MAX_CORRECTION_DB,
    engine: str = "band_eq_match",
) -> dict[str, Any]:
    """Подогнать микс под референс и вернуть отчёт отклонений до/после."""
    if not Path(mix_wav).exists():
        return {"ok": False, "reason": f"mix not found: {mix_wav}"}
    if not Path(reference_wav).exists():
        return {"ok": False, "reason": f"reference not found: {reference_wav}"}

    out_wav = out_wav or str(Path(mix_wav).with_name("mix_matched.wav"))
    mix, sample_rate = _load(mix_wav)
    reference, reference_sr = _load(reference_wav)
    if reference_sr != sample_rate:
        # профиль считается в полосах: частота дискретизации референса не важна,
        # но для честности фиксируем это в отчёте.
        reference_info = {"reference_sample_rate": reference_sr}
    else:
        reference_info = {}

    reference_profile = band_profile(reference, reference_sr)
    before_profile = band_profile(mix, sample_rate)
    correction = np.clip(reference_profile - before_profile, -max_correction_db, max_correction_db)

    engine_used = "band_eq_match"
    fallback_used = False
    reason = None
    if engine == "matchering":
        matched = _match_with_matchering(mix_wav, reference_wav, out_wav)
        if matched and matched.get("ok"):
            engine_used = "matchering"
            written, _ = _load(out_wav)
        else:
            fallback_used = True
            reason = (matched or {}).get("reason", "matchering unavailable")
            written = apply_band_gains(mix, sample_rate, correction)
            engine_used = "band_eq_match"
    else:
        written = apply_band_gains(mix, sample_rate, correction)

    # Страховка уровня: матчинг не должен «выстрелить» в клиппинг.
    peak = float(np.max(np.abs(written))) if written.size else 0.0
    if peak > 0.98:
        written = written / peak * 0.98

    after_profile = band_profile(written, sample_rate)
    deviation = _deviation_report(before_profile, after_profile, reference_profile)
    gates = {
        "profile_deviation": deviation["max_deviation_after_db"] <= GATE_DEVIATION_DB,
        "true_peak": metrics.true_peak_dbtp(written) <= -1.0,
        "no_clipping": metrics.clipping_samples(written) == 0,
    }

    out_path = Path(out_wav)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    import soundfile as sf

    sf.write(str(out_path), written.astype(np.float32), sample_rate)

    report: dict[str, Any] = {
        "ok": True,
        "out_wav": str(out_path),
        "engine": engine_used,
        "fallback_used": fallback_used,
        "reason": reason,
        "correction_db": {f"{int(edge)}Hz": round(float(value), 2) for edge, value in zip(BAND_EDGES_HZ + (20000.0,), correction)},
        "loudness": {
            "mix_lufs": round(float(metrics.integrated_lufs(mix, sample_rate)[0]), 2),
            "reference_lufs": round(float(metrics.integrated_lufs(reference, reference_sr)[0]), 2),
            "matched_lufs": round(float(metrics.integrated_lufs(written, sample_rate)[0]), 2),
        },
        "crest_db": {
            "mix": round(metrics.crest_db(mix), 2),
            "reference": round(metrics.crest_db(reference), 2),
            "matched": round(metrics.crest_db(written), 2),
        },
        "bands": deviation,
        "gates": gates,
        "gates_passed": all(gates.values()),
        **reference_info,
    }
    report_path = out_path.with_name("reference_match_report.json")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["report_path"] = str(report_path)
    return report
