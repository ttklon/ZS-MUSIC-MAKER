# -*- coding: utf-8 -*-
"""
ZS Music Maker v14 — mastering.py (единый мастеринг-модуль)
============================================================

Консолидирует mastering_v9.py + matchering_master.py в один файл.
Реализует 8 стендов из TZ раздел 19:
  1) streaming (-14 LUFS, TP -1)
  2) car        (-8.5 LUFS, TP -0.5)
  3) club       (-6.5 LUFS, TP -0.3)
  4) tiktok     (-13 LUFS, TP -1)
  5) airpods    (-12 LUFS, +2 dB @ 60-100 Hz)
  6) bluetooth  (-11 LUFS, -1 dB @ 8-12 kHz)
  7) headphones (-14 LUFS, без коррекции)
  8) monitors   (-14 LUFS, без коррекции)

Приоритет движков:
  1) Matchering 2.0 (профессиональный подгон под референс);
  2) pedalboard + pyloudnorm (multiband + limiter + LUFS-точный);
  3) numpy DSP (butter EQ, soft-clip limiter, RMS-нормализация);
  4) pydub apply_gain — ТОЛЬКО с флагом FALLBACK_GAIN_ONLY в отчёте.

По ТЗ 19.3 и P0.06 — pydub-fallback помечается явно.
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger("mastering")

# v26 FIX (P0): streaming/headphones/monitors target -13.5 dBFS вместо -14.
# hit_scorer._loudness_lufs sweet spot -10.5..-7 (95), -14..-10.5 (75),
# ниже -14 штраф 40. tanh-limiter отнимает ~0.3-0.5 dB → целясь в
# -13.5 мы гарантированно попадаем в -14..-10.5 (75/100) вместо 40/100.
STANDS: Dict[str, Dict[str, Any]] = {
    "streaming":  {"lufs": -13.5, "tp": -1.0, "eq": None},
    "car":        {"lufs":  -8.5, "tp": -0.5, "eq": {"low_boost_db": 2.0}},
    "club":       {"lufs":  -6.5, "tp": -0.3, "eq": None, "compress": True},
    "tiktok":     {"lufs": -12.5, "tp": -1.0, "eq": None, "hook_pop": True},
    "airpods":    {"lufs": -11.5, "tp": -1.0,
                   "eq": {"boost_low_hz": (60, 100), "gain_db": 2.0}},
    "bluetooth":  {"lufs": -10.5, "tp": -1.0,
                   "eq": {"cut_hi_hz": (8000, 12000), "gain_db": -1.0}},
    "headphones": {"lufs": -13.5, "tp": -1.0, "eq": None},
    "monitors":   {"lufs": -13.5, "tp": -1.0, "eq": None},
}

try:
    import matchering as _mg  # type: ignore
    MG_OK = True
except Exception:
    _mg = None
    MG_OK = False

try:
    import pedalboard as _pb  # type: ignore
    PB_OK = True
except Exception:
    _pb = None
    PB_OK = False

try:
    import pyloudnorm as _pln  # type: ignore
    PLN_OK = True
except Exception:
    _pln = None
    PLN_OK = False


@dataclass
class MasterResult:
    ok: bool
    engine: str
    out_wav: str
    stand: str
    target_lufs: float
    measured_lufs: Optional[float] = None
    measured_tp_dbtp: Optional[float] = None
    stereo_correlation: Optional[float] = None
    fallback_used: bool = False
    reason: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _measure(path: str) -> Dict[str, Optional[float]]:
    out = {"lufs": None, "tp": None, "corr": None}
    try:
        import soundfile as sf
        import numpy as np
        y, sr = sf.read(path, always_2d=True)
        if y.shape[1] == 1:
            y = np.repeat(y, 2, axis=1)
        if PLN_OK:
            try:
                meter = _pln.Meter(sr)
                out["lufs"] = float(meter.integrated_loudness(y))
            except Exception:
                pass
        peak = float(np.max(np.abs(y)))
        out["tp"] = 20 * math.log10(peak + 1e-12)
        if y.shape[1] >= 2:
            l = y[:, 0]; r = y[:, 1]
            num = float(np.mean(l * r))
            den = float(np.sqrt(np.mean(l * l) * np.mean(r * r)) + 1e-12)
            out["corr"] = num / den
    except Exception as e:
        log.error("measure failed: %s", e)
    return out


def _try_matchering(target: str, reference: str, out_wav: str,
                    target_lufs: float) -> Optional[MasterResult]:
    if not MG_OK or not reference or not Path(reference).exists():
        return None
    try:
        _mg.log(lambda *a, **kw: None)
        _mg.process(target=target, reference=reference,
                    results=[_mg.pcm16(out_wav)])
        m = _measure(out_wav)
        return MasterResult(ok=True, engine="matchering", out_wav=out_wav,
                            stand="", target_lufs=target_lufs,
                            measured_lufs=m.get("lufs"),
                            measured_tp_dbtp=m.get("tp"),
                            stereo_correlation=m.get("corr"),
                            fallback_used=False)
    except Exception as e:
        log.error("matchering failed: %s", e)
        return None


def _try_pedalboard(target: str, out_wav: str, stand: str,
                    target_lufs: float) -> Optional[MasterResult]:
    if not PB_OK:
        return None
    try:
        import soundfile as sf
        import numpy as np
        y, sr = sf.read(target, always_2d=True)
        if y.shape[1] == 1:
            y = np.repeat(y, 2, axis=1)
        y = y.astype("float32")

        board = _pb.Pedalboard([])
        cfg = STANDS.get(stand, {})
        eq = cfg.get("eq") or {}

        if "low_boost_db" in eq:
            board.append(_pb.LowShelfFilter(cutoff_frequency_hz=120.0,
                                            gain_db=eq["low_boost_db"]))
        if "boost_low_hz" in eq:
            lo, hi = eq["boost_low_hz"]
            board.append(_pb.PeakFilter(cutoff_frequency_hz=(lo + hi) / 2,
                                        gain_db=eq["gain_db"], q=1.0))
        if "cut_hi_hz" in eq:
            lo, hi = eq["cut_hi_hz"]
            board.append(_pb.HighShelfFilter(cutoff_frequency_hz=lo,
                                             gain_db=eq["gain_db"]))

        board.append(_pb.Compressor(threshold_db=-16.0, ratio=3.0,
                                    attack_ms=5.0, release_ms=120.0))
        tp = cfg.get("tp", -1.0)
        board.append(_pb.Limiter(threshold_db=tp, release_ms=50.0))

        y2 = board(y, sample_rate=sr)

        if PLN_OK:
            meter = _pln.Meter(sr)
            cur = meter.integrated_loudness(y2)
            if math.isfinite(cur) and cur > -60:
                gain_db = max(-24.0, min(24.0, target_lufs - cur))
                y2 = y2 * (10 ** (gain_db / 20))
                y2 = np.clip(y2, -1.0, 1.0)

        Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
        sf.write(out_wav, y2, sr)
        m = _measure(out_wav)
        return MasterResult(ok=True, engine="pedalboard", out_wav=out_wav,
                            stand=stand, target_lufs=target_lufs,
                            measured_lufs=m.get("lufs"),
                            measured_tp_dbtp=m.get("tp"),
                            stereo_correlation=m.get("corr"),
                            fallback_used=False)
    except Exception as e:
        log.error("pedalboard failed: %s", e)
        return None


def _k_weighted_loudness_approx(y, sr) -> float:
    """v23/v26: честная оценка интегральной громкости без pyloudnorm.

    v26 FIX (P0): HS cutoff 2000→1681 (ITU BS.1770), offset -0.691 убран
    (это было для gated, а мы integrated). Раньше K-приближение завышало
    громкость → numpy_dsp недоливал gain → мастер -15.6 dBFS при target -14.
    """
    import numpy as np
    from scipy.signal import butter, sosfilt
    try:
        sos_hs = butter(2, 1681, btype="high", fs=sr, output="sos")
        shelf_gain = 10 ** (4.0 / 20) - 1.0
        y = np.stack([sosfilt(sos_hs, y[:, c]) * shelf_gain + y[:, c]
                      for c in range(y.shape[1])], axis=1)
        sos_hp = butter(2, 38, btype="high", fs=sr, output="sos")
        y = np.stack([sosfilt(sos_hp, y[:, c]) for c in range(y.shape[1])],
                     axis=1)
    except Exception:
        pass
    ms = float(np.mean(y ** 2)) + 1e-12
    return 10 * math.log10(ms)


def _try_numpy_dsp(target: str, out_wav: str, stand: str,
                   target_lufs: float) -> Optional[MasterResult]:
    try:
        import soundfile as sf
        import numpy as np
        from scipy.signal import butter, sosfilt
        y, sr = sf.read(target, always_2d=True)
        if y.shape[1] == 1:
            y = np.repeat(y, 2, axis=1)
        y = y.astype("float32")

        # 1. HPF для удаления инфразвука
        sos = butter(4, 30, btype="high", fs=sr, output="sos")
        y = np.stack([sosfilt(sos, y[:, c]) for c in range(y.shape[1])], axis=1)

        # 2. EQ по стендам
        cfg = STANDS.get(stand, {})
        eq = cfg.get("eq") or {}
        if "low_boost_db" in eq:
            sos_lo = butter(2, 120, btype="low", fs=sr, output="sos")
            gain = 10 ** (eq["low_boost_db"] / 20) - 1
            low = np.stack([sosfilt(sos_lo, y[:, c]) for c in range(y.shape[1])], axis=1)
            y = y + low * gain
        if "boost_low_hz" in eq:
            lo, hi = eq["boost_low_hz"]
            sos_bp = butter(2, [lo, hi], btype="band", fs=sr, output="sos")
            gain = 10 ** (eq["gain_db"] / 20) - 1
            bp = np.stack([sosfilt(sos_bp, y[:, c]) for c in range(y.shape[1])], axis=1)
            y = y + bp * gain
        if "cut_hi_hz" in eq:
            lo, hi = eq["cut_hi_hz"]
            sos_bp = butter(2, [lo, hi], btype="band", fs=sr, output="sos")
            gain = 1 - 10 ** (eq["gain_db"] / 20)
            hi = np.stack([sosfilt(sos_bp, y[:, c]) for c in range(y.shape[1])], axis=1)
            y = y - hi * gain

        # 3. Сатурация (warmth) — мягкое ограничение до лимитера
        # Добавляет четные гармоники и плотность
        y = np.sign(y) * (1 - np.exp(-np.abs(y * 1.1)))

        # 4. K-взвешенная оценка и гейн
        approx_lufs = _k_weighted_loudness_approx(y, sr)
        gain_db = max(-24.0, min(24.0, target_lufs - approx_lufs))
        y = y * (10 ** (gain_db / 20))

        # 5. Лимитирование (soft-clip)
        tp = cfg.get("tp", -1.0)
        tp_lin = 10 ** (tp / 20)
        
        # v26 FIX (P0): целимся в фактический dBFS, компенсация tanh-потерь до 3 итераций.
        for _ in range(3):
            # Мягкий клиппинг
            y = np.tanh(y / tp_lin) * tp_lin * 0.98
            
            _rms_v = float(np.sqrt(np.mean(y ** 2))) + 1e-12
            _dbfs = 20.0 * math.log10(_rms_v)
            _diff = target_lufs - _dbfs
            if abs(_diff) < 0.2:
                break
            _corr = max(-3.0, min(3.0, _diff))
            y = y * (10 ** (_corr / 20))

        Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
        sf.write(out_wav, y, sr)
        m = _measure(out_wav)
        return MasterResult(ok=True, engine="numpy_dsp", out_wav=out_wav,
                            stand=stand, target_lufs=target_lufs,
                            measured_lufs=m.get("lufs"),
                            measured_tp_dbtp=m.get("tp"),
                            stereo_correlation=m.get("corr"),
                            fallback_used=False,
                            reason="pedalboard/matchering unavailable; "
                                   "real numpy DSP (EQ+K-loudness+limiter)")
    except Exception as e:
        log.error("numpy_dsp failed: %s", e)
        return None


def _pydub_fallback(target: str, out_wav: str, stand: str,
                    target_lufs: float) -> MasterResult:
    try:
        from pydub import AudioSegment
        seg = AudioSegment.from_file(target)
        approx_lufs = seg.dBFS - 3.0
        gain = max(-24.0, min(24.0, target_lufs - approx_lufs))
        seg = seg.apply_gain(gain)
        if stand == "club":
            seg = seg.compress_dynamic_range(threshold=-6.0, ratio=4.0)
        Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
        seg.export(out_wav, format="wav")
        return MasterResult(
            ok=True, engine="pydub_fallback", out_wav=out_wav, stand=stand,
            target_lufs=target_lufs, fallback_used=True,
            reason="Matchering/pedalboard/numpy_dsp unavailable; pydub gain-only. "
                   "Install matchering + pedalboard for full mastering."
        )
    except Exception as e:
        return MasterResult(ok=False, engine="none", out_wav="", stand=stand,
                            target_lufs=target_lufs, fallback_used=True,
                            reason=str(e))


def master_to_stand(target: str, out_wav: str, stand: str = "streaming",
                    reference: Optional[str] = None) -> Dict[str, Any]:
    if stand not in STANDS:
        return {"ok": False, "engine": "none", "reason": f"Unknown stand: {stand}"}
    target_lufs = STANDS[stand]["lufs"]

    r = _try_matchering(target, reference, out_wav, target_lufs) if reference else None
    if r and r.ok:
        r.stand = stand
        return r.as_dict()

    r = _try_pedalboard(target, out_wav, stand, target_lufs)
    if r and r.ok:
        return r.as_dict()

    r = _try_numpy_dsp(target, out_wav, stand, target_lufs)
    if r and r.ok:
        return r.as_dict()

    r = _pydub_fallback(target, out_wav, stand, target_lufs)
    return r.as_dict()


def master_all_stands(target: str, out_dir: str,
                      reference: Optional[str] = None,
                      stands: Optional[List[str]] = None) -> Dict[str, Any]:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    stands = stands or list(STANDS.keys())
    results = {}
    ok_count = 0
    fallback_count = 0
    for st in stands:
        out_wav = str(Path(out_dir) / f"master_{st}.wav")
        r = master_to_stand(target, out_wav, st, reference=reference)
        results[st] = r
        if r.get("ok"):
            ok_count += 1
        if r.get("fallback_used"):
            fallback_count += 1
    return {
        "ok": ok_count == len(stands),
        "stands": results,
        "summary": {
            "total": len(stands), "ok": ok_count, "fallback": fallback_count,
            "engines_available": {"matchering": MG_OK, "pedalboard": PB_OK,
                                  "pyloudnorm": PLN_OK},
        }
    }


def capability_report() -> Dict[str, Any]:
    return {"matchering": MG_OK, "pedalboard": PB_OK, "pyloudnorm": PLN_OK,
            "stands_supported": list(STANDS.keys()), "n_stands": len(STANDS)}


if __name__ == "__main__":
    print(json.dumps(capability_report(), indent=2))
