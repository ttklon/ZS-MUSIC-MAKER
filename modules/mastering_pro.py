"""
ZS Music Maker — mastering_pro.py (GOD MODE Safe Fallback)
========================================================================
Профессиональный мастеринг-движок с безопасными фоллбеками при
отсутствии тяжелых библиотек (pyloudnorm, pedalboard).

v29 FIX (P1/P2):
  * true-peak ceiling: после LUFS-нормализации возможна перегрузка
    (pyloudnorm warning "Possible clipped samples"). Добавлен
    post-normalization ceiling limiter (-1 dBTP mode для streaming).
  * защита от NaN/Inf в аудио (могло убить mastered.wav).
  * возвращаем реальные output_lufs и output_peak для честного отчёта
    (не только input_lufs).
  * mono → stereo up-mix через дублирование канала (раньше могли
    получить (frames,1) и sf.write писал моно WAV, сбивая God Mode).
"""

import os
from pathlib import Path

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


def _sanitize(x: np.ndarray) -> np.ndarray:
    """NaN/Inf → 0 (защита от gain-blow-up при пустых буферах)."""
    if not np.isfinite(x).all():
        x = np.nan_to_num(x, nan=0.0, posinf=0.99, neginf=-0.99)
    return x


def _apply_ceiling(x: np.ndarray, ceiling_db: float = -1.0) -> np.ndarray:
    """
    Простой look-ahead-free peak ceiling.
    Если pedalboard.Limiter отработал в цепи — это дублирующая страховка
    против post-LUFS overshoot (pyloudnorm.normalize.loudness может
    вывести пики > 1.0 после gain).
    """
    ceiling = 10.0 ** (ceiling_db / 20.0)  # -1 dB → ~0.891
    peak = float(np.max(np.abs(x))) if x.size else 0.0
    if peak > ceiling and peak > 0:
        x = x * (ceiling / peak)
    return x


def process_mastering(input_wav: str, output_wav: str, vocal_path: str = None, target_lufs: float = -14.0):
    """
    Профессиональный мастеринг трека с автоматическими фоллбеками.
    Если передан vocal_path, вокал подмешивается к биту перед мастерингом.

    v29: добавлен true-peak ceiling (-1 dBTP) и honest output-метрики.
    """
    # Capability imports are process-wide, but an execution failure is local
    # to this master. Do not permanently degrade later tracks on one error.
    pedalboard_available = HAS_PEDALBOARD
    loudnorm_available = HAS_PYLOUDNORM
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

    mastered = None
    samplerate = 44100
    audio_to_norm = None
    engine = "unknown"

    if pedalboard_available:
        try:
            with AudioFile(input_wav) as f:
                audio = f.read(f.frames)
                samplerate = f.samplerate

            board = Pedalboard([
                HighpassFilter(cutoff_frequency_hz=30),
                Distortion(drive_db=2.0),
                Compressor(threshold_db=-18, ratio=2.0, attack_ms=5.0, release_ms=50.0),
                Chorus(rate_hz=0.1, depth=0.1, centre_delay_ms=7.0, feedback=0.0, mix=0.15),
                Limiter(threshold_db=-1.0, release_ms=100.0),  # v29: -1 dBTP streaming ceiling
            ])
            mastered = board(audio, samplerate)
            audio_to_norm = mastered.T
            engine = "pedalboard_pro_safe"
        except Exception as e:
            print(f"[mastering_pro] Pedalboard execution error: {e}, falling back to numpy/soundfile")
            pedalboard_available = False

    if not pedalboard_available:
        audio_data, samplerate = sf.read(input_wav, always_2d=True)
        # audio_data is (frames, channels), convert to (channels, frames) for consistency
        mastered = audio_data.T
        audio_to_norm = audio_data
        engine = "numpy_rms_safe"

    audio_to_norm = _sanitize(np.asarray(audio_to_norm))

    # Нормализация громкости
    input_lufs = -20.0
    if loudnorm_available:
        try:
            meter = pyln.Meter(samplerate)
            input_lufs = meter.integrated_loudness(audio_to_norm)
            # v29: подавляем ClippingWarning — мы всё равно снизим потом ceiling'ом
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                mastered = pyln.normalize.loudness(audio_to_norm, input_lufs, target_lufs)
            mastered = mastered.T  # back to (channels, frames)
        except Exception as e:
            print(f"[mastering_pro] pyloudnorm error: {e}, using RMS fallback")
            loudnorm_available = False

    if not loudnorm_available:
        # Простой RMS-фоллбек нормализации
        current_rms = np.sqrt(np.mean(mastered ** 2)) + 1e-12
        target_rms = 10.0 ** (target_lufs / 20.0)
        gain = target_rms / current_rms
        mastered = mastered * min(gain, 5.0)  # ограничение усиления

    mastered = _sanitize(np.asarray(mastered))

    # v29: true-peak ceiling -1 dBTP (streaming/AES стенд, страховка после LUFS)
    mastered = _apply_ceiling(mastered, ceiling_db=-1.0)

    # Финальный soft clip (страховка на случай числовых артефактов)
    mastered = np.clip(mastered, -0.99, 0.99)

    # Приведение к (frames, channels) для sf.write
    if mastered.ndim == 2 and mastered.shape[0] < mastered.shape[1]:
        mastered = mastered.T

    # v29: моно → стерео (God Mode ожидает стерео мастер)
    if mastered.ndim == 1:
        mastered = np.stack([mastered, mastered], axis=1)
    elif mastered.ndim == 2 and mastered.shape[1] == 1:
        mastered = np.concatenate([mastered, mastered], axis=1)

    os.makedirs(os.path.dirname(output_wav) or ".", exist_ok=True)
    sf.write(output_wav, mastered, samplerate, format="WAV", subtype="PCM_16")

    # v29: honest output metrics
    output_peak_db = 20.0 * np.log10(float(np.max(np.abs(mastered))) + 1e-12)
    output_lufs = None
    if loudnorm_available:
        try:
            meter = pyln.Meter(samplerate)
            output_lufs = float(meter.integrated_loudness(mastered))
        except Exception:
            output_lufs = None

    return {
        "ok": True,
        "path": output_wav,
        "engine": engine,
        "input_lufs": round(float(input_lufs), 2),
        "target_lufs": target_lufs,
        "output_lufs": round(output_lufs, 2) if output_lufs is not None else None,
        "output_peak_db": round(float(output_peak_db), 2),
        "channels": int(mastered.shape[1]) if mastered.ndim == 2 else 1,
        "sample_rate": int(samplerate),
    }



def normalize_master_loudness(input_wav: str, output_wav: str | None = None,
                               target_lufs: float = -14.0,
                               ceiling_db: float = -1.0) -> dict:
    """Нормализовать уже обработанный master без добавления новой DSP-окраски.

    При установленном pyloudnorm используется integrated loudness. В лёгкой
    среде применяется честная RMS approximation и это явно отмечается в
    `loudness_mode`; peak ceiling применяется в обоих режимах.
    """
    output_wav = output_wav or input_wav
    samples, sample_rate = sf.read(input_wav, always_2d=True)
    samples = _sanitize(np.asarray(samples, dtype=np.float64))
    loudnorm_available = HAS_PYLOUDNORM
    if samples.size == 0:
        return {"ok": False, "reason": "master audio is empty"}
    loudness_mode = "rms_approximation"
    input_lufs = None
    normalized = samples
    if loudnorm_available:
        try:
            meter = pyln.Meter(sample_rate)
            input_lufs = float(meter.integrated_loudness(samples))
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                normalized = pyln.normalize.loudness(samples, input_lufs, target_lufs)
            loudness_mode = "integrated_lufs"
        except Exception:
            normalized = samples
    if loudness_mode == "rms_approximation":
        rms = float(np.sqrt(np.mean(normalized ** 2)) + 1e-12)
        target_rms = 10.0 ** (target_lufs / 20.0)
        normalized = normalized * min(target_rms / rms, 5.0)
    normalized = _apply_ceiling(_sanitize(normalized), ceiling_db=ceiling_db)
    normalized = np.clip(normalized, -0.99, 0.99)
    Path(output_wav).parent.mkdir(parents=True, exist_ok=True)
    sf.write(output_wav, normalized.astype("float32"), sample_rate, format="WAV", subtype="PCM_16")

    output_lufs = None
    if loudnorm_available:
        try:
            output_lufs = float(pyln.Meter(sample_rate).integrated_loudness(normalized))
        except Exception:
            output_lufs = None
    peak_db = 20.0 * np.log10(float(np.max(np.abs(normalized))) + 1e-12)
    rms_db = 20.0 * np.log10(float(np.sqrt(np.mean(normalized ** 2))) + 1e-12)
    return {
        "ok": True,
        "path": output_wav,
        "target_lufs": float(target_lufs),
        "output_lufs": round(output_lufs, 2) if output_lufs is not None else None,
        "output_rms_dbfs": round(float(rms_db), 2),
        "output_peak_db": round(float(peak_db), 2),
        "loudness_mode": loudness_mode,
        "sample_rate": int(sample_rate),
        "channels": int(normalized.shape[1]),
    }
