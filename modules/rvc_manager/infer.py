# -*- coding: utf-8 -*-
"""
modules/rvc_manager/infer.py — инференс RVC: рендер голоса и отчёт состояния.
"""

from __future__ import annotations

from modules.rvc_manager.backend import detect_backend
from modules.rvc_manager.config import FORKS_DIR, MODELS_DIR, ROOT, _load_state


def infer(
    input_wav: str,
    voice_name: str = "my_voice",
    pitch_shift: int = 0,
    out_name: str = "converted.wav",
) -> str:
    """
    RVC-инференс: заменяет тембр во входном wav на голос пользователя.
    Пытается сначала rvc-python, потом форк. Возвращает путь к результату.
    """
    OUT = ROOT / "output" / "voice_final"
    OUT.mkdir(parents=True, exist_ok=True)
    out_path = OUT / out_name

    model_path = MODELS_DIR / voice_name / f"{voice_name}.pth"
    index_path = MODELS_DIR / voice_name / f"{voice_name}.index"

    if not model_path.exists():
        raise RuntimeError("RVC model is not available; refusing pitch-shift fallback")

    # 1) rvc-python
    backend = detect_backend()
    try:
        from rvc_python.infer import infer_file

        infer_file(
            input_path=input_wav,
            model_path=str(model_path),
            index_path=str(index_path) if index_path.exists() else None,
            output_path=str(out_path),
            f0up_key=pitch_shift,
            f0method="rmvpe",
            device=backend.kind,
        )
        if out_path.exists() and out_path.stat().st_size > 1000:
            return str(out_path)
        else:
            raise RuntimeError("RVC output file is empty or too small")
    except ImportError:
        # 2) AMD/DirectML/CPU: try fork if present
        if backend.fork != "rvc-python":
            fork_dir = FORKS_DIR / backend.fork
            if fork_dir.exists():
                # Здесь должна быть логика вызова CLI форка,
                # но для v14 мы оставляем это как задел для реального железа.
                raise RuntimeError(
                    f"RVC fork {backend.fork} is cloned but CLI integration is pending for this OS."
                )
        raise RuntimeError(
            "rvc-python not installed and no active fork integration found."
        )
    except Exception as e:
        print(f"[rvc_manager.infer] rvc-python failed: {e}")
        raise RuntimeError(
            f"RVC inference failed: {e}. No non-RVC fallback is permitted (TZ 33.5)."
        )


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
