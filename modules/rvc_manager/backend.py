# -*- coding: utf-8 -*-
"""
modules/rvc_manager/backend.py — определение бэкенда RVC и подтягивание форка.

Определение устройства PyTorch для RVC inference и ручное получение форков.
Наличие устройства не доказывает наличие пакета, весов или успешный inference.
"""

from __future__ import annotations

import logging

import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from modules.rvc_manager.config import AMD_FORKS, FORKS_DIR


@dataclass
class RVCBackend:
    kind: str = "cpu"  # "cuda" | "directml" | "rocm" | "cpu"
    device_name: str = "CPU"
    vram_gb: float = 0.0
    fork: str = "rvc-python"  # rvc-python | applio | mangio | rvc-webui
    ok: bool = False
    reason: str = ""


def detect_backend() -> RVCBackend:
    """rvc-python supports torch CPU or torch CUDA/ROCm, not generic DirectML."""
    try:
        import torch

        if torch.cuda.is_available():
            is_rocm = bool(getattr(getattr(torch, "version", None), "hip", None))
            return RVCBackend(
                kind="rocm" if is_rocm else "cuda",
                device_name=torch.cuda.get_device_name(0),
                vram_gb=round(torch.cuda.get_device_properties(0).total_memory / (1024 ** 3), 2),
                fork="rvc-python", ok=True,
                reason="PyTorch ROCm device detected" if is_rocm else "PyTorch CUDA device detected",
            )
    except Exception:
        logging.getLogger(__name__).debug("RVC GPU backend unavailable", exc_info=True)
    return RVCBackend(kind="cpu", device_name="CPU", fork="rvc-python", ok=True,
                      reason="CPU selected; installed RVC package and model still need verification")


# ---------------------------------------------------------------- ensure fork
def ensure_fork(
    fork_name: str, on_progress: Callable[[str], None] | None = None
) -> Path:
    """
    Клонирует AMD-совместимый форк RVC локально при первом запуске.
    Возвращает путь к папке форка. Не требует интернета если уже подтянут.
    """

    def _p(msg: str):
        if on_progress:
            on_progress(msg)
        print(f"[rvc_manager] {msg}")

    if fork_name == "rvc-python":
        # rvc-python — pip-пакет, отдельно клонировать не нужно
        try:
            import rvc_python  # noqa: F401

            _p("rvc-python OK (pip)")
        except ImportError:
            # v37 FIX: windows_build.bat больше не существует — указываем реальный путь установки.
            _p(
                "rvc-python не установлен — pip install rvc-python "
                "(или запусти install.py, он ставит heavy-deps per-package; см. INSTALL.md §4)"
            )
        return FORKS_DIR / "rvc-python"

    if fork_name not in AMD_FORKS:
        _p(f"Неизвестный форк {fork_name}, использую applio")
        fork_name = "applio"

    target = FORKS_DIR / fork_name
    if target.exists() and (target / ".git").exists():
        _p(f"Форк {fork_name} уже подтянут → {target}")
        return target

    url = AMD_FORKS[fork_name]
    _p(f"Клонирую {fork_name} из {url}")
    try:
        # depth=1 для скорости и экономии диска
        subprocess.run(
            ["git", "clone", "--depth", "1", url, str(target)],
            check=True,
            capture_output=True,
            text=True,
            timeout=600,
        )
        _p(f"{fork_name} успешно клонирован → {target}")
    except FileNotFoundError:
        _p("git не найден. Установи git for Windows: https://git-scm.com/download/win")
    except subprocess.CalledProcessError as e:
        _p(f"git clone упал: {e.stderr[-300:] if e.stderr else e}")
    except Exception as e:
        _p(f"ensure_fork: {type(e).__name__}: {e}")
    return target
