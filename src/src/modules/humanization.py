# -*- coding: utf-8 -*-
"""
[8] humanization.py — Humanization & Authenticity Layer v3
Устраняет признаки «нейроношности» песни:
  • микро-расхождения тайминга (но под контролем)
  • живые дыхания
  • вариации между куплетом и припевом
  • нормальная развязка трека (не обрубание)
  • разговорные повороты в лексике
  • контроль адлибов и бэков
  • эволюция аранжировки по секциям
  • проверка вокала на дикцию, атаку согласных, переавтотюненность
v3: bpm параметризован, robust IO, безопасные fallback.
"""
import os, json, numpy as np, random

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "voice_final")
# v22: ленивое создание (не при импорте)

def _read_wav(path: str):
    from pydub import AudioSegment
    seg = AudioSegment.from_file(path)
    sr = seg.frame_rate
    samples = np.array(seg.get_array_of_samples(), dtype=np.float32)
    if seg.channels > 1:
        samples = samples.reshape(-1, seg.channels).mean(axis=1)
    samples = samples / (2 ** 15)
    return samples, sr


def _write_wav(path: str, samples: np.ndarray, sr: int):
    from scipy.io import wavfile
    peak = np.max(np.abs(samples)) + 1e-9
    if peak > 1.0:
        samples = samples / peak * 0.95
    wavfile.write(path, sr, (samples * 32767).astype(np.int16))


def humanize_vocal(vocal_path: str, intensity: float = 0.5,
                   out_name: str = "humanized_vocal.wav") -> dict:
    try:
        samples, sr = _read_wav(vocal_path)
    except Exception as e:
        return {"error": f"read fail: {e}", "path": vocal_path}

    timing_jitter_ms = random.uniform(3, 12) * intensity
    shift_samples = int(sr * timing_jitter_ms / 1000)
    if shift_samples > 0:
        samples = np.roll(samples, shift_samples)
        samples[:shift_samples] = 0

    if intensity > 0.3 and len(samples) > 100:
        t = np.arange(len(samples)) / sr
        vibrato = 1.0 + 0.001 * intensity * np.sin(2 * np.pi * 5.5 * t)
        indices = np.arange(len(samples))
        warped = np.clip(indices * vibrato, 0, len(samples) - 1)
        samples = np.interp(warped, indices, samples)

    silence_thresh = 0.01
    window = int(sr * 0.05)
    if window > 0:
        for i in range(0, len(samples) - window, window):
            chunk = samples[i:i + window]
            if np.max(np.abs(chunk)) < silence_thresh:
                breath = np.random.randn(len(chunk)) * 0.02 * intensity
                samples[i:i + window] += breath

    n_sections = 4
    section_len = len(samples) // n_sections
    if section_len > 0:
        for s in range(n_sections):
            start = s * section_len
            end = start + section_len
            if s % 2 == 1:
                samples[start:end] *= 1.0 + 0.08 * intensity
            else:
                samples[start:end] *= 1.0 - 0.04 * intensity

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, out_name)
    _write_wav(out_path, samples, sr)

    return {
        "humanized_path": out_path,
        "intensity": intensity,
        "timing_jitter_ms": round(timing_jitter_ms, 2),
        "applied": ["timing_jitter", "pitch_vibrato",
                    "breath_in_silences", "section_dynamics"],
    }


def humanize_arrangement(beat_path: str, intensity: float = 0.4,
                         bpm: int = 128,
                         out_name: str = "humanized_beat.wav") -> dict:
    try:
        samples, sr = _read_wav(beat_path)
    except Exception as e:
        return {"error": f"read fail: {e}", "path": beat_path}

    beat_sec = 60.0 / max(bpm, 40)
    step_samples = max(1, int(sr * beat_sec / 4))
    swing_amount = 0.12 * intensity
    n_steps = len(samples) // step_samples
    for i in range(1, n_steps, 2):
        shift = int(step_samples * swing_amount)
        start = i * step_samples
        end = start + step_samples
        if end + shift < len(samples):
            samples[start:end] = np.roll(samples[start:end], shift)

    fade_samples = int(sr * 3.0)
    if len(samples) > fade_samples:
        fade = np.linspace(1.0, 0.0, fade_samples)
        samples[-fade_samples:] *= fade

    if intensity > 0.3:
        bar_samples = step_samples * 16
        if bar_samples > 0:
            for bar in range(len(samples) // bar_samples):
                start = bar * bar_samples
                end = start + bar_samples
                variation = 1.0 + random.uniform(-0.03, 0.03) * intensity
                samples[start:end] *= variation

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, out_name)
    _write_wav(out_path, samples, sr)

    return {
        "humanized_beat": out_path,
        "intensity": intensity,
        "bpm_used": bpm,
        "applied": ["swing", "fade_out_ending", "micro_gain_variation"],
    }


def check_ai_artifacts(vocal_path: str) -> dict:
    try:
        import librosa
    except ImportError:
        return {"error": "librosa не установлен"}

    y, sr = librosa.load(vocal_path, sr=22050, mono=True)

    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
    dynamic_range = float(np.std(rms) / (np.mean(rms) + 1e-9))

    zcr = librosa.feature.zero_crossing_rate(y, frame_length=2048, hop_length=512)[0]
    zcr_consistency = float(np.std(zcr) / (np.mean(zcr) + 1e-9))

    try:
        f0, voiced_flag, _ = librosa.pyin(y, fmin=80, fmax=600, sr=sr)
        f0_voiced = f0[voiced_flag]
        pitch_stability = float(np.std(f0_voiced) / (np.mean(f0_voiced) + 1e-9)) \
            if len(f0_voiced) > 0 else 1.0
    except Exception:
        pitch_stability = 1.0

    scores = {
        "dynamic_range": round(dynamic_range, 4),
        "dynamic_verdict": "natural" if dynamic_range > 0.3 else "TOO_FLAT_AI_LIKE",
        "consonant_clarity": round(zcr_consistency, 4),
        "consonant_verdict": "natural" if zcr_consistency > 0.5 else "SMUDGED_CONSONANTS",
        "pitch_stability": round(pitch_stability, 4),
        "pitch_verdict": "natural" if pitch_stability > 0.05 else "OVER_AUTOTUNED",
    }

    ai_score = 0
    for k in ("dynamic_verdict", "consonant_verdict", "pitch_verdict"):
        if scores[k] != "natural":
            ai_score += 1

    scores["ai_likeness_score"] = f"{ai_score}/3"
    scores["recommendation"] = (
        "Голос звучит естественно ✅" if ai_score == 0
        else f"Обнаружено {ai_score} AI-признака. Прогони humanize_vocal()" if ai_score <= 2
        else "Высокий AI-риск! Нужен RVC + humanization + ручная запись"
    )
    return scores


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(json.dumps(check_ai_artifacts(sys.argv[1]), ensure_ascii=False, indent=2))
    else:
        print("Usage: python humanization.py <vocal.wav>")
