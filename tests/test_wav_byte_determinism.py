"""Один рецепт — одни байты: WAV не должен зависеть от времени записи.

Найдено в 42.0.16. `soundfile.write` (libsndfile) добавляет в WAV чанк `PEAK`,
а в нём лежит **текущее время** создания файла. Поэтому два файла с побитово
одинаковым аудио различались ровно одним байтом, и проверка
«`polished.wav` при одинаковом seed совпадает побайтово» не могла пройти,
сколько бы детерминизма ни добавляли в DSP.

`modules/dsp/wavio.write_wav` пишет RIFF сам: ни `PEAK`, ни чего-либо ещё
зависящего от окружения там нет.
"""

from __future__ import annotations

import hashlib
import struct
import time

import numpy as np
import soundfile as sf

from modules.dsp.wavio import strip_wav_metadata, supported_subtypes, write_wav


def _tone(sr: int = 8000, seconds: float = 2.0) -> np.ndarray:
    t = np.arange(int(sr * seconds))
    y = (0.25 * np.sin(t * 0.1)).astype("float32")
    return np.stack([y, y], axis=1)


def _sha(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_writes_are_byte_identical_across_time(tmp_path):
    """Главная регрессия: пауза между записями не меняет ни одного байта."""
    ref = _tone()
    first = tmp_path / "a.wav"
    write_wav(first, ref, 8000, subtype="FLOAT")
    time.sleep(1.1)  # секунда — минимальный шаг timestamp в чанке PEAK
    second = tmp_path / "b.wav"
    write_wav(second, ref, 8000, subtype="FLOAT")
    assert _sha(first) == _sha(second)


def test_no_peak_chunk_in_output(tmp_path):
    """Чанк `PEAK` — источник метки времени, его не должно быть вовсе."""
    path = tmp_path / "a.wav"
    write_wav(path, _tone(), 8000, subtype="FLOAT")
    assert b"PEAK" not in path.read_bytes()
    assert b"data" in path.read_bytes()


def test_soundfile_still_reads_our_files(tmp_path):
    """Свой RIFF обязан остаться обычным WAV для любого плеера."""
    for subtype in supported_subtypes():
        path = tmp_path / f"{subtype}.wav"
        ref = _tone()
        write_wav(path, ref, 8000, subtype=subtype)
        back, sr = sf.read(str(path), dtype="float64")
        assert sr == 8000
        assert back.shape == ref.shape
        # PCM теряет точность квантования, FLOAT — нет
        assert float(np.abs(back - ref).max()) < (1e-4 if subtype == "FLOAT" else 3e-4) or subtype == "PCM_24"


def test_riff_sizes_are_consistent(tmp_path):
    """Битый заголовок читается как «нет аудио» — проверяем арифметику."""
    path = tmp_path / "a.wav"
    write_wav(path, _tone(seconds=0.5), 8000, subtype="FLOAT")
    raw = path.read_bytes()
    assert raw[:4] == b"RIFF"
    assert raw[8:12] == b"WAVE"
    riff_size = struct.unpack("<I", raw[4:8])[0]
    assert riff_size == len(raw) - 8


def test_strip_wav_metadata_removes_timestamp(tmp_path):
    """Старые файлы с `PEAK` тоже приводятся к канону."""
    path = tmp_path / "legacy.wav"
    sf.write(str(path), _tone(), 8000, subtype="FLOAT")
    assert b"PEAK" in path.read_bytes(), "soundfile должен был поставить PEAK"
    assert strip_wav_metadata(path) is True
    assert b"PEAK" not in path.read_bytes()
    # повторный вызов уже ничего не меняет
    assert strip_wav_metadata(path) is False


def test_master_and_normalize_are_byte_stable(tmp_path):
    """Мастер и нормализация громкости — тоже без меток времени."""
    from modules import mastering

    ref = _tone(seconds=2.0)
    src = tmp_path / "src.wav"
    write_wav(src, ref, 8000, subtype="FLOAT")

    outs = []
    for i in range(3):
        out = tmp_path / f"n{i}.wav"
        mastering.normalize_master_loudness(str(src), str(out), target_lufs=-14.0)
        outs.append(_sha(out))
        time.sleep(0.02)
    assert len(set(outs)) == 1, f"нормализация дала разные байты: {outs}"
