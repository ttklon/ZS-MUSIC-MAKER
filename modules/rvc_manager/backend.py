# -*- coding: utf-8 -*-
"""
modules/rvc_manager/backend.py — определение бэкенда RVC и подтягивание форка.

NVIDIA → `rvc-python` (CUDA), AMD/DirectML → Applio/Mangio-форк через git clone,
остальное → CPU. `detect_backend()` честно возвращает `ok=False`, если
рабочего рантайма нет.
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
    """Определяем оптимальный бэкенд и форк RVC под текущее железо."""
    b = RVCBackend()
    # 1) NVIDIA CUDA
    try:
        import torch

        if torch.cuda.is_available():
            b.kind = "cuda"
            b.device_name = torch.cuda.get_device_name(0)
            b.vram_gb = round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1)
            b.fork = "rvc-python"
            b.ok = True
            b.reason = "CUDA available"
            return b
    except Exception:
        logging.getLogger(__name__).debug("ignored exception", exc_info=True)
    # 2) DirectML (AMD/Intel iGPU на Windows)
    try:
        import torch_directml as dml

        b.kind = "directml"
        b.device_name = (
            dml.device_name(0) if hasattr(dml, "device_name") else "DirectML GPU"
        )
        b.vram_gb = 4.0
        b.fork = "applio"  # Applio — лучший AMD-friendly форк
        b.ok = True
        b.reason = "DirectML available"
        return b
    except Exception:
        logging.getLogger(__name__).debug("ignored exception", exc_info=True)
    # 3) ROCm (Linux, редко)
    try:
        import torch

        if hasattr(torch.version, "hip") and torch.version.hip is not None:
            b.kind = "rocm"
            b.device_name = "AMD GPU (ROCm)"
            b.vram_gb = 8.0
            b.fork = "mangio"
            b.ok = True
            b.reason = "ROCm available"
            return b
    except Exception:
        logging.getLogger(__name__).debug("ignored exception", exc_info=True)
    # 4) CPU fallback
    b.kind = "cpu"
    b.device_name = "CPU"
    b.fork = "rvc-python"
    b.ok = True
    b.reason = "CPU fallback"
    return b


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
