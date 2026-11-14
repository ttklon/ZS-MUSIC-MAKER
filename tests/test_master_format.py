# -*- coding: utf-8 -*-
"""
Формат мастер-файлов: PCM 24 бит, а не 32-bit float.

Живой прогон `--god` отдал восемь мастеров по 40 МБ каждый (120 с, стерео,
44100 Гц) в `FLOAT`: файл вдвое тяжелее нужного, а площадки (Spotify, Apple
Music, YouTube) принимают для мастера PCM 16/24 бита — float WAV им не нужен
и часть сервисов его не берёт.

Замер перекодирования на 20 с реального сигнала:

    FLOAT   6.7 МБ  SNR 350.6 дБ
    PCM_24  5.0 МБ  SNR 132.3 дБ   ← 24 бита — потолок для мастера
    PCM_16  3.4 МБ  SNR  83.2 дБ   ← шум слышен на тихих местах

LUFS у всех трёх одинаковый (−10.08), поэтому выбор 24 бит не меняет
громкость стенда и не трогает гейты.
"""

from __future__ import annotations

import numpy as np
import soundfile as sf

from modules.mastering import chain


def _mix(path, seconds: float = 2.0) -> str:
    sample_rate = 22_050
    axis = np.arange(int(sample_rate * seconds)) / sample_rate
    signal = 0.2 * np.sin(2 * np.pi * 100 * axis) + 0.1 * np.sin(2 * np.pi * 900 * axis)
    stereo = np.stack([signal, signal], axis=1).astype(np.float32)
    sf.write(str(path), stereo, sample_rate)
    return str(path)


def test_master_is_written_as_pcm24(tmp_path) -> None:
    mix = _mix(tmp_path / "mix.wav")
    result = chain.master_one(mix, str(tmp_path / "master.wav"), stand="streaming")

    assert result["ok"] is True, result.get("reason")
    info = sf.info(result["path"])
    assert info.subtype == "PCM_24", f"мастер записан как {info.subtype}: площадки ждут PCM 16/24"


def test_master_changes_only_the_encoding(tmp_path) -> None:
    """Смена формата трогает только кодировку: каналы, частота, громкость те же.

    Целевой LUFS стенда на двухсекундном синтетическом сигнале не
    достигается ни в float, ни в PCM 24 (стенд «streaming» хочет −14, а
    короткий тон упирается в потолок пика) — это свойство тестового сигнала,
    а не формата. Поэтому сравниваются измерения до и после кодирования.
    """
    import numpy as np

    mix = _mix(tmp_path / "mix.wav")
    result = chain.master_one(mix, str(tmp_path / "master.wav"), stand="streaming")

    info = sf.info(result["path"])
    assert info.channels == 2
    assert info.samplerate == 22_050

    # Громкость в файле совпадает с той, что назвал отчёт мастеринга: запись
    # в PCM 24 не сдвинула уровень.
    audio, sample_rate = sf.read(result["path"], dtype="float64")
    from modules.dsp import metrics

    written_lufs = metrics.integrated_lufs(audio, sample_rate)[0]
    assert abs(written_lufs - result["output_lufs"]) <= 0.5, (written_lufs, result["output_lufs"])
    assert np.isfinite(written_lufs)


def test_pcm24_noise_floor_is_below_audible() -> None:
    """Проверка выбора формата числом: 24 бита дают SNR выше 100 дБ."""
    sample_rate = 44_100
    axis = np.arange(sample_rate) / sample_rate
    reference = np.sin(2 * np.pi * 440 * axis)
    for subtype, floor in (("PCM_24", 100.0), ("PCM_16", 80.0)):
        noise = (reference * 32768).round() / 32768 if subtype == "PCM_16" else None
        if subtype == "PCM_24":
            quantized = (reference * 8388608).round() / 8388608
        else:
            quantized = noise
        error = quantized - reference
        snr = 10 * np.log10(np.sum(reference**2) / max(np.sum(error**2), 1e-30))
        assert snr > floor, f"{subtype}: SNR {snr:.1f} дБ ниже {floor}"
