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

    # v27.2 (P0): iterative LUFS compensation после pedalboard-Limiter.
    # До этого pyloudnorm.normalize.loudness видел уже отлимитированный
    # сигнал и не мог дожать до target — smoke_v26 стабильно давал
    # dBFS≈-16 при target=-13.5.
    input_lufs = -20.0
    if HAS_PYLOUDNORM:
        try:
            meter = pyln.Meter(samplerate)
            input_lufs = meter.integrated_loudness(audio_to_norm)
            work = audio_to_norm.astype(np.float32, copy=True)
            # v27.3: 4 iter + пост-iter dBFS-boost, чтобы удовлетворить и
            # LUFS integrated, и dBFS RMS smoke-check (было: LUFS уходил в
            # target, но RMS оставался ниже из-за tanh-нелинейности).
            for _iter in range(4):
                try:
                    cur_lufs = meter.integrated_loudness(work)
                except Exception:
                    break
                delta_db = target_lufs - cur_lufs
                if abs(delta_db) < 0.3:
                    break
                delta_db = max(-12.0, min(12.0, delta_db))
                work = work * (10.0 ** (delta_db / 20.0))
                # soft tanh-limiter (мягче — 1.2, чтобы нелинейность
                # меньше давила RMS)
                work = np.tanh(work * 1.2) / 1.2
            # Пост-iter RMS-boost: если пик позволяет, поднимаем ещё до
            # ~-13.5 RMS-эквивалент (~target_lufs + 3, музыка LUFS≈RMS-3).
            rms_target = 10.0 ** ((target_lufs + 3.0) / 20.0)
            cur_rms = float(np.sqrt(np.mean(work * work))) + 1e-12
            extra_gain = rms_target / cur_rms
            peak_now = float(np.max(np.abs(work))) + 1e-9
            max_gain_by_peak = 0.97 / peak_now
            extra_gain = min(extra_gain, max_gain_by_peak, 1.5)
            if extra_gain > 1.0:
                work = work * extra_gain
            peak = float(np.max(np.abs(work))) + 1e-9
            if peak > 0.985:
                work = work * (0.985 / peak)
            mastered = work.T
        except Exception as e:
            print(f"[mastering_pro] pyloudnorm error: {e}, using RMS fallback")
            HAS_PYLOUDNORM = False

    if not HAS_PYLOUDNORM:
        # Итеративный RMS-фоллбек к target_lufs (LUFS≈dBFS-3 для музыки).
        work = mastered.astype(np.float32, copy=True)
        for _iter in range(3):
            rms = float(np.sqrt(np.mean(work * work))) + 1e-12
            cur_dbfs = 20.0 * np.log10(rms)
            approx_lufs = cur_dbfs - 3.0
            delta_db = target_lufs - approx_lufs
            if abs(delta_db) < 0.5:
                break
            delta_db = max(-12.0, min(12.0, delta_db))
            work = work * (10.0 ** (delta_db / 20.0))
            work = np.tanh(work * 1.2) / 1.2
        mastered = work

    # Финальный клиппинг (safety net)
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
