# -*- coding: utf-8 -*-
"""
[v7] karaoke_recorder v4 — караоке-запись с 8 стилями и прогрессом покрытия.

Возможности:
  • Показ фразы с подсветкой слова (по времени)
  • Проигрывание бита в наушниках при записи (Pro mode)
  • Метроном по BPM
  • Автосохранение в voice_vault/ с меткой стиля
  • Прогресс: сколько записей по каждому стилю, покрытие фонем
"""
from __future__ import annotations
import os, time, json, math, wave
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
VAULT = ROOT / "voice_vault"
VAULT.mkdir(parents=True, exist_ok=True)


def build_metronome(bpm: int, duration_sec: int = 8, sr: int = 44100) -> str:
    """Генерирует WAV с метрономом на BPM."""
    try:
        import numpy as np, soundfile as sf
        n = int(sr * duration_sec)
        y = np.zeros(n, dtype="float32")
        beat_samples = int(sr * 60.0 / bpm)
        click_dur = int(0.02 * sr)
        # клик — короткий треугольник
        for i in range(0, n, beat_samples):
            if i + click_dur >= n: break
            t = np.linspace(0, 1, click_dur)
            click = np.sin(2*np.pi*1200*t) * np.exp(-t*30) * 0.5
            y[i:i+click_dur] += click.astype("float32")
        out = str(VAULT / f"_metronome_{bpm}.wav")
        sf.write(out, y, sr)
        return out
    except Exception as e:
        print(f"[karaoke.metronome] {e}")
        return ""


def play_backing_track(track_path: str, in_headphones: bool = True) -> bool:
    """
    Стартует проигрывание бита в наушниках. На Windows — через winsound
    (playAsync), на других системах — через subprocess.
    """
    if not track_path or not os.path.exists(track_path):
        return False
    try:
        import platform
        if platform.system() == "Windows":
            import winsound
            winsound.PlaySound(track_path,
                               winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
        else:
            import subprocess
            subprocess.Popen(["aplay", track_path], stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        print(f"[karaoke.play_backing_track] {e}")
        return False


def record_with_backing(backing_path: str, duration_sec: int = 30,
                        style: str = "conversational", text: str = "",
                        sr: int = 44100) -> dict:
    """
    Записывает голос с параллельным проигрыванием бита.
    Автоматически кладёт в voice_vault/ с меткой стиля.
    """
    try:
        import sounddevice as sd
        import numpy as np, soundfile as sf
    except ImportError:
        return {"error": "sounddevice не установлен"}

    if backing_path and os.path.exists(backing_path):
        play_backing_track(backing_path, in_headphones=True)

    print(f"[karaoke] Запись {duration_sec} сек в стиле '{style}' — ПОЕХАЛИ!")
    audio = sd.rec(int(duration_sec * sr), samplerate=sr, channels=1, dtype="float32")
    sd.wait()

    ts = int(time.time())
    out = VAULT / f"rec_{ts}_{style}.wav"
    sf.write(str(out), audio.squeeze(), sr)

    # Регистрируем в vault_index через voice_convert
    try:
        from modules.voice_convert import add_recording
        add_recording(str(out), {"style": style, "text": text,
                                  "duration_sec": duration_sec,
                                  "timestamp": ts})
    except Exception: pass

    return {"ok": True, "path": str(out), "style": style,
            "duration_sec": duration_sec}


def karaoke_ui(phrase: str, bpm: int = 120,
               style: str = "conversational",
               beat_path: Optional[str] = None) -> dict:
    """
    Заглушка для интеграции с v5 Gradio.
    В v7 Wizard использует прямо record_with_backing().
    """
    return {"phrase": phrase, "bpm": bpm, "style": style,
            "hint": "Слушай бит в наушниках, читай фразу, жми запись."}


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
