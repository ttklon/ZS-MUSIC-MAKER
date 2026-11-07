"""
ZS Music Maker v14 — sidechain.py (настоящий sidechain, TZ 19.5, P0.04)
========================================================================

Реализация sidechain-компрессии:
  — numpy DSP: envelope-follower на кик-канале, ratio-компрессор,
    time-varying gain применяется к bus;
  — метрика ducking: RMS bus в момент кика vs между киками (по ТЗ
    должна быть минимум 3 dB).

НЕ имитация volume-envelope по сетке — реальный расчёт envelope
от кик-канала.

ВАЖНО о границах этого модуля (было обещано лишнее):

  • pedalboard здесь НЕ используется. Раньше в докстринге стояло «pedalboard
    как препроцессор», но `_pb` ни разу не вызывался: обработка целиком на
    numpy, а `PB_OK` — только строка в `capability_report()`. Строка убрана.
  • В рабочем пайплайне сайдчейн делает `modules/mix/ducking.py`
    (`duck_low_band`, только низ шины < 120 Гц, отчёт с измеренной глубиной).
    Этот модуль достижимости не имеет и помечен DEPRECATED в инвентаре
    (`tools/readiness.py`); он остаётся как самостоятельная реализация и как
    регресс-страж `tools/fallback_audit.py` против «бит дакает сам себя».
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import pedalboard as _pb  # type: ignore

    PB_OK = True
except Exception:
    _pb = None
    PB_OK = False

try:
    import numpy as _np
    import soundfile as _sf

    NP_OK = True
except Exception:
    _np = None
    _sf = None
    NP_OK = False

# v18 FIX: scipy вынесен из общего try — без него numpy-DSP должен работать.
try:
    from scipy.signal import butter as _butter
    from scipy.signal import sosfilt as _sosfilt

    SCIPY_OK = True
except Exception:
    _butter = None
    _sosfilt = None
    SCIPY_OK = False


@dataclass
class SidechainResult:
    ok: bool
    engine: str
    out_wav: str
    intensity: float
    kick_rms_db: float
    bus_before_rms_db: float
    bus_after_rms_db: float
    ducking_db: float
    reason: str | None = None


def _envelope_from_kick(
    kick_y, sr: int, attack_ms: float = 5.0, release_ms: float = 120.0
):
    if _np is None:
        return None
    x = _np.abs(kick_y)
    w = max(1, int(sr * 0.005))
    if w > 1:
        k = _np.ones(w) / w
        x = _np.convolve(x, k, mode="same")
    a = math.exp(-1.0 / (sr * (attack_ms / 1000.0)))
    r = math.exp(-1.0 / (sr * (release_ms / 1000.0)))
    env = _np.zeros_like(x)
    y = 0.0
    for i in range(len(x)):
        if x[i] > y:
            y = a * y + (1 - a) * x[i]
        else:
            y = r * y + (1 - r) * x[i]
        env[i] = y
    return env


def _bandpass_numpy(kick_y, sr: int, lo_hz: float = 30.0, hi_hz: float = 200.0):
    """v18: честный numpy-only bandpass 30-200 Гц без scipy.

    FFT brick-wall фильтр: обнуляем частоты вне полосы кика и делаем
    обратное FFT. Это реальный фильтр (не имитация), подходит для
    onset-детекции бочки на слабом железе без scipy.
    """
    n = len(kick_y)
    if n < 4:
        return kick_y
    spec = _np.fft.rfft(kick_y)
    freqs = _np.fft.rfftfreq(n, d=1.0 / sr)
    mask = (freqs >= lo_hz) & (freqs <= hi_hz)
    spec = spec * mask
    return _np.fft.irfft(spec, n=n).astype("float32")


def _detect_kick_onsets(kick_y, sr: int):
    if _np is None:
        return []
    try:
        if SCIPY_OK:
            sos = _butter(4, [30, 200], btype="band", fs=sr, output="sos")
            y = _sosfilt(sos, kick_y)
        else:
            # v18: numpy-only полосовой фильтр, детекция больше не
            # молча отваливается без scipy.
            y = _bandpass_numpy(kick_y, sr)
        env = _np.abs(y)
        w = int(sr * 0.01)
        if w > 1:
            k = _np.ones(w) / w
            env = _np.convolve(env, k, mode="same")
        thr = float(_np.mean(env) + 3 * _np.std(env))
        onsets = []
        min_gap = int(sr * 0.08)
        last = -min_gap
        for i in range(1, len(env) - 1):
            if env[i] > thr and env[i] > env[i - 1] and env[i] >= env[i + 1]:
                if i - last > min_gap:
                    onsets.append(i)
                    last = i
        return onsets
    except Exception:
        return []


def _numpy_dsp(
    bus_wav: str,
    kick_wav: str,
    out_wav: str,
    intensity: float,
    ratio: float = 4.0,
    attack_ms: float = 5.0,
    release_ms: float = 120.0,
) -> SidechainResult:
    if not NP_OK:
        return SidechainResult(
            ok=False,
            engine="none",
            out_wav="",
            intensity=intensity,
            kick_rms_db=-100,
            bus_before_rms_db=-100,
            bus_after_rms_db=-100,
            ducking_db=0.0,
            reason="numpy/soundfile unavailable",
        )
    try:
        bus, sr_b = _sf.read(bus_wav, always_2d=True)
        kick, sr_k = _sf.read(kick_wav, always_2d=True)
        if sr_k != sr_b:
            import scipy.signal as ss

            kick_mono = kick[:, 0] if kick.ndim > 1 else kick
            n = int(len(kick_mono) * sr_b / sr_k)
            kick_mono = ss.resample(kick_mono, n)
            kick = kick_mono
        else:
            kick = kick[:, 0] if kick.ndim > 1 else kick.reshape(-1)

        n = min(len(bus), len(kick))
        bus = bus[:n]
        kick = kick[:n]
        if _np.ndim(kick) > 1:
            kick = kick[:, 0]

        # v19: HP/BP-фильтр 30-200 Гц по kick-каналу ПЕРЕД envelope-follower.
        # Защита от ложных дакингов на вокал/hi-hat, если по ошибке в kick_wav
        # пришёл bus/mix. Реальная бочка обычно 30-200 Гц.
        try:
            kick_hp = _bandpass_numpy(
                kick.astype("float32"), sr_b, lo_hz=30.0, hi_hz=200.0
            )
        except Exception:
            kick_hp = kick.astype("float32")
        env = _envelope_from_kick(
            kick_hp, sr_b, attack_ms=attack_ms, release_ms=release_ms
        )
        env_max = float(_np.max(env) + 1e-9)
        env_n = env / env_max

        thr_lin = 10 ** (-18.0 / 20)
        over = _np.maximum(env_n - thr_lin, 0.0)
        gr_db = -over * 20.0 * (1 - 1 / ratio) * intensity
        gain_lin = 10 ** (gr_db / 20)

        bus_ducked = bus.copy()
        for c in range(bus.shape[1]):
            bus_ducked[:, c] = bus[:, c] * gain_lin
        bus_ducked = _np.clip(bus_ducked, -1.0, 1.0)

        Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
        _sf.write(out_wav, bus_ducked, sr_b)

        kick_rms = float(_np.sqrt(_np.mean(kick**2)) + 1e-9)
        bus_rms_b = float(_np.sqrt(_np.mean(bus**2)) + 1e-9)
        bus_rms_a = float(_np.sqrt(_np.mean(bus_ducked**2)) + 1e-9)
        ducking = measure_ducking_effect(bus, bus_ducked, kick, sr_b)

        return SidechainResult(
            ok=True,
            engine="numpy_dsp_real_sidechain",
            out_wav=out_wav,
            intensity=intensity,
            kick_rms_db=20 * math.log10(kick_rms),
            bus_before_rms_db=20 * math.log10(bus_rms_b),
            bus_after_rms_db=20 * math.log10(bus_rms_a),
            ducking_db=ducking,
        )
    except Exception as e:
        return SidechainResult(
            ok=False,
            engine="none",
            out_wav="",
            intensity=intensity,
            kick_rms_db=-100,
            bus_before_rms_db=-100,
            bus_after_rms_db=-100,
            ducking_db=0.0,
            reason=str(e),
        )


def measure_ducking_effect(bus_before, bus_after, kick, sr: int) -> float:
    if _np is None:
        return 0.0
    try:
        onsets = _detect_kick_onsets(kick, sr)
        if not onsets:
            return 0.0
        w = int(sr * 0.05)
        deltas = []
        b = bus_before[:, 0] if bus_before.ndim > 1 else bus_before
        a = bus_after[:, 0] if bus_after.ndim > 1 else bus_after
        for o in onsets:
            s = o
            e = min(o + w, len(b))
            if e - s < 10:
                continue
            r_b = float(_np.sqrt(_np.mean(b[s:e] ** 2)) + 1e-9)
            r_a = float(_np.sqrt(_np.mean(a[s:e] ** 2)) + 1e-9)
            deltas.append(20 * math.log10(r_b / r_a))
        return float(_np.mean(deltas)) if deltas else 0.0
    except Exception:
        return 0.0


def apply_sidechain(
    bus_wav: str,
    kick_wav: str,
    out_wav: str,
    intensity: float = 0.5,
    ratio: float = 4.0,
    attack_ms: float = 5.0,
    release_ms: float = 120.0,
) -> dict[str, Any]:
    r = _numpy_dsp(
        bus_wav,
        kick_wav,
        out_wav,
        intensity,
        ratio=ratio,
        attack_ms=attack_ms,
        release_ms=release_ms,
    )
    return r.__dict__


def capability_report() -> dict[str, Any]:
    return {
        "pedalboard": PB_OK,
        "numpy_soundfile": NP_OK,
        "scipy": SCIPY_OK,
        "onset_detector": "scipy_butter" if SCIPY_OK else "numpy_fft",
        "real_sidechain_possible": NP_OK,
    }


if __name__ == "__main__":
    print(json.dumps(capability_report(), indent=2))
