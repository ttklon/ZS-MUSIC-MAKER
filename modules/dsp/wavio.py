# -*- coding: utf-8 -*-
"""modules/dsp/wavio.py — каноническая запись WAV: один рецепт даёт одни байты.

Проблема, которую решает модуль
-------------------------------
`libsndfile` (через `soundfile.write`) по умолчанию добавляет в WAV чанки
`PEAK` и `fact`, а в `PEAK` пишет **текущее время** (поле `timestamp`). Из-за
этого два файла с побитово одинаковым аудио различались ровно одним байтом —
меткой времени. Замеры ломались сразу и незаметно:

* `sha256(polished.wav)` менялся от прогона к прогону при одинаковом seed
  (в 42.0.15 это списали на DSP, хотя DSP был уже детерминирован);
* любая проверка «тот же рецепт → те же байты» не могла пройти в принципе;
* кэш/дедупликация проектов видели «разные» файлы там, где аудио совпадало.

Что делает модуль
-----------------
Пишет WAV сам: RIFF + `fmt ` (+ `fact` для не-PCM) + `data`, без `PEAK` и без
прочих необязательных чанков. Содержимое файла зависит только от
`(данные, sample_rate, subtype)`. Аудио не трогается: значения пишутся
как есть, тем же `float32`/`int16`, что выбрал бы soundfile.

Формат:
* `FLOAT`  — 32-битный IEEE float, WAVE_FORMAT_IEEE_FLOAT (3);
* `PCM_16` — 16-битный PCM, WAVE_FORMAT_PCM (1), с правильным округлением
  и клиппингом (libsndfile делает то же самое);
* `PCM_24` — 24-битный PCM.
"""

from __future__ import annotations

import struct
from pathlib import Path

import numpy as np

WAVE_FORMAT_PCM = 1
WAVE_FORMAT_IEEE_FLOAT = 3
WAVE_FORMAT_EXTENSIBLE = 0xFFFE

_SUBTYPE_CODES: dict[str, tuple[int, int]] = {
    # subtype: (wave_format, bits_per_sample)
    "FLOAT": (WAVE_FORMAT_IEEE_FLOAT, 32),
    "PCM_16": (WAVE_FORMAT_PCM, 16),
    "PCM_24": (WAVE_FORMAT_PCM, 24),
}


def supported_subtypes() -> tuple[str, ...]:
    """Подтипы, которые модуль умеет писать без метаданных."""
    return tuple(_SUBTYPE_CODES)


def _as_2d(data: np.ndarray) -> np.ndarray:
    arr = np.asarray(data)
    if arr.ndim == 1:
        return arr[:, None]
    if arr.ndim != 2:
        raise ValueError(f"wavio: ожидается (N,) или (N, C), получено {arr.shape}")
    return arr


def _encode(data: np.ndarray, subtype: str) -> bytes:
    """Аудио → байты в целевом формате. Единственное место преобразования."""
    if subtype == "FLOAT":
        return np.ascontiguousarray(data, dtype="<f4").tobytes()
    if subtype == "PCM_16":
        scaled = np.clip(np.asarray(data, dtype=np.float64), -1.0, 1.0) * 32767.0
        return np.ascontiguousarray(np.rint(scaled), dtype="<i2").tobytes()
    if subtype == "PCM_24":
        scaled = np.clip(np.asarray(data, dtype=np.float64), -1.0, 1.0) * 8388607.0
        ints = np.ascontiguousarray(np.rint(scaled), dtype="<i4")
        # little-endian: младшие 3 байта каждого int32 и есть 24-битный сэмпл
        # (для отрицательных значений дополнение до двух уже учтено самим int32)
        return ints.reshape(-1).view(np.uint8).reshape(-1, 4)[:, :3].tobytes()
    raise ValueError(f"wavio: неизвестный subtype {subtype!r}, есть {supported_subtypes()}")


def _fmt_chunk(wave_format: int, channels: int, sample_rate: int, bits: int) -> bytes:
    block_align = channels * bits // 8
    byte_rate = sample_rate * block_align
    payload = struct.pack(
        "<HHIIHH", wave_format, channels, sample_rate, byte_rate, block_align, bits
    )
    return b"fmt " + struct.pack("<I", len(payload)) + payload


def write_wav(
    path: str | Path,
    data: np.ndarray,
    sample_rate: int,
    subtype: str = "FLOAT",
) -> str:
    """Записать WAV без меток времени. Возвращает путь строкой.

    Байты результата определяются только аргументами: ни время, ни окружение,
    ни порядок вызовов на файл не влияют.
    """
    if subtype not in _SUBTYPE_CODES:
        raise ValueError(f"wavio: неизвестный subtype {subtype!r}, есть {supported_subtypes()}")
    sr = int(sample_rate)
    if sr <= 0:
        raise ValueError(f"wavio: некорректный sample_rate {sample_rate!r}")

    arr = _as_2d(data)
    channels = int(arr.shape[1])
    if channels <= 0:
        raise ValueError("wavio: нет каналов")
    wave_format, bits = _SUBTYPE_CODES[subtype]

    payload = _encode(arr, subtype)
    chunks = [_fmt_chunk(wave_format, channels, sr, bits)]
    if subtype == "FLOAT":
        # libsndfile ставит `fact` для не-PCM, и это законно: число сэмплов на канал.
        frames = struct.pack("<I", int(arr.shape[0]))
        chunks.append(b"fact" + struct.pack("<I", len(frames)) + frames)
    chunks.append(b"data" + struct.pack("<I", len(payload)) + payload)

    body = b"WAVE" + b"".join(chunks)
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(b"RIFF" + struct.pack("<I", len(body)) + body)
    return str(out)


def strip_wav_metadata(path: str | Path) -> bool:
    """Перезаписать существующий WAV канонической формой. True — файл изменён."""
    from . import wavio as _self  # скрытая зависимость от soundfile только здесь

    del _self
    try:
        import soundfile as sf
    except Exception:  # pragma: no cover - soundfile есть всегда в проекте
        return False
    data, sr = sf.read(str(path), always_2d=True, dtype="float32")
    info = sf.info(str(path))
    subtype = info.subtype if info.subtype in _SUBTYPE_CODES else "FLOAT"
    before = Path(path).read_bytes()
    write_wav(path, data, sr, subtype=subtype)
    return Path(path).read_bytes() != before
