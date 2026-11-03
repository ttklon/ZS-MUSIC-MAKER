# -*- coding: utf-8 -*-
"""
modules/rvc_manager/infer.py — инференс RVC: рендер голоса и отчёт состояния.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from modules.rvc_manager.backend import detect_backend
from modules.rvc_manager.config import MODELS_DIR, ROOT, _load_state


def infer(
    input_wav: str,
    voice_name: str = "my_voice",
    pitch_shift: int = 0,
    out_name: str = "converted.wav",
    model_path: str | None = None,
    index_path: str | None = None,
) -> str:
    """RVC через rvc-python. Явно выбранный индекс обязателен к чтению."""
    if not voice_name or Path(voice_name).name != voice_name or voice_name in (".", ".."):
        raise ValueError("invalid voice name")
    OUT = ROOT / "output" / "voice_final"
    out_path = OUT / out_name

    weights = Path(model_path) if model_path else MODELS_DIR / voice_name / f"{voice_name}.pth"
    default_index = MODELS_DIR / voice_name / f"{voice_name}.index"
    index = Path(index_path) if index_path else (default_index if not model_path else None)
    if not weights.is_file() or weights.suffix.lower() != ".pth":
        raise RuntimeError(f"RVC .pth model is not available: {weights}")
    if index_path and (not index.is_file() or index.suffix.lower() != ".index"):
        raise RuntimeError(f"RVC .index is not available: {index}")
    if out_path.resolve() in {Path(input_wav).resolve(), weights.resolve()} or (
        index is not None and out_path.resolve() == index.resolve()
    ):
        raise ValueError("RVC output must not overwrite input or model files")

    # rvc-python 0.1.x exposes RVCInference, not a module-level infer_file.
    # DirectML is not supported by this API; use CPU unless torch CUDA/ROCm is available.
    backend = detect_backend()
    temp_path = None
    model = None
    try:
        from rvc_python.infer import RVCInference
        from app.ai.quality import validate_rvc_artifact

        out_path.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(dir=out_path.parent, suffix=".wav")
        os.close(fd)
        temp_path = Path(name)
        device = "cuda:0" if backend.kind in ("cuda", "rocm") else "cpu:0"
        model = RVCInference(device=device, model_path=str(weights),
                             index_path=str(index) if index and index.is_file() else "")
        model.set_params(f0up_key=int(pitch_shift), f0method="rmvpe")
        model.infer_file(input_wav, str(temp_path))
        quality = validate_rvc_artifact(input_wav, temp_path)
        if not quality.get("ok"):
            raise RuntimeError(f"RVC output validation failed: {quality.get('reason')}")
        os.replace(temp_path, out_path)
        return str(out_path)
    except Exception as exc:
        raise RuntimeError(f"RVC inference failed: {type(exc).__name__}: {exc}") from exc
    finally:
        if model is not None:
            try:
                model.unload_model()
            except Exception:
                import logging
                logging.getLogger(__name__).warning("RVC unload failed", exc_info=True)
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def _fallback_pitch(input_wav: str, out_path: str, pitch_shift: int) -> str:
    """
    УДАЛЕНО в v14: pitch_shift fallback запрещён (TZ 33.5, P0.05).
    Эта функция сохранена только как явный отказ — вызов поднимает
    RuntimeError. Используйте RVC .pth модель или честный BLOCKED.
    """
    raise RuntimeError(
        "P0.05: pitch-shift as RVC is FORBIDDEN by TZ 33.5. "
        "RVC model is required. Got call to _fallback_pitch which was "
        "disabled. Train a voice model first (see voice_onboarding)."
    )


def get_state(voice_name: str = "my_voice") -> dict:
    """Читаем состояние обучения (для UI)."""
    return _load_state().get(voice_name, {})


def is_trained(voice_name: str = "my_voice") -> bool:
    return (MODELS_DIR / voice_name / f"{voice_name}.pth").exists()
