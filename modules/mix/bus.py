# -*- coding: utf-8 -*-
"""modules/mix/bus.py — сборка микса: бит + вокал → шина (план 4.5).

Порядок жёсткий и единственный:

1. оба элемента сводятся по уровню (gain staging, −18 dBFS RMS шины);
2. вокал получает HP 80 Гц и присутствие +2 дБ на 3 кГц (канальный EQ);
3. шина суммируется, вокал сдвигается вниз на `vocal_gain_db`;
4. сайдчейн kick → низ шины (только < 120 Гц);
5. mid/side ширина приводится к коридору корреляции 0.2…0.8;
6. страховка по пику −6 dBFS на шине и честный отчёт с гейтами §7.2.

Функция не бросает исключений на «плохих» данных: если вокала нет — шина
работает как инструментал и это прямо написано в отчёте (`vocal_used=False`).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from modules.dsp.filters import highpass, shelf
from modules.dsp.metrics import (
    loudness_report,
    peak_dbfs,
    reference_crest_db,
    reference_rms_dbfs,
)
from modules.mix.ducking import duck_low_band
from modules.mix.staging import BUS_TARGET_DBFS, stage
from modules.mix.width import match_width, stereo_report

__all__ = ["build_mix", "prepare_mix", "MIX_GATES"]

MIX_GATES = {
    "bus_rms_dbfs": (-19.0, -17.0),  # опорный участок: −18 ± 1 дБ
    "correlation": (0.2, 0.8),
    "true_peak_dbtp_max": -1.0,
    "peak_dbfs_max": -3.0,  # запас до мастеринга
    "crest_db": (8.0, 14.0),
    "clipping_samples": 0,
}


def _load(path: str | Path) -> tuple[np.ndarray, int]:
    import soundfile as sf

    data, sr = sf.read(str(path), always_2d=True)
    return np.asarray(data, dtype=np.float64), int(sr)


def _fit_length(a: np.ndarray, n: int) -> np.ndarray:
    if a.shape[0] < n:
        pad = np.zeros((n - a.shape[0], a.shape[1]), dtype=a.dtype)
        return np.concatenate([a, pad], axis=0)
    return a[:n]


def _to_stereo(x: np.ndarray) -> np.ndarray:
    if x.ndim == 1:
        return np.stack([x, x], axis=1)
    if x.shape[1] == 1:
        return np.repeat(x, 2, axis=1)
    return x


def _resample(x: np.ndarray, src_sr: int, dst_sr: int) -> np.ndarray:
    if src_sr == dst_sr:
        return x
    try:
        from scipy.signal import resample_poly

        return np.stack([resample_poly(x[:, c], dst_sr, src_sr) for c in range(x.shape[1])], axis=1)
    except Exception:  # pragma: no cover - scipy в зависимостях
        idx = np.linspace(0, x.shape[0] - 1, int(x.shape[0] * dst_sr / src_sr))
        return np.stack([np.interp(idx, np.arange(x.shape[0]), x[:, c]) for c in range(x.shape[1])], axis=1)


def _vocal_chain(vocal: np.ndarray, sample_rate: int) -> np.ndarray:
    """Канальная обработка вокала: HP 80 Гц + присутствие 3 кГц."""
    out = highpass(vocal, sample_rate, 80.0, order=4)
    return shelf(out, sample_rate, 3000.0, 2.0, band="high")


def build_mix(
    beat_wav: str | Path,
    vocal_wav: str | Path | None,
    out_wav: str | Path,
    *,
    vocal_gain_db: float = -3.0,
    bus_target_dbfs: float = BUS_TARGET_DBFS,
    width: float | None = None,
    sidechain: bool = True,
    bus_crest_target_db: float = 12.5,
) -> dict[str, Any]:
    """Собрать микс и вернуть измеренный отчёт (не «ok на слово»)."""
    beat, sr = _load(beat_wav)
    beat = _to_stereo(beat)
    beat_staged, beat_stage = stage(beat, target_rms_dbfs=bus_target_dbfs, sample_rate=sr)
    n = beat_staged.shape[0]

    vocal_used = False
    vocal_stage: dict[str, Any] = {"applied": False}
    vocal: np.ndarray | None = None
    if vocal_wav and Path(str(vocal_wav)).exists():
        raw_vocal, vocal_sr = _load(vocal_wav)
        raw_vocal = _resample(_to_stereo(raw_vocal), vocal_sr, sr)
        raw_vocal = _fit_length(raw_vocal, n)
        if float(np.max(np.abs(raw_vocal))) > 1e-6:
            vocal, vocal_stage = stage(
                _vocal_chain(raw_vocal, sr), target_rms_dbfs=bus_target_dbfs, sample_rate=sr
            )
            vocal_stage["applied"] = True
            vocal_used = True

    bus = beat_staged.copy()
    if vocal is not None:
        bus = bus + vocal * (10.0 ** (vocal_gain_db / 20.0))

    # Финальный gain staging шины: сумма двух элементов всегда громче каждого.
    bus, bus_stage = stage(bus, target_rms_dbfs=bus_target_dbfs, sample_rate=sr)

    duck_report: dict[str, Any] = {"applied": False, "reason": "disabled"}
    if sidechain:
        bus, duck_report = duck_low_band(bus, beat_staged, sr, depth_db=3.5)

    width_report: dict[str, Any] = {"width": 1.0, "correlation_after": stereo_report(bus)["correlation"]}
    if width is None:
        bus, width_report = match_width(bus)
    else:
        bus = bus * 1.0
        from modules.mix.width import apply_width

        bus = apply_width(bus, width)
        width_report = {"width": float(width), **stereo_report(bus)}

    # Контроль крest-фактора: если опорный участок динамичнее 14 дБ, подрезаем
    # только пики шины (look-ahead лимитер) и заново ставим уровень. Именно
    # пик-лимитер, а не компрессор: компрессор с медленной атакой делает крест
    # ЕЩЁ выше (тело тише, транзиенты на месте).
    from modules.dsp.limiter import limit

    glue_info: dict[str, object] = {"applied": False, "passes": []}
    for attempt in range(3):
        if reference_crest_db(bus, sr) <= min(bus_crest_target_db, MIX_GATES["crest_db"][1]) - 0.1:
            break
        bus, pass_info = limit(
            bus, sr, ceiling_dbtp=-6.0 - 2.0 * attempt, lookahead_ms=2.0, release_ms=40.0
        )
        bus, bus_stage = stage(bus, target_rms_dbfs=bus_target_dbfs, sample_rate=sr)
        glue_info["passes"].append(pass_info)  # type: ignore[union-attr]
        glue_info["applied"] = True
    if glue_info["applied"]:
        width_report["correlation_after"] = stereo_report(bus)["correlation"]

    # Страховка по пику шины: запас −3 dBFS, чтобы мастеринг не начинал с клиппа.
    peak_trim_db = 0.0
    if peak_dbfs(bus) > MIX_GATES["peak_dbfs_max"]:
        peak_trim_db = MIX_GATES["peak_dbfs_max"] - peak_dbfs(bus)
        bus = bus * (10.0 ** (peak_trim_db / 20.0))

    report = loudness_report(bus, sr)
    reference_rms = reference_rms_dbfs(bus, sr)
    reference_crest = reference_crest_db(bus, sr)
    gates = {
        "bus_rms": MIX_GATES["bus_rms_dbfs"][0] <= reference_rms <= MIX_GATES["bus_rms_dbfs"][1],
        "correlation": MIX_GATES["correlation"][0]
        <= float(report["stereo_correlation"])
        <= MIX_GATES["correlation"][1],
        "true_peak": float(report["true_peak_dbtp"]) <= MIX_GATES["true_peak_dbtp_max"],
        "crest": MIX_GATES["crest_db"][0] <= reference_crest <= MIX_GATES["crest_db"][1],
        "no_clipping": int(report["clipping_samples"]) == MIX_GATES["clipping_samples"],
    }
    payload: dict[str, Any] = {
        "ok": True,
        "out_wav": str(out_wav),
        "sample_rate": sr,
        "vocal_used": vocal_used,
        "beat_staging": beat_stage,
        "bus_staging": bus_stage,
        "vocal_staging": vocal_stage,
        "glue": glue_info,
        "bus_crest_target_db": bus_crest_target_db,
        "sidechain": duck_report,
        "width": width_report,
        "peak_trim_db": round(peak_trim_db, 2),
        "report": {**report, "reference_rms_dbfs": round(reference_rms, 2),
                   "reference_crest_db": round(reference_crest, 2)},
        "gates": gates,
        "gates_passed": all(gates.values()),
    }

    out = Path(out_wav)
    out.parent.mkdir(parents=True, exist_ok=True)
    import soundfile as sf

    sf.write(str(out), bus.astype(np.float32), sr)
    return payload


def prepare_mix(
    beat_wav: str | Path,
    vocal_wav: str | Path | None,
    out_dir: str | Path,
    **kwargs: Any,
) -> dict[str, Any]:
    """Пайплайн-обёртка: пишет `mix.wav` + `mix_report.json` рядом."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    mix_wav = out_dir / "mix.wav"
    result = build_mix(beat_wav, vocal_wav, mix_wav, **kwargs)
    report_path = out_dir / "mix_report.json"
    report_path.write_text(
        json.dumps({k: v for k, v in result.items() if k != "out_wav"}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    result["report_path"] = str(report_path)
    return result
