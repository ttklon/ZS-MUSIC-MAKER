"""
ZS Music Maker — phonk_engine.py (GOD MODE)
========================================================================
Синтезатор классического Phonk-колокольчика (Cowbell).
Генерирует звук из Saw-волны с жесткой дисторшн-обработкой и эквализацией.
"""

import numpy as np
import soundfile as sf
from pedalboard import (
    Clipping,
    Delay,
    Distortion,
    HighpassFilter,
    LowpassFilter,
    Pedalboard,
    Reverb,
)


def generate_cowbell(note_hz: float, duration_sec: float = 0.5, sr: int = 44100):
    """
    Генерирует один удар Phonk-колокольчика.
    """
    t = np.linspace(0, duration_sec, int(sr * duration_sec), endpoint=False)

    # 1. Базовая волна (Sawtooth + Square для агрессии)
    wave = 0.6 * (2 * (t * note_hz - np.floor(0.5 + t * note_hz)))  # Saw
    wave += 0.4 * np.sign(np.sin(2 * np.pi * note_hz * t))  # Square

    # 2. Огибающая (ADSR - быстрый спад)
    envelope = np.exp(-t * 12.0)
    wave = wave * envelope

    # 3. Pedalboard обработка (Hard Distortion + Reverb)
    board = Pedalboard(
        [
            Distortion(drive_db=25.0),
            HighpassFilter(cutoff_frequency_hz=400),
            LowpassFilter(cutoff_frequency_hz=8000),
            Delay(delay_seconds=0.15, feedback=0.3, mix=0.2),
            Reverb(room_size=0.3, wet_level=0.2),
            Clipping(threshold_db=-1.0),
        ]
    )

    processed = board(wave.reshape(1, -1), sr).reshape(-1)

    # Нормализация
    processed = processed / (np.max(np.abs(processed)) + 1e-9)
    return processed


def create_cowbell_melody(notes_hz: list, bpm: int, out_wav: str):
    """
    Создает мелодию из колокольчиков.
    """
    sr = 44100
    step_sec = 60.0 / bpm / 2  # 1/8 ноты
    total_len = int(len(notes_hz) * step_sec * sr)
    buffer = np.zeros(total_len + sr, dtype=np.float32)

    for i, hz in enumerate(notes_hz):
        if hz > 0:
            bell = generate_cowbell(hz, duration_sec=0.6, sr=sr)
            start = int(i * step_sec * sr)
            end = start + len(bell)
            buffer[start:end] += bell

    # Нормализация и запись
    buffer = buffer / (np.max(np.abs(buffer)) + 1e-9)
    sf.write(out_wav, buffer, sr)
    return out_wav


if __name__ == "__main__":
    # Тест: классическая Phonk мелодия
    bpm = 130
    # Ноты (Hz): A4, A4, C5, A4, G4, A4...
    melody = [440, 0, 440, 0, 523.25, 0, 440, 0, 392, 0, 440, 0]
    create_cowbell_melody(melody, bpm, "output/phonk_cowbell_test.wav")
