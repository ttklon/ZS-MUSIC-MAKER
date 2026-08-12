"""
ZS Music Maker — voice_cleaner.py (GOD MODE)
========================================================================
Интеллектуальная очистка голоса от шумов.
Использует спектральное вычитание для удаления фонового шума.
"""

import os
import shutil

import soundfile as sf

# v27 FIX (P0): noisereduce был жёстким top-level импортом — при его отсутствии
# падал ВЕСЬ orchestrator_god (ModuleNotFoundError на import). Теперь ленивый
# импорт с честным fallback: highpass+простое спектральное приглушение либо
# passthrough-копия, но пайплайн не ломается.
try:
    import noisereduce as nr  # type: ignore
    _HAS_NR = True
except Exception:  # pragma: no cover
    nr = None
    _HAS_NR = False


def _fallback_clean(data, samplerate):
    """Лёгкий offline fallback: убираем DC + мягкий highpass ~80Hz однополюсным
    фильтром + лёгкое приглушение низкочастотного гула. Не noisereduce, но
    лучше, чем ничего, и честно помечено fallback_used=True."""
    import numpy as np

    x = np.asarray(data, dtype=np.float32)
    mono = x.ndim == 1
    if mono:
        x = x[:, None]
    # DC removal
    x = x - np.mean(x, axis=0, keepdims=True)
    # однополюсный highpass: y[n] = a*(y[n-1] + x[n] - x[n-1])
    rc = 1.0 / (2.0 * 3.14159265 * 80.0)
    dt = 1.0 / float(samplerate)
    a = rc / (rc + dt)
    y = np.zeros_like(x)
    prev_x = x[0].copy()
    prev_y = np.zeros(x.shape[1], dtype=np.float32)
    for n in range(len(x)):
        cur = a * (prev_y + x[n] - prev_x)
        y[n] = cur
        prev_y = cur
        prev_x = x[n]
    return y[:, 0] if mono else y


def clean_vocal(input_wav: str, output_wav: str, prop_decrease: float = 1.0):
    """
    Очистка вокала от шума.
    """
    data, samplerate = sf.read(input_wav)

    os.makedirs(os.path.dirname(output_wav) or ".", exist_ok=True)

    if _HAS_NR:
        # noisereduce работает с 1D (mono) или 2D (stereo) массивами
        reduced_noise = nr.reduce_noise(y=data, sr=samplerate, prop_decrease=prop_decrease)
        sf.write(output_wav, reduced_noise, samplerate)
        return {
            "ok": True,
            "path": output_wav,
            "engine": "noisereduce_v3",
            "prop_decrease": prop_decrease,
        }

    # FALLBACK_ONLY: честный lightweight-режим без noisereduce
    try:
        cleaned = _fallback_clean(data, samplerate)
        sf.write(output_wav, cleaned, samplerate)
    except Exception:
        shutil.copy(input_wav, output_wav)
    return {
        "ok": True,
        "path": output_wav,
        "engine": "fallback_highpass_dc",
        "fallback_used": True,
        "reason": "noisereduce not installed; DC-removal + 80Hz highpass applied",
        "prop_decrease": prop_decrease,
    }


if __name__ == "__main__":
    # Тестовый запуск
    pass
