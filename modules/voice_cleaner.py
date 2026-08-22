"""Deterministic vocal cleanup: denoise, conservative de-essing and silence gating."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

import soundfile as sf

try:
    import noisereduce as nr  # type: ignore

    _HAS_NR = True
except Exception:  # pragma: no cover - optional runtime dependency
    nr = None
    _HAS_NR = False

CLEANING_PRESETS: dict[str, dict[str, float]] = {
    "default": {"highpass_hz": 80.0, "deesser_low_hz": 4500.0, "deesser_high_hz": 9500.0, "deesser_db": 3.0, "gate_db": -38.0, "gate_floor_db": -80.0},
    "phonk": {"highpass_hz": 85.0, "deesser_low_hz": 4600.0, "deesser_high_hz": 9500.0, "deesser_db": 3.0, "gate_db": -37.0, "gate_floor_db": -80.0},
    "trap": {"highpass_hz": 75.0, "deesser_low_hz": 4400.0, "deesser_high_hz": 9500.0, "deesser_db": 3.0, "gate_db": -39.0, "gate_floor_db": -80.0},
    "pop": {"highpass_hz": 70.0, "deesser_low_hz": 4800.0, "deesser_high_hz": 9500.0, "deesser_db": 3.0, "gate_db": -40.0, "gate_floor_db": -82.0},
}


def cleaning_preset(genre: str | None = None) -> dict[str, float]:
    """Return a copy of the closest non-PII genre cleanup preset."""
    name = (genre or "default").strip().lower().replace("-", "_")
    if name not in CLEANING_PRESETS:
        name = "default"
    return dict(CLEANING_PRESETS[name])


def _as_2d(data):
    import numpy as np

    array = np.asarray(data, dtype="float32")
    return array[:, None] if array.ndim == 1 else array


def _fallback_clean(data, samplerate: int, highpass_hz: float):
    """Remove DC and low-frequency rumble without rolling off high vocal air."""
    import numpy as np

    x = _as_2d(data)
    x = x - np.mean(x, axis=0, keepdims=True)
    rc = 1.0 / (2.0 * np.pi * max(20.0, highpass_hz))
    coefficient = rc / (rc + 1.0 / float(samplerate))
    output = np.zeros_like(x)
    previous_x = x[0].copy()
    previous_y = np.zeros(x.shape[1], dtype=np.float32)
    for index in range(len(x)):
        current = coefficient * (previous_y + x[index] - previous_x)
        output[index] = current
        previous_y = current
        previous_x = x[index]
    return output


def _de_ess(data, samplerate: int, low_hz: float, high_hz: float, reduction_db: float):
    """Attenuate only the sibilance band; content above 10 kHz is left intact."""
    import numpy as np
    from scipy.signal import butter, sosfilt, sosfiltfilt

    x = _as_2d(data)
    nyquist = samplerate / 2.0
    high = min(high_hz, nyquist * 0.95)
    low = min(low_hz, high * 0.8)
    if low <= 0.0 or high <= low:
        return x
    sos = butter(4, [low / nyquist, high / nyquist], btype="bandpass", output="sos")
    try:
        band = sosfiltfilt(sos, x, axis=0).astype("float32")
    except ValueError:  # very short clips cannot satisfy filtfilt padding
        band = sosfilt(sos, x, axis=0).astype("float32")
    retain = 10.0 ** (-max(0.0, reduction_db) / 20.0)
    return x - band * (1.0 - retain)


def _soft_silence_gate(data, samplerate: int, threshold_db: float, floor_db: float):
    """Apply a 10 ms-smoothed gate to silence, avoiding abrupt sample cuts."""
    import numpy as np

    x = _as_2d(data)
    mono = x.mean(axis=1)
    window = max(1, int(samplerate * 0.01))
    envelope = np.sqrt(np.convolve(mono * mono, np.ones(window, dtype="float32") / window, mode="same") + 1e-12)
    threshold = 10.0 ** (threshold_db / 20.0)
    floor_gain = 10.0 ** (floor_db / 20.0)
    target = np.where(envelope < threshold, floor_gain, 1.0).astype("float32")
    smoothing = max(1, int(samplerate * 0.008))
    gain = np.convolve(target, np.ones(smoothing, dtype="float32") / smoothing, mode="same")
    return x * gain[:, None], envelope


def _pause_noise_dbfs(data, envelope, threshold_db: float) -> float:
    import numpy as np

    threshold = 10.0 ** (threshold_db / 20.0)
    mask = envelope < threshold
    if not np.any(mask):
        return -120.0
    rms = float(np.sqrt(np.mean(_as_2d(data)[mask] ** 2)) + 1e-12)
    return float(20.0 * np.log10(rms))


def clean_vocal_chain(
    input_wav: str | Path,
    output_wav: str | Path,
    genre: str | None = None,
    preset: dict[str, float] | None = None,
    prop_decrease: float = 1.0,
) -> dict[str, Any]:
    """Run denoise -> de-ess -> silence gate and save a clean vocal artifact."""
    try:
        import numpy as np

        data, samplerate = sf.read(str(input_wav), always_2d=False)
        values = cleaning_preset(genre)
        values.update(preset or {})
        if _HAS_NR:
            denoised = nr.reduce_noise(y=data, sr=samplerate, prop_decrease=prop_decrease)
            denoise_engine = "noisereduce_v3"
        else:
            denoised = _fallback_clean(data, samplerate, values["highpass_hz"])
            denoise_engine = "fallback_highpass_dc"
        deessed = _de_ess(
            denoised,
            samplerate,
            values["deesser_low_hz"],
            values["deesser_high_hz"],
            values["deesser_db"],
        )
        gated, envelope = _soft_silence_gate(deessed, samplerate, values["gate_db"], values["gate_floor_db"])
        peak = float(np.max(np.abs(gated))) if len(gated) else 0.0
        if peak > 0.98:
            gated = gated * (0.98 / peak)
        target = Path(output_wav)
        target.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(target), gated, samplerate, subtype="PCM_16")
        pause_dbfs = _pause_noise_dbfs(gated, envelope, values["gate_db"])
        return {
            "ok": True,
            "path": str(target),
            "engine": denoise_engine + "+band_deesser+silence_gate",
            "fallback_used": not _HAS_NR,
            "preset": values,
            "pause_noise_dbfs": pause_dbfs,
            "deesser_reduction_db": values["deesser_db"],
            "reason": None if _HAS_NR else "noisereduce not installed; deterministic DC/highpass fallback used",
        }
    except Exception as exc:
        return {"ok": False, "path": "", "reason": f"vocal clean chain failed: {exc}"}


def clean_vocal(input_wav: str, output_wav: str, prop_decrease: float = 1.0):
    """Backward-compatible cleanup API using the default preset."""
    result = clean_vocal_chain(input_wav, output_wav, prop_decrease=prop_decrease)
    if result.get("ok"):
        return result
    try:
        os.makedirs(os.path.dirname(output_wav) or ".", exist_ok=True)
        shutil.copy(input_wav, output_wav)
        result["fallback_copy"] = {"ok": True, "path": output_wav}
    except (OSError, shutil.Error) as error:
        result["fallback_copy"] = {"ok": False, "error": f"{type(error).__name__}: {error}"}
        result["reason"] = f"{result.get('reason', 'vocal clean chain failed')}; raw fallback copy failed: {error}"
    return result
