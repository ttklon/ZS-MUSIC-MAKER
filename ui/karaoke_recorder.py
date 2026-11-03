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
import uuid
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


def _select_device_format(sd, preferred_sr: int, backing_channels: int) -> tuple[int, int, bool]:
    """Probe the default input/output devices; never silently drop requested playback."""
    if not hasattr(sd, "check_input_settings") or (backing_channels and not hasattr(sd, "check_output_settings")):
        return preferred_sr, backing_channels, False
    candidates = [preferred_sr]
    if hasattr(sd, "query_devices"):
        for kind in (("input", "output") if backing_channels else ("input",)):
            try:
                value = sd.query_devices(kind=kind).get("default_samplerate")
                if value is not None:
                    candidates.append(int(round(float(value))))
            except Exception:
                logging.getLogger(__name__).debug("default %s device not reported", kind, exc_info=True)
    candidates.extend((48000, 44100, 32000))
    input_rates = []
    for rate in dict.fromkeys(candidates):
        if not 8000 <= rate <= 192000:
            continue
        try:
            sd.check_input_settings(channels=1, samplerate=rate, dtype="float32")
            input_rates.append(rate)
        except Exception:
            logging.getLogger(__name__).debug("input rate %s unavailable", rate, exc_info=True)
    if input_rates and not backing_channels:
        return input_rates[0], 0, True
    # Preserve stereo when any mutually supported rate can do it; only then try mono.
    for channels in dict.fromkeys((backing_channels, 1)):
        for rate in input_rates:
            try:
                sd.check_output_settings(channels=channels, samplerate=rate, dtype="float32")
                return rate, channels, True
            except Exception:
                logging.getLogger(__name__).debug("output format unavailable", exc_info=True)
    raise RuntimeError("No compatible input/output sample rate; check default devices and full-duplex support")


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
    except (ImportError, OSError) as exc:
        return {"error": f"audio recording backend unavailable: {type(exc).__name__}: {exc}"}

    try:
        if not 0 < float(duration_sec) <= 600 or not 8000 <= int(sr) <= 192000:
            raise ValueError("duration must be 0–600 seconds and sample rate 8–192 kHz")
        backing = None
        backing_sr = None
        channels = 0
        if backing_path:
            path = Path(backing_path)
            if not path.is_file():
                raise FileNotFoundError(f"backing track not found: {backing_path}")
            with sf.SoundFile(str(path)) as source:
                backing_sr = source.samplerate
                channels = source.channels
                if channels not in (1, 2) or not 8000 <= backing_sr <= 192000:
                    raise ValueError("backing must be mono/stereo and 8–192 kHz")
        actual_sr, output_channels, format_checked = _select_device_format(sd, int(sr), channels)
        frames = int(float(duration_sec) * actual_sr)
        if frames < 1:
            raise ValueError("recording is shorter than one sample")
        short_backing = False
        if backing_path:
            with sf.SoundFile(str(path)) as source:
                if source.samplerate != backing_sr or source.channels != channels:
                    raise ValueError("backing format changed before recording")
                wanted = min(len(source), int(np.ceil(frames * backing_sr / actual_sr)) + 4)
                backing = source.read(wanted, dtype="float32", always_2d=True)
            if not len(backing) or not np.isfinite(backing).all():
                raise ValueError("backing track is empty or invalid")
            if backing_sr != actual_sr:
                from math import gcd
                from scipy.signal import resample_poly

                factor = gcd(backing_sr, actual_sr)
                backing = resample_poly(backing, actual_sr // factor, backing_sr // factor, axis=0).astype("float32")
            if output_channels == 1 and backing.shape[1] == 2:
                backing = backing.mean(axis=1, keepdims=True)
            # Pad with silence instead of looping unexpectedly.
            playback = np.zeros((frames, output_channels), dtype="float32")
            n = min(frames, len(backing))
            playback[:n] = backing[:n]
            short_backing = n < frames
            audio = sd.playrec(playback, samplerate=actual_sr, channels=1, dtype="float32", blocking=True)
        else:
            audio = sd.rec(frames, samplerate=actual_sr, channels=1, dtype="float32")
            sd.wait()
        audio = np.asarray(audio, dtype="float32").reshape(-1)
        if len(audio) != frames or not np.isfinite(audio).all():
            raise ValueError("microphone returned incomplete or invalid audio")
        peak = float(np.max(np.abs(audio)))
        if peak < 1e-5:
            raise ValueError("microphone recording is silent; check input device and level")
        safe_style = re.sub(r"[^\w-]", "_", style)[:40] or "voice"
        ts = time.time_ns()
        VAULT.mkdir(parents=True, exist_ok=True)
        out = VAULT / f"rec_{ts}_{uuid.uuid4().hex}_{safe_style}.wav"
        # Exclusive, lossless float WAV: never overwrite another take or quantize it.
        try:
            with out.open("xb") as target:
                sf.write(target, audio, actual_sr, format="WAV", subtype="FLOAT")
        except Exception as exc:
            raise RuntimeError(f"take could not be fully saved; partial file may remain at {out}: {exc}") from exc
    except Exception as exc:
        return {"error": f"recording failed: {type(exc).__name__}: {exc}"}

    # A saved take remains usable even if indexing fails; report the distinction.
    warning = ""
    try:
        from modules.voice_convert import add_recording

        entry = add_recording(str(out), {"style": style, "text": text,
                                        "duration_sec": len(audio) / actual_sr, "timestamp": ts / 1e9})
        if entry.get("error"):
            warning = f"Recording saved but Voice Vault indexing failed: {entry['error']}"
    except Exception as exc:
        warning = f"Recording saved but Voice Vault indexing failed: {type(exc).__name__}: {exc}"
        logging.getLogger(__name__).warning(warning)
    if actual_sr != int(sr):
        warning = (warning + " " if warning else "") + f"Device sample rate selected: {actual_sr} Hz instead of {int(sr)} Hz."
    if backing_path and channels == 2 and output_channels == 1:
        warning = (warning + " " if warning else "") + "Stereo backing was downmixed to mono for the output device."
    if short_backing:
        warning = (warning + " " if warning else "") + "Backing ended before recording; remaining playback was silence."
    if peak >= 0.98:
        warning = (warning + " " if warning else "") + "Recording may be clipped; lower microphone gain."
    return {"ok": True, "path": str(out), "style": style, "duration_sec": len(audio) / actual_sr, "sample_rate": actual_sr,
            "backing_used": bool(backing_path), "playback_channels": output_channels,
            "device_format_checked": format_checked, "backing_shorter": short_backing,
            "peak": peak, "warning": warning}


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
