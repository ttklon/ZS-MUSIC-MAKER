"""
ZS Music Maker — mastering_pro.py (GOD MODE Safe Fallback)
========================================================================
Профессиональный мастеринг-движок с безопасными фоллбеками при
отсутствии тяжелых библиотек (pyloudnorm, pedalboard).
"""

import os
import numpy as np
import soundfile as sf

# Безопасный импорт тяжелых библиотек
try:
    import pyloudnorm as pyln
    HAS_PYLOUDNORM = True
except ImportError:
    HAS_PYLOUDNORM = False

try:
    from pedalboard import (
        Chorus,
        Compressor,
        Distortion,
        HighpassFilter,
        Limiter,
        Pedalboard,
    )
    from pedalboard.io import AudioFile
    HAS_PEDALBOARD = True
except ImportError:
    HAS_PEDALBOARD = False


def process_mastering(input_wav: str, output_wav: str, vocal_path: str = None, target_lufs: float = -14.0):
    """
    Профессиональный мастеринг трека с автоматическими фоллбеками.
    Если передан vocal_path, вокал подмешивается к биту перед мастерингом.
    """
    global HAS_PEDALBOARD, HAS_PYLOUDNORM
    if not os.path.exists(input_wav):
        raise FileNotFoundError(f"Input wav not found: {input_wav}")

    # v26: Сведение вокала и бита если нужно
    if vocal_path and os.path.exists(vocal_path):
        try:
            from pydub import AudioSegment
            beat = AudioSegment.from_file(input_wav)
            vocal = AudioSegment.from_file(vocal_path)
            # Базовое сведение
            combined = beat.overlay(vocal)
            temp_mix = output_wav.replace(".wav", "_temp_mix.wav")
            combined.export(temp_mix, format="wav")
            input_wav = temp_mix
        except Exception as e:
            print(f"[mastering_pro] Mix failed: {e}")

    if HAS_PEDALBOARD:
        try:
            with AudioFile(input_wav) as f:
                audio = f.read(f.frames)
                samplerate = f.samplerate

            board = Pedalboard([
                HighpassFilter(cutoff_frequency_hz=30),
                Distortion(drive_db=2.0),
                Compressor(threshold_db=-18, ratio=2.0, attack_ms=5.0, release_ms=50.0),
                Chorus(rate_hz=0.1, depth=0.1, centre_delay_ms=7.0, feedback=0.0, mix=0.15),
                Limiter(threshold_db=-0.5, release_ms=100.0),
            ])
            mastered = board(audio, samplerate)
            audio_to_norm = mastered.T
        except Exception as e:
            print(f"[mastering_pro] Pedalboard execution error: {e}, falling back to numpy/soundfile")
            HAS_PEDALBOARD = False

    if not HAS_PEDALBOARD:
        audio_data, samplerate = sf.read(input_wav, always_2d=True)
        # audio_data is (frames, channels), convert to (channels, frames) for consistency
        mastered = audio_data.T
        audio_to_norm = audio_data

    # Нормализация громкости
    input_lufs = -20.0
    if HAS_PYLOUDNORM:
        try:
            meter = pyln.Meter(samplerate)
            input_lufs = meter.integrated_loudness(audio_to_norm)
            mastered = pyln.normalize.loudness(audio_to_norm, input_lufs, target_lufs)
            mastered = mastered.T # back to (channels, frames) or (frames, channels)
        except Exception as e:
            print(f"[mastering_pro] pyloudnorm error: {e}, using RMS fallback")
            HAS_PYLOUDNORM = False

    if not HAS_PYLOUDNORM:
        # Простой RMS-фоллбек нормализации
        current_rms = np.sqrt(np.mean(mastered**2)) + 1e-12
        target_rms = 10.0 ** (target_lufs / 20.0)
        gain = target_rms / current_rms
        mastered = mastered * min(gain, 5.0) # ограничение усиления

    # Финальный клиппинг
    mastered = np.clip(mastered, -0.99, 0.99)

    # Если массив канальный, приведем к (frames, channels) для sf.write если нужно,
    # но sf.write принимает (frames, channels). mastered у нас обычно (channels, frames) если от pedalboard.
    if mastered.ndim == 2 and mastered.shape[0] < mastered.shape[1]:
        mastered = mastered.T

    os.makedirs(os.path.dirname(output_wav), exist_ok=True)
    sf.write(output_wav, mastered, samplerate, format="WAV", subtype="PCM_16")

    return {
        "ok": True,
        "path": output_wav,
        "engine": "pedalboard_pro_safe" if HAS_PEDALBOARD else "numpy_rms_safe",
        "input_lufs": round(float(input_lufs), 2),
        "target_lufs": target_lufs,
    }
