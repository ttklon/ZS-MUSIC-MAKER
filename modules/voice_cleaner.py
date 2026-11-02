"""Deterministic vocal cleanup: denoise, conservative de-essing and silence gating."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

import soundfile as sf

DENOISE_MAX_REDUCTION_DB = 12.0
DENOISE_FRAME = 1024
DENOISE_HOP = 256

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


def _remove_rumble(data, samplerate: int, highpass_hz: float):
    """Убрать DC и инфраниз, не задевая воздух вокала.

    Однополюсный хайпасс через `lfilter` (рекурсия, но вектором): пошаговый
    цикл на 4-минутном вокале — это секунды впустую.
    """
    import numpy as np
    from scipy.signal import lfilter

    x = _as_2d(data)
    x = x - np.mean(x, axis=0, keepdims=True)
    rc = 1.0 / (2.0 * np.pi * max(20.0, highpass_hz))
    coefficient = rc / (rc + 1.0 / float(samplerate))
    output = lfilter([coefficient, -coefficient], [1.0, -coefficient], x, axis=0)
    return output.astype("float32")


def _stft(padded, frame: int, hop: int):
    import numpy as np

    window = np.hanning(frame).astype(np.float64)
    count = 1 + (padded.shape[0] - frame) // hop
    index = np.arange(frame)[None, :] + hop * np.arange(count)[:, None]
    return padded[index] * window, window, count


def _spectral_denoise(data, samplerate: int, prop_decrease: float = 1.0):
    """Спектральные воротца против шипения — детерминированно, на numpy.

    Профиль шума берётся из самых тихих 20 % кадров (средняя мощность по
    каждому бину), а не «на слух»: так шипение убирается, а устойчивые тоны
    голоса (и сибилянты) остаются, потому что они заметно выше профиля.
    Подавление ограничено `DENOISE_MAX_REDUCTION_DB`, окна перекрываются с
    нормировкой суммы — уровень и длина не меняются.

    Ограничение честно: если в записи вообще нет паузы, а шум стационарен,
    отличить его от тона по самому сигналу невозможно — для вокала это
    нереальный случай (дыхание и паузы есть всегда).
    """
    import numpy as np
    from scipy.ndimage import uniform_filter1d

    x = _as_2d(data).astype(np.float64)
    n = x.shape[0]
    frame, hop = DENOISE_FRAME, DENOISE_HOP
    if n < frame * 2:
        return x.astype("float32"), {"applied": False, "reason": "signal shorter than 2 frames"}
    pad = frame
    padded = np.pad(x, ((pad, pad + frame), (0, 0)), mode="edge")
    out = np.zeros_like(padded)
    weight = np.zeros(padded.shape[0])
    # нижняя граница амплитудного усиления: -12 дБ, а не «в ноль»
    gain_floor = 10.0 ** (-float(DENOISE_MAX_REDUCTION_DB) / 20.0)
    reduction_sum = 0.0
    active_frames = 0.0
    frames_total = 0
    for channel in range(x.shape[1]):
        frames, window, count = _stft(padded[:, channel], frame, hop)
        power = np.abs(np.fft.rfft(frames, axis=1)) ** 2
        # профиль шума = средняя мощность самых тихих 20 % кадров:
        # процентиль по каждому бину занижен (нижний хвост флуктуаций),
        # и шипение проходило бы насквозь
        frame_energy = power.sum(axis=1)
        quiet = frame_energy <= np.percentile(frame_energy, 20)
        noise = power[quiet].mean(axis=0)
        # сглаживание профиля по частоте: одиночные пики не считаем шумом
        noise = uniform_filter1d(noise, size=5, mode="nearest")
        gain = 1.0 - float(prop_decrease) * np.minimum(1.0, noise / np.maximum(power, 1e-20))
        # сглаживание маски по времени, чтобы не было «музыкального» шипения
        gain = uniform_filter1d(gain, size=3, axis=0, mode="nearest")
        gain = np.clip(gain, gain_floor, 1.0)
        gain_db = 20.0 * np.log10(gain)
        reduction_sum += float(np.mean(gain_db))
        active_frames += float(np.mean(gain_db < -0.5) * 100.0)
        frames_total += 1
        spec = np.fft.rfft(frames, axis=1) * gain
        restored = np.fft.irfft(spec, frame, axis=1) * window
        for index in range(count):
            start = index * hop
            out[start : start + frame, channel] += restored[index]
            if channel == 0:
                weight[start : start + frame] += window**2
    safe = weight > 1e-9
    for channel in range(x.shape[1]):
        out[safe, channel] = out[safe, channel] / weight[safe]
    result = out[pad : pad + n].astype("float32")
    report = {
        "applied": True,
        "engine": "numpy_spectral_gate",
        "max_reduction_db": round(float(DENOISE_MAX_REDUCTION_DB), 2),
        "mean_reduction_db": round(reduction_sum / max(1, frames_total), 2),
        "reduction_active_pct": round(active_frames / max(1, frames_total), 1),
        "length_preserved": result.shape[0] == n,
    }
    return result, report


def _de_ess(data, samplerate: int, low_hz: float, high_hz: float, reduction_db: float):
    """Де-эссинг через единственную реализацию — `modules.vocal_fx.desser`.

    Статический срез полосы глушит воздух там, где сибилянтов нет, поэтому
    чистящая стадия использует тот же динамический де-эссер, что и вокальная
    цепочка, только с пределом подавления из пресета очистки.
    """
    import numpy as np

    from modules.vocal_fx.desser import dynamic_deess

    try:
        processed, _report = dynamic_deess(
            np.asarray(data, dtype="float64"), samplerate, reduction_db=float(reduction_db)
        )
        return processed.astype("float32")
    except Exception:  # noqa: BLE001 - очистка не должна падать из-за де-эссера
        return _as_2d(data)


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
        denoised, denoise_report = _spectral_denoise(
            _remove_rumble(data, samplerate, values["highpass_hz"]),
            samplerate,
            prop_decrease=prop_decrease,
        )
        denoise_engine = denoise_report["engine"] if denoise_report["applied"] else "highpass_only"
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
        sf.write(str(target), gated, samplerate, subtype="FLOAT")
        pause_dbfs = _pause_noise_dbfs(gated, envelope, values["gate_db"])
        return {
            "ok": True,
            "path": str(target),
            "engine": denoise_engine + "+dynamic_deesser+silence_gate",
            "fallback_used": not denoise_report["applied"],
            "denoise": denoise_report,
            "preset": values,
            "pause_noise_dbfs": pause_dbfs,
            "deesser_reduction_db": values["deesser_db"],
            "reason": denoise_report.get("reason"),
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
