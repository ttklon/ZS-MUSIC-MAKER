# -*- coding: utf-8 -*-
"""MusicGen beat adapter: чанки до 30 секунд, continuation и проверяемый handle contract."""
from __future__ import annotations

import logging

import math
from pathlib import Path
from typing import Any, Dict, Optional

from app.ai.registry import registry


def _tensor_to_numpy(value: Any):
    """Извлечь CPU numpy без привязки к конкретной версии torch/audiocraft."""
    if hasattr(value, "detach"):
        value = value.detach()
    if hasattr(value, "cpu"):
        value = value.cpu()
    return value.numpy() if hasattr(value, "numpy") else value


def _render_with_handle(handle: Any, prompt: str, *, bpm: int, duration_sec: int,
                        out_path: str, chunk_sec: int) -> Dict[str, Any]:
    import numpy as np
    import soundfile as sf

    if duration_sec <= 0:
        return {"ok": False, "reason": "duration_sec must be positive"}
    chunk_sec = max(1, min(int(chunk_sec), 30))
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    try:
        handle.set_generation_params(
            duration=chunk_sec, top_k=250, top_p=0.0, temperature=1.0, cfg_coef=3.0
        )
    except Exception:
        # Совместимые fake/minimal handles могут не предоставлять parameters API.
        logging.getLogger(__name__).debug("ignored exception", exc_info=True)
    sample_rate = int(getattr(handle, "sample_rate", 32000))
    chunks = [_tensor_to_numpy(handle.generate([prompt], progress=False)[0])]
    chunk_count = max(1, math.ceil(duration_sec / chunk_sec))
    for _ in range(1, chunk_count):
        try:
            import torch

            previous = torch.from_numpy(chunks[-1]).unsqueeze(0)
            language_model = getattr(handle, "lm", None)
            if language_model is not None and any(p.is_cuda for p in language_model.parameters()):
                previous = previous.cuda()
            continuation = handle.generate_continuation(
                previous, sample_rate, [prompt], progress=False
            )[0]
            chunks.append(_tensor_to_numpy(continuation))
        except Exception:
            # Continuation является улучшением связности; если API его не
            # поддерживает, следующий independent chunk остаётся честным fallback.
            chunks.append(_tensor_to_numpy(handle.generate([prompt], progress=False)[0]))
    full = np.concatenate(chunks, axis=-1)
    expected_samples = int(duration_sec * sample_rate)
    if full.shape[-1] < expected_samples:
        return {
            "ok": False,
            "reason": "music generator returned fewer samples than requested duration",
            "generated_samples": int(full.shape[-1]),
            "expected_samples": expected_samples,
        }
    full = full[..., :expected_samples]
    if full.ndim == 1:
        full = np.stack([full, full], axis=-1)
    else:
        full = full.T
        if full.shape[1] == 1:
            full = np.concatenate([full, full], axis=1)
    peak = float(np.max(np.abs(full)) + 1e-9)
    if peak > 0.99:
        full = full * (0.98 / peak)
    sf.write(out_path, full.astype("float32"), sample_rate, subtype="PCM_16")
    return {
        "ok": True,
        "beat_path": str(out_path),
        "duration_sec": duration_sec,
        "sample_rate": sample_rate,
        "bpm": bpm,
        "engine": "musicgen-large",
        "chunks": chunk_count,
        "peak_before_ceiling": round(peak, 6),
        "continuation_fallback_allowed": True,
    }


def render_beat_ai(prompt: str, bpm: int = 140, duration_sec: int = 120,
                   out_path: str = "beat.wav", reference_wav: Optional[str] = None,
                   chunk_sec: int = 20, handle: Any = None) -> Dict[str, Any]:
    """Рендерить beat через переданный runner handle или standalone registry use.

    ``reference_wav`` сохраняется в result как provenance. MusicGen-large API,
    используемый здесь, не получает reference аудио как conditioning signal;
    параметр не маркируется как применённый, пока нет engine-specific adapter.
    """
    if handle is None and not registry.is_available("music_generation"):
        return {"ok": False, "reason": "music_generation unavailable - install audiocraft"}
    if handle is None:
        with registry.use("music_generation") as loaded:
            result = _render_with_handle(
                loaded.handle, prompt, bpm=bpm, duration_sec=duration_sec,
                out_path=out_path, chunk_sec=chunk_sec,
            )
    else:
        result = _render_with_handle(
            handle, prompt, bpm=bpm, duration_sec=duration_sec,
            out_path=out_path, chunk_sec=chunk_sec,
        )
    result["reference_wav"] = reference_wav
    result["reference_applied"] = False
    if reference_wav:
        result["reference_note"] = "reference path recorded; current MusicGen adapter has no audio-conditioning API"
    return result
