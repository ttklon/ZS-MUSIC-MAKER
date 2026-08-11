"""
ZS Music Maker — voice_cleaner.py (GOD MODE)
========================================================================
Интеллектуальная очистка голоса от шумов.
Использует спектральное вычитание для удаления фонового шума.
"""

import os

import noisereduce as nr
import soundfile as sf


def clean_vocal(input_wav: str, output_wav: str, prop_decrease: float = 1.0):
    """
    Очистка вокала от шума.
    """
    data, samplerate = sf.read(input_wav)

    # noisereduce работает с 1D (mono) или 2D (stereo) массивами
    # Если стерео, обрабатываем каналы
    reduced_noise = nr.reduce_noise(y=data, sr=samplerate, prop_decrease=prop_decrease)

    os.makedirs(os.path.dirname(output_wav), exist_ok=True)
    sf.write(output_wav, reduced_noise, samplerate)

    return {
        "ok": True,
        "path": output_wav,
        "engine": "noisereduce_v3",
        "prop_decrease": prop_decrease,
    }


if __name__ == "__main__":
    # Тестовый запуск
    pass
