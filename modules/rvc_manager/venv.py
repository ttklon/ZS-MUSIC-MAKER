# -*- coding: utf-8 -*-
"""
modules/rvc_manager/venv.py — отдельное окружение для RVC (`.venv-rvc`).

Почему отдельное: `rvc-python==0.1.5` тянет `numpy<=1.23.5`, а основной проект
живёт на `numpy>=1.26`. Поставить оба в один интерпретатор нельзя, поэтому
инференс RVC идёт отдельным процессом (`ZSMM_RVC_PYTHON`), а это окружение
должно кто-то создать. Раньше это была ручная инструкция в `INSTALL.md` —
человек нажимал «Клонировать голос» и получал отказ.

Здесь три вещи без магии:

  * `find_rvc_python()` — найти готовый интерпретатор: env → `.venv-rvc`;
  * `ensure_rvc_venv()` — создать окружение и поставить `rvc-python`, честно
    возвращая отчёт (что поставили, чем не смогли, что осталось);
  * `rvc_venv_report()` — состояние для readiness/UI без побочных эффектов.

Сеть уважается: без разрешения ничего не качается, возвращается причина.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path

from modules.rvc_manager.config import ROOT

_LOG = logging.getLogger(__name__)

VENV_DIR = ROOT / ".venv-rvc"
PINNED_RVC = "rvc-python==0.1.5"
# numpy прибит версией пакета: ставить сверху «свежий» — значит ломать rvc-python.
PINNED_EXTRA = ("numpy<=1.23.5", "soundfile", "torch==2.5.1", "torchaudio==2.5.1")

# Порядок поиска базового интерпретатора: RVC требует Python 3.8–3.11.
BASE_CANDIDATES = ("py -3.10", "py -3.11", "python3.10", "python3.11", "python3", "python")
# rvc-python 0.1.5 собран под numpy<=1.23.5, у которого нет колёс для 3.12+.
_SUPPORTED_VERSIONS = {"(3, 8)", "(3, 9)", "(3, 10)", "(3, 11)"}


def _venv_python(venv_dir: Path = VENV_DIR) -> Path:
    """Путь к интерпретатору внутри окружения (Windows и POSIX)."""
    windows = venv_dir / "Scripts" / "python.exe"
    return windows if windows.is_file() else venv_dir / "bin" / "python"


def find_rvc_python(venv_dir: Path | None = None) -> str | None:
    """Готовый интерпретатор RVC: сначала явный `ZSMM_RVC_PYTHON`, потом venv."""
    explicit = os.environ.get("ZSMM_RVC_PYTHON", "").strip()
    if explicit:
        path = Path(explicit)
        return str(path) if path.is_absolute() and path.is_file() else None
    candidate = _venv_python(venv_dir or VENV_DIR)
    return str(candidate) if candidate.is_file() else None


def _run(cmd: list[str], timeout: int) -> tuple[int, str]:
    """Выполнить команду без оболочки; весь вывод вернуть строкой."""
    try:
        done = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, f"{type(exc).__name__}: {exc}"
    return done.returncode, (done.stdout or "") + (done.stderr or "")


def _base_python() -> list[str] | None:
    """Найти системный Python, из которого можно создать окружение."""
    for candidate in BASE_CANDIDATES:
        parts = candidate.split()
        code, out = _run(parts + ["-c", "import sys; print(sys.version_info[:2])"], timeout=30)
        if code != 0:
            continue
        if out.strip() in _SUPPORTED_VERSIONS:
            return parts
        _LOG.debug("RVC venv: %s даёт %s — нужен Python 3.8–3.11", candidate, out.strip())
    return None


def _install(interpreter: str, allow_download: bool) -> dict:
    """Поставить rvc-python в окружение. Возвращает отчёт, а не исключение."""
    # Обновление pip — удобство, а не условие: старый pip тоже ставит колёса.
    # Раньше его отказ прерывал установку, и человек видел «pip upgrade failed»
    # вместо готового окружения.
    code, out = _run([interpreter, "-m", "pip", "install", "--upgrade", "pip", "--quiet"], timeout=600)
    if code != 0:
        _LOG.debug("RVC venv: pip upgrade failed, продолжаю: %s", out.strip()[-200:])
    code, out = _run(
        [interpreter, "-m", "pip", "install", "--quiet", PINNED_RVC, *PINNED_EXTRA],
        timeout=3600,
    )
    if code != 0:
        hint = "" if allow_download else " (сеть запрещена — включи --online)"
        return {"ok": False, "reason": f"rvc-python install failed: {out.strip()[-400:]}{hint}"}
    code, check = _run([interpreter, "-c", "import rvc_python, numpy; print(numpy.__version__)"], timeout=120)
    if code != 0:
        return {"ok": False, "reason": f"rvc_python import failed: {check.strip()[-300:]}"}
    return {"ok": True, "numpy": check.strip().splitlines()[-1] if check.strip() else "", "output": out.strip()[-300:]}


def ensure_rvc_venv(
    allow_download: bool | None = None, silent: bool = True, venv_dir: Path | None = None
) -> dict:
    """Создать `.venv-rvc` и поставить `rvc-python`, если его ещё нет.

    Идемпотентно: готовое окружение не пересоздаётся и не переустанавливается.
    """
    from app.core.net_policy import network_allowed

    target = venv_dir or VENV_DIR
    existing = find_rvc_python(target)
    if existing:
        return {"ok": True, "python": existing, "created": False, "reason": "already installed"}
    if allow_download is None:
        allow_download = network_allowed()
    if not allow_download:
        return {"ok": False, "python": None, "created": False, "reason": "network disabled"}

    base = _base_python()
    if base is None:
        return {
            "ok": False, "python": None, "created": False,
            "reason": "не найден Python 3.8–3.11 для окружения RVC "
                      "(rvc-python не совместим с numpy основного проекта)",
        }
    code, out = _run([*base, "-m", "venv", str(target)], timeout=900)
    if code != 0:
        return {"ok": False, "python": None, "created": False, "reason": f"venv creation failed: {out.strip()[-300:]}"}
    interpreter = str(_venv_python(target))
    installed = _install(interpreter, allow_download)
    if not installed.get("ok"):
        return {"ok": False, "python": interpreter, "created": True, "reason": installed.get("reason")}
    os.environ["ZSMM_RVC_PYTHON"] = interpreter
    if not silent:
        _LOG.info("[rvc] окружение готово: %s", interpreter)
    return {
        "ok": True, "python": interpreter, "created": True,
        "reason": "created", "numpy": installed.get("numpy", ""),
    }


def rvc_venv_report() -> dict:
    """Состояние окружения RVC без побочных эффектов (для readiness и UI)."""
    current = find_rvc_python()
    assets_dir = None
    if current:
        code, out = _run(
            [current, "-c",
             "import importlib.util, pathlib, json;"
             "spec=importlib.util.find_spec('rvc_python');"
             "print(json.dumps({'origin': spec.origin if spec else ''}))"],
            timeout=120,
        )
        if code == 0 and out.strip():
            try:
                origin = json.loads(out.strip().splitlines()[-1]).get("origin") or ""
                assets_dir = str(Path(origin).parent / "base_model") if origin else None
            except ValueError:
                _LOG.debug("rvc venv report: unparsable %r", out.strip()[:120])
    assets = None
    if assets_dir:
        folder = Path(assets_dir)
        assets = {name: (folder / name).is_file() for name in ("hubert_base.pt", "rmvpe.pt", "rmvpe.onnx")}
    return {
        "installed": bool(current),
        "python": current,
        "venv": str(VENV_DIR),
        "base_model_dir": assets_dir,
        "base_assets": assets,
        "active": bool(os.environ.get("ZSMM_RVC_PYTHON", "").strip()),
    }
