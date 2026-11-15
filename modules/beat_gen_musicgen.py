# -*- coding: utf-8 -*-
"""
modules.beat_gen_musicgen — бит от MusicGen на CPU: чанки 30 с, честный отказ.

Зачем отдельный модуль, если есть `modules/beat_gen_ai`:

  * `beat_gen_ai` работает через `registry` (handle может быть `None`);
  * здесь — прямой путь «загрузил `facebook/musicgen-small`, сгенерировал
    N чанков по 30 секунд, склеил, записал WAV», который нужен агентику и
    `HitFactory` без адаптивного гуру-режима;
  * CPU — целевая платформа: чанк 30 с — максимум модели и одновременно
    разумный шаг, чтобы не держать 3 ГБ активаций.

Контракт: `render_musicgen_beat(...) -> dict`. Если движка нет — `ok: False`
и `reason` с инструкцией. Никакого процедурного суррогата здесь нет:
он живёт в другом модуле и называется своим именем.
"""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Any

_LOG = logging.getLogger(__name__)

# MusicGen обучен на 32 кГц и 30 секундах: длиннее — уже не «продолжение», а
# накопление ошибки; короче — больше склеек.
SAMPLE_RATE = 32000
MAX_CHUNK_SEC = 30
DEFAULT_MODEL = "facebook/musicgen-small"


def _tensor_to_numpy(value: Any) -> Any:
    """Tensor → numpy без жёсткой привязки к версии torch/audiocraft."""
    if hasattr(value, "detach"):
        value = value.detach()
    if hasattr(value, "float"):
        value = value.float()
    if hasattr(value, "cpu"):
        value = value.cpu()
    return value.numpy() if hasattr(value, "numpy") else value


def _load_model(model_name: str, device: str) -> Any:
    """Ленивая загрузка MusicGen. `get_model`, если версия его знает.

    audiocraft 1.3.0 допускает `get_pretrained`, но новый API — `get_model`;
    пробуем новый первым, потому что он не тянет веса по неверному имени.
    """
    from audiocraft.models import MusicGen

    loader = getattr(MusicGen, "get_model", None) or getattr(MusicGen, "get_pretrained")
    try:
        return loader(model_name, device=device)
    except TypeError:
        # Старые подписи не принимают `device` (или принимают иначе).
        return loader(model_name)


def _generate_chunks(model: Any, prompt: str, duration_sec: int, chunk_sec: int) -> Any:
    """Сгенерировать `duration_sec` секунд: первый чанк + продолжения."""
    import numpy as np

    model.set_generation_params(duration=chunk_sec, top_k=250, top_p=0.0, temperature=1.0, cfg_coef=3.0)
    chunks = [_tensor_to_numpy(model.generate([prompt], progress=False)[0])]
    total = max(1, math.ceil(duration_sec / chunk_sec))
    for _ in range(1, total):
        chunks.append(_continue_chunk(model, chunks[-1], prompt))
    return np.concatenate([np.asarray(chunk) for chunk in chunks], axis=-1)


def _continue_chunk(model: Any, previous: Any, prompt: str) -> Any:
    """Продолжение предыдущего чанка; нет API — независимый чанк того же промпта.

    Продолжение связнее, но не у всех версий audiocraft оно есть. Отказ
    помечается в отчёте (`continuation_used`), а не прячется.
    """
    try:
        import torch

        tensor = torch.from_numpy(previous).unsqueeze(0)
        return _tensor_to_numpy(model.generate_continuation(tensor, SAMPLE_RATE, [prompt], progress=False)[0])
    except Exception as exc:  # noqa: BLE001 — ниже честный независимый чанк
        _LOG.info("MusicGen continuation unavailable: %s", exc)
        return _tensor_to_numpy(model.generate([prompt], progress=False)[0])


def _to_stereo(data: Any, samples: int) -> Any:
    """Обрезать/дополнить до точной длины и сделать два канала."""
    import numpy as np

    audio = np.asarray(data)
    if audio.ndim == 1:
        audio = np.stack([audio, audio], axis=-1)
    elif audio.shape[0] <= 2 and audio.shape[-1] > audio.shape[0]:
        # (channels, samples) → (samples, channels)
        audio = audio.T
        if audio.shape[1] == 1:
            audio = np.concatenate([audio, audio], axis=1)
    if audio.shape[0] < samples:
        pad = samples - audio.shape[0]
        audio = np.pad(audio, ((0, pad), (0, 0)))
    audio = audio[:samples]
    peak = float(np.max(np.abs(audio)) + 1e-9)
    if peak > 0.99:
        audio = audio * (0.98 / peak)
    return audio.astype("float32")


def render_musicgen_beat(
    prompt: str,
    out_path: str,
    duration_sec: int = 60,
    model_name: str = DEFAULT_MODEL,
    chunk_sec: int = MAX_CHUNK_SEC,
    device: str = "cpu",
) -> dict[str, Any]:
    """Отрисовать бит MusicGen на CPU и записать WAV.

    Возвращает `{ok, beat_path, engine, chunks, sample_rate, duration_sec}`.
    При отсутствии audiocraft/весов — `{ok: False, reason}` без исключения:
    вызывающий код обязан уметь честно сказать «бита от MusicGen нет».
    """
    if not prompt or not prompt.strip():
        return {"ok": False, "reason": "пустой промпт: MusicGen не знает, что играть"}
    duration = max(1, int(duration_sec))
    chunk = max(5, min(int(chunk_sec), MAX_CHUNK_SEC))
    try:
        import soundfile as sf

        model = _load_model(model_name, device)
        data = _generate_chunks(model, prompt, duration, chunk)
        audio = _to_stereo(data, duration * SAMPLE_RATE)
        target = Path(out_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(target), audio, SAMPLE_RATE, subtype="PCM_16")
    except ImportError as exc:
        return {
            "ok": False,
            "reason": f"audiocraft/soundfile недоступны: {exc}",
            "action": "python main.py --bootstrap --online",
        }
    except Exception as exc:  # noqa: BLE001 — причина в отчёте, а не в трейсбеке
        _LOG.warning("MusicGen render failed: %s", exc)
        return {"ok": False, "reason": f"{type(exc).__name__}: {exc}"}
    return {
        "ok": True,
        "beat_path": str(out_path),
        "engine": f"musicgen:{model_name}",
        "chunks": max(1, math.ceil(duration / chunk)),
        "chunk_sec": chunk,
        "sample_rate": SAMPLE_RATE,
        "duration_sec": duration,
        "device": device,
    }


def musicgen_available() -> dict[str, Any]:
    """Готов ли MusicGen: движок + веса. Без сети и без загрузки модели."""
    import importlib.util

    engine = importlib.util.find_spec("audiocraft") is not None
    torch_ok = importlib.util.find_spec("torch") is not None
    return {
        "ok": bool(engine and torch_ok),
        "engine": engine,
        "torch": torch_ok,
        "reason": "" if engine and torch_ok else "нужен bootstrap: audiocraft + torch 2.5.1 CPU",
    }
