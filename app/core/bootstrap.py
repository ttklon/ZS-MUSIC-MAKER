# -*- coding: utf-8 -*-
"""
app/core/bootstrap.py — тихий авто-докач всего тяжёлого (all_heavy).

Вызывается молча: без вопросов, без UI, без показа железа.
- detect_budget() → RAM/VRAM/CPU, выбор cuda/cpu
- если BLOCKED musicgen/demucs/torch/faster-whisper — pip install при allow_online
- если модели не скачаны — pull_ai_models --all + RVC base + ollama qwen
- после — readiness должен уйти с 65% → 90-100% (heavy cap снимается)
- genre/ai: full_agents — trend_scout + sample_hunter + sequential_runner везде

Использует app/core/net_policy.network_allowed для проверки сети.
Логи только в файл/logs, в консоль минимум.
"""
from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_LOG = logging.getLogger(__name__)

# тяжёлые pip-пакеты, которые не входят в requirements.txt (см. INSTALL.md)
HEAVY_PIP = {
    "torch": "torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cpu",
    "audiocraft": "audiocraft==1.3.0",
    "demucs": "demucs==4.0.1",
    "faster_whisper": "faster-whisper==1.1.1",
    "rvc_python": "rvc-python==0.1.5",
}

# pip имена → import имена
PIP_TO_IMPORT = {
    "torch": "torch",
    "audiocraft": "audiocraft",
    "demucs": "demucs",
    "faster_whisper": "faster_whisper",
    "rvc_python": "rvc_python",
}

def _module_exists(name: str) -> bool:
    try:
        __import__(name)
        return True
    except Exception:
        return False

def silent_hardware_budget() -> dict:
    """Тихий детект железа — ничего не показывает, сам понимает."""
    try:
        from app.ai.hardware import detect_budget
        b = detect_budget()
        _LOG.info(f"[bootstrap] hw silent: RAM {b.get('ram_gb')}GB VRAM {b.get('vram_gb')}GB threads {b.get('cpu_threads')}")
        return b
    except Exception as e:
        _LOG.debug(f"[bootstrap] hw silent failed: {e}")
        return {"ram_gb": 0, "vram_gb": 0, "cpu_threads": os.cpu_count() or 1}

def _network_allowed() -> bool:
    try:
        from app.core.net_policy import network_allowed
        return network_allowed()
    except Exception:
        return False

def missing_heavy() -> list[str]:
    miss = []
    for pip_name, import_name in PIP_TO_IMPORT.items():
        if not _module_exists(import_name):
            miss.append(pip_name)
    # дополнительно audiocraft/demucs могут быть установлены но BLOCKED из-за torch
    return miss

def _pip_install(spec: str, silent: bool = True) -> bool:
    """pip install spec (может содержать --index-url). Возвращает успех."""
    try:
        cmd = [sys.executable, "-m", "pip", "install", "--quiet"] + spec.split()
        _LOG.info(f"[bootstrap] pip install {' '.join(cmd[4:6])}...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0:
            _LOG.info(f"[bootstrap] pip ok: {spec.split()[0]}")
            return True
        _LOG.warning(f"[bootstrap] pip fail {spec.split()[0]}: {result.stderr[:500]}")
        return False
    except Exception as e:
        _LOG.warning(f"[bootstrap] pip exception {spec}: {e}")
        return False

def ensure_heavy_engines(silent: bool = True, allow_download: bool | None = None) -> dict:
    """
    Тихая установка тяжёлых pip-пакетов если сеть разрешена.
    Возвращает {installed:[], skipped:[], failed:[]}
    """
    if allow_download is None:
        allow_download = _network_allowed()
    if not allow_download:
        _LOG.info("[bootstrap] network not allowed — skip heavy pip")
        return {"installed": [], "skipped": missing_heavy(), "failed": []}

    budget = silent_hardware_budget()
    # если VRAM 0 — ставим cpu-версию torch (already cpu index)
    miss = missing_heavy()
    if not miss:
        _LOG.info("[bootstrap] heavy engines already present")
        return {"installed": [], "skipped": [], "failed": []}

    installed, failed = [], []
    for name in miss:
        spec = HEAVY_PIP.get(name)
        if not spec:
            continue
        ok = _pip_install(spec, silent=silent)
        if ok:
            installed.append(name)
        else:
            failed.append(name)
        # GC между тяжёлыми установками
        try:
            import gc
            gc.collect()
        except Exception as _e:
            _LOG.debug(f"[bootstrap] gc skip: {_e}")
    return {"installed": installed, "skipped": [], "failed": failed}

def missing_models() -> list[str]:
    """Какие роли MODEL_REGISTRY не available."""
    try:
        from app.ai.registry import registry
        miss = []
        for key in registry._loaders.keys():
            try:
                if not registry.is_available(key):
                    miss.append(key)
            except Exception:
                miss.append(key)
        return miss
    except Exception as e:
        _LOG.debug(f"[bootstrap] missing_models check failed: {e}")
        return []

def _pull_missing_roles() -> tuple[list[str], list[str]]:
    pulled, failed = [], []
    try:
        from tools.pull_ai_models import pull as pull_one
        from app.ai.model_catalog import MODEL_REGISTRY
        for role in MODEL_REGISTRY.keys():
            if MODEL_REGISTRY[role].get("engine") == "rvc":
                continue
            try:
                from app.ai.registry import registry
                if registry.is_available(role):
                    continue
            except Exception as _e:
                _LOG.debug(f"[bootstrap] is_available skip {role}: {_e}")
            _LOG.info(f"[bootstrap] pull {role}...")
            try:
                ok = pull_one(role)
                pulled.append(role)
            except Exception as e:
                _LOG.warning(f"[bootstrap] pull {role} fail: {e}")
                failed.append(role)
    except Exception as e:
        _LOG.warning(f"[bootstrap] pull all failed: {e}")
    return pulled, failed

def _ensure_rvc_base() -> None:
    try:
        import os as _os
        if _os.environ.get("ZSMM_RVC_PYTHON", "").strip():
            _LOG.info("[bootstrap] RVC external env present — skip base check")
            return
        from modules.rvc_manager.rvc_worker import require_base_assets
        require_base_assets()
        _LOG.info("[bootstrap] RVC base assets ok")
    except Exception as e:
        _LOG.info(f"[bootstrap] RVC base missing (will be fetched on first infer): {e}")

def _ensure_ollama_qwen() -> list[str]:
    try:
        import shutil, subprocess as _sp
        if not shutil.which("ollama"):
            return []
        _LOG.info("[bootstrap] ollama found — pull qwen3.5:4b if missing")
        res = _sp.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
        if "qwen" not in (res.stdout or "").lower():
            _LOG.info("[bootstrap] ollama pull qwen3.5:4b ...")
            _sp.run(["ollama", "pull", "qwen3.5:4b"], capture_output=True, text=True, timeout=600)
            return ["ollama_qwen"]
    except Exception as _e:
        _LOG.debug(f"[bootstrap] ollama pull skip: {_e}")
    return []

def ensure_models(silent: bool = True, allow_download: bool | None = None) -> dict:
    """Тихая докачка моделей через tools/pull_ai_models --all + RVC base."""
    if allow_download is None:
        allow_download = _network_allowed()
    if not allow_download:
        _LOG.info("[bootstrap] network not allowed — skip model pull")
        return {"pulled": [], "skipped": missing_models(), "failed": []}
    pulled, failed = _pull_missing_roles()
    # 2) RVC base assets — тихо
    _ensure_rvc_base()
    # 3) Ollama qwen3.5:4b — если ollama установлен, тихо pull
    pulled += _ensure_ollama_qwen()

    return {"pulled": pulled, "skipped": [], "failed": failed}

def ensure_rvc_default_voice(silent: bool = True, allow_download: bool | None = None) -> dict:
    """Если models/rvc пусто — докачать демо-голос (tiny) чтобы RVC не был MISSING."""
    if allow_download is None:
        allow_download = _network_allowed()
    rvc_dir = ROOT / "models" / "rvc"
    has_pth = any(rvc_dir.rglob("*.pth")) if rvc_dir.exists() else False
    if has_pth:
        return {"present": True, "downloaded": False}
    if not allow_download:
        return {"present": False, "downloaded": False}
    # пробуем скачать tiny демо с huggingface (публичный, маленький)
    # используем huggingface_hub если есть, иначе оставляем user_supplied
    try:
        from huggingface_hub import hf_hub_download
        target = rvc_dir / "my_voice"
        target.mkdir(parents=True, exist_ok=True)
        # пример: используем лёгкий тестовый pth если доступен — иначе просто создаём заглушку
        # здесь не качаем тяжёлый чужой голос без лицензии, отмечаем как user_supplied
        _LOG.info("[bootstrap] RVC no .pth — keep user_supplied, will be BLOCKED until user adds model")
        return {"present": False, "downloaded": False}
    except Exception as _e:
        _LOG.debug(f"[bootstrap] RVC voice check: {_e}")
        return {"present": False, "downloaded": False}

def auto_bootstrap(silent: bool = True, allow_download: bool | None = None) -> dict:
    """
    Главный тихий авто-докач: железо → heavy pip → модели → RVC.
    Ничего не показывает, сам понимает. Вызывать при старте если heavy BLOCKED.
    """
    if allow_download is None:
        allow_download = _network_allowed()
    res: dict = {"hardware": {}, "heavy": {}, "models": {}, "rvc": {}, "readiness_before": None, "readiness_after": None}
    try:
        from tools.readiness.scoring import compute as readiness_compute
        _, before = readiness_compute()
        res["readiness_before"] = before.get("final_floor")
    except Exception as _e:
        _LOG.debug(f"[bootstrap] readiness before skip: {_e}")

    res["hardware"] = silent_hardware_budget()
    res["heavy"] = ensure_heavy_engines(silent=silent, allow_download=allow_download)
    res["models"] = ensure_models(silent=silent, allow_download=allow_download)
    res["rvc"] = ensure_rvc_default_voice(silent=silent, allow_download=allow_download)

    # авто-жанр/full_agents уже в breakthrough/orchestrator — здесь только гарантия что heavy есть
    try:
        from tools.readiness.scoring import compute as readiness_compute2
        final, after = readiness_compute2()
        res["readiness_after"] = after.get("final_floor")
        res["caps_after"] = after.get("caps_triggered")
        _LOG.info(f"[bootstrap] readiness {res['readiness_before']} → {final} caps {res['caps_after']}")
    except Exception as e:
        _LOG.debug(f"[bootstrap] readiness after fail: {e}")

    return res

def wire_full_agents():
    """
    Гарантирует что каждый вызов прогоняет всех ИИ-агентов автономно.
    Уже в breakthrough.full_orchestrate и orchestrator — здесь только проверка.
    """
    # проверка что агенты импортируются
    try:
        import agents.trend_scout  # noqa
        import agents.sample_hunter  # noqa
        from app.ai.sequential_runner import SequentialAIRunner  # noqa
        _LOG.info("[bootstrap] full_agents wired: trend_scout, sample_hunter, SequentialAI")
        return True
    except Exception as e:
        _LOG.warning(f"[bootstrap] full_agents missing: {e}")
        return False
