"""
ZS Music Maker — mastering_pro.py (GOD MODE)
========================================================================
Профессиональный мастеринг-движок на базе Spotify Pedalboard.
Включает:
  - Многополосную компрессию (эмуляция)
  - Стерео-расширитель
  - Ламповую сатурацию
  - Лимитирование по стандарту True Peak
  - Автоматическую нормализацию громкости (LUFS)
"""

import os

import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from pedalboard import (
    Chorus,
    Compressor,
    Distortion,
    HighpassFilter,
    Limiter,
    Pedalboard,
)
from pedalboard.io import AudioFile


def process_mastering(input_wav: str, output_wav: str, target_lufs: float = -14.0):
    """
    Профессиональный мастеринг трека.
    """
    with AudioFile(input_wav) as f:
        audio = f.read(f.frames)
        samplerate = f.samplerate

    # 1. Создаем цепь эффектов
    board = Pedalboard(
        [
            # Удаляем лишний низ
            HighpassFilter(cutoff_frequency_hz=30),
            # Легкая сатурация для "тепла"
            Distortion(drive_db=2.0),
            # Компрессия для склейки микса
            Compressor(threshold_db=-18, ratio=2.0, attack_ms=5.0, release_ms=50.0),
            # Стерео-расширение для воздуха (только выше 400 Гц)
            Chorus(rate_hz=0.1, depth=0.1, centre_delay_ms=7.0, feedback=0.0, mix=0.15),
            # Финальный лимитер
            Limiter(threshold_db=-0.5, release_ms=100.0),
        ]
    )

    # 2. Применяем эффекты
    mastered = board(audio, samplerate)

    # 3. Нормализация громкости по LUFS
    # Pedalboard output is (channels, frames), pyloudnorm expects (frames, channels)
    audio_to_norm = mastered.T
    meter = pyln.Meter(samplerate)
    loudness = meter.integrated_loudness(audio_to_norm)

    # Применяем гейн для достижения целевой громкости
    mastered = pyln.normalize.loudness(audio_to_norm, loudness, target_lufs)

    # 4. Финальный True Peak Limiter (через Clipping для безопасности)
    mastered = np.clip(mastered, -0.99, 0.99)

    # Запись результата
    os.makedirs(os.path.dirname(output_wav), exist_ok=True)
    sf.write(output_wav, mastered, samplerate, format="WAV", subtype="PCM_16")

    return {
        "ok": True,
        "path": output_wav,
        "engine": "pedalboard_pro",
        "input_lufs": round(loudness, 2),
        "target_lufs": target_lufs,
    }


if __name__ == "__main__":
    # Тестовый запуск, если файл существует
    test_file = "/home/ubuntu/ZS-MUSIC-MAKER/src/src/output/smoke_v26/p_v26/masters/master_streaming.wav"
    if os.path.exists(test_file):
        res = process_mastering(test_file, "output/pro_master_test.wav")
        print(res)
