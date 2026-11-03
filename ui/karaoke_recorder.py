"""
[v7] karaoke_recorder v4 — караоке-запись с 8 стилями и прогрессом покрытия.

Возможности:
  • Синхронное воспроизведение выбранного бита при записи через sounddevice
  • Сохранение в voice_vault/ с меткой стиля и диагностикой индекса
"""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VAULT = ROOT / "voice_vault"
VAULT.mkdir(parents=True, exist_ok=True)


def build_metronome(bpm: int, duration_sec: int = 8, sr: int = 44100) -> str:
    """Генерирует WAV с метрономом на BPM."""
    try:
        import numpy as np
        import soundfile as sf

        n = int(sr * duration_sec)
        y = np.zeros(n, dtype="float32")
        beat_samples = int(sr * 60.0 / bpm)
        click_dur = int(0.02 * sr)
        # клик — короткий треугольник
        for i in range(0, n, beat_samples):
            if i + click_dur >= n:
                break
            t = np.linspace(0, 1, click_dur)
            click = np.sin(2 * np.pi * 1200 * t) * np.exp(-t * 30) * 0.5
            y[i : i + click_dur] += click.astype("float32")
        out = str(VAULT / f"_metronome_{bpm}.wav")
        sf.write(out, y, sr)
        return out
    except Exception as e:
        print(f"[karaoke.metronome] {e}")
        return ""


def record_with_backing(
    backing_path: str,
    duration_sec: int = 30,
    style: str = "conversational",
    text: str = "",
    sr: int = 44100,
) -> dict:
    """
    Записывает голос с параллельным проигрыванием бита.
    Автоматически кладёт в voice_vault/ с меткой стиля.
    """
    try:
        import numpy as np
        import sounddevice as sd
        import soundfile as sf
    except ImportError:
        return {"error": "sounddevice не установлен"}

    try:
        frames = int(duration_sec * sr)
        if frames <= 0 or frames > 600 * sr:
            raise ValueError("duration must be between 0 and 600 seconds")
        if backing_path:
            path = Path(backing_path)
            if not path.is_file():
                raise FileNotFoundError(f"backing track not found: {backing_path}")
            with sf.SoundFile(str(path)) as source:
                backing_sr = source.samplerate
                wanted = min(len(source), int(np.ceil(frames * backing_sr / sr)) + 4)
                backing = source.read(wanted, dtype="float32", always_2d=True)
            if not len(backing) or not np.isfinite(backing).all():
                raise ValueError("backing track is empty or invalid")
            if backing_sr != sr:
                from math import gcd
                from scipy.signal import resample_poly

                factor = gcd(backing_sr, sr)
                backing = resample_poly(backing, sr // factor, backing_sr // factor, axis=0).astype("float32")
            if backing.shape[1] > 2:
                backing = backing[:, :2]
            # Pad with silence instead of looping unexpectedly.
            playback = np.zeros((frames, backing.shape[1]), dtype="float32")
            n = min(frames, len(backing))
            playback[:n] = backing[:n]
            audio = sd.playrec(playback, samplerate=sr, channels=1, dtype="float32", blocking=True)
        else:
            audio = sd.rec(frames, samplerate=sr, channels=1, dtype="float32")
            sd.wait()
        audio = np.asarray(audio, dtype="float32").reshape(-1)
        if len(audio) != frames or not np.isfinite(audio).all():
            raise ValueError("microphone returned incomplete or invalid audio")
        peak = float(np.max(np.abs(audio)))
        if peak < 1e-5:
            raise ValueError("microphone recording is silent; check input device and level")
        safe_style = re.sub(r"[^\w-]", "_", style)[:40] or "voice"
        ts = time.time_ns()
        out = VAULT / f"rec_{ts}_{safe_style}.wav"
        sf.write(str(out), audio, sr)
    except Exception as exc:
        return {"error": f"recording failed: {type(exc).__name__}: {exc}"}

    # A saved take remains usable even if indexing fails; report the distinction.
    warning = ""
    try:
        from modules.voice_convert import add_recording

        entry = add_recording(str(out), {"style": style, "text": text,
                                        "duration_sec": len(audio) / sr, "timestamp": ts / 1e9})
        if entry.get("error"):
            warning = f"Recording saved but Voice Vault indexing failed: {entry['error']}"
    except Exception as exc:
        warning = f"Recording saved but Voice Vault indexing failed: {type(exc).__name__}: {exc}"
        logging.getLogger(__name__).warning(warning)
    if peak >= 0.98:
        warning = (warning + " " if warning else "") + "Recording may be clipped; lower microphone gain."
    return {"ok": True, "path": str(out), "style": style, "duration_sec": len(audio) / sr,
            "backing_used": bool(backing_path), "peak": peak, "warning": warning}


def karaoke_ui(
    phrase: str,
    bpm: int = 120,
    style: str = "conversational",
    beat_path: str | None = None,
) -> dict:
    """
    Заглушка для интеграции с v5 Gradio.
    В v7 Wizard использует прямо record_with_backing().
    """
    return {
        "phrase": phrase,
        "bpm": bpm,
        "style": style,
        "hint": "Слушай бит в наушниках, читай фразу, жми запись.",
    }


def get_progress() -> dict:
    """Прогресс по всем 8 стилям — для дашборда."""
    try:
        from modules.voice_convert import vault_summary

        return vault_summary()
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print(json.dumps(get_progress(), ensure_ascii=False, indent=2))
    print("Метроном для BPM=140:", build_metronome(140, duration_sec=4))
