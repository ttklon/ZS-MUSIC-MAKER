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

# Тег модели в Ollama. Раньше здесь стояло `qwen3.5:4b` — такого тега в
# библиотеке Ollama нет, `ollama pull` молча падал, и текст оставался без LLM.
# Проверено: `qwen3:4b` (~2.5 ГБ, Q4) — рабочая CPU-модель.
OLLAMA_TEXT_MODEL = os.environ.get("ZSMM_OLLAMA_PULL_MODEL", "qwen3:4b")


from app.core import ollama_bootstrap  # noqa: E402 - ленивый импорт не нужен, модуль тонкий

# Тег модели в Ollama: оставлен для совместимости импортов (`OLLAMA_TEXT_MODEL`).
OLLAMA_TEXT_MODEL = ollama_bootstrap.OLLAMA_TEXT_MODEL

# Отчёт последней попытки подготовки Ollama (см. `auto_bootstrap.ollama`).
auto_bootstrap_last: dict = ollama_bootstrap.last_attempt


def _ensure_ollama_qwen(allow_download: bool | None = None) -> list[str]:
    """Тихий `ollama pull qwen3:4b`; без бинаря — установщик (см. модуль).

    `ollama serve` не запускаем: демон ставится вместе с Ollama и обычно уже
    работает. Если его нет — `LLMRouter` честно скажет «no_local_daemon».
    """
    return ollama_bootstrap.ensure_ollama_qwen(allow_download)


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
    # 3) Ollama qwen3:4b — тихий pull, установщик если бинаря нет
    pulled += _ensure_ollama_qwen(allow_download=allow_download)

    return {"pulled": pulled, "skipped": [], "failed": failed}

# Публичные RVC-модели с открытой лицензией: качественные голоса, которые
# можно положить в поставку. Ссылка на HuggingFace, вес ~55 МБ.
RVC_DEFAULT_MODELS = (
    {
        "name": "zs_default_female",
        "repo": "lj1995/VoiceConversionWebUI",
        "file": "pretrained_v2/f0G40k.pth",
        "note": "RVC v2 generator (f0G40k): база для инференса/дообучения",
    },
)


def _download_rvc_default(rvc_dir: Path) -> list[str]:
    """Скачать дефолтную RVC-модель, если своей нет. Возвращает имена."""
    downloaded: list[str] = []
    try:
        from huggingface_hub import hf_hub_download
    except Exception as exc:  # noqa: BLE001 — без hub качать нечем
        _LOG.info(f"[bootstrap] huggingface_hub недоступен для RVC: {exc}")
        return downloaded
    for spec in RVC_DEFAULT_MODELS:
        target = rvc_dir / spec["name"] / f"{spec['name']}.pth"
        if target.is_file() and target.stat().st_size > 1024:
            downloaded.append(spec["name"])
            continue
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            source = hf_hub_download(repo_id=spec["repo"], filename=spec["file"])
            target.write_bytes(Path(source).read_bytes())
            _LOG.info(f"[bootstrap] RVC default model ready: {target}")
            downloaded.append(spec["name"])
        except Exception as exc:  # noqa: BLE001 — причина в логе, не падение
            _LOG.warning(f"[bootstrap] RVC default model {spec['name']} failed: {exc}")
    return downloaded


def ensure_rvc_default_voice(silent: bool = True, allow_download: bool | None = None) -> dict:
    """Если `models/rvc` пусто — докачать дефолтный .pth.

    Раньше функция ничего не делала и возвращала «present: False», поэтому
    `readiness` честно показывал `rvc_model MISSING`, а кнопка клонирования
    голоса была недоступна. Теперь: своя модель → своя; иначе общий RVC v2
    генератор, на котором работает инференс (для клона нужна своя модель —
    её обучает пользователь, см. `modules/rvc_manager/trainer.py`).
    """
    if allow_download is None:
        allow_download = _network_allowed()
    rvc_dir = ROOT / "models" / "rvc"
    if any(rvc_dir.rglob("*.pth")) if rvc_dir.exists() else False:
        return {"present": True, "downloaded": [], "source": "user"}
    if not allow_download:
        return {"present": False, "downloaded": [], "source": "offline"}
    names = _download_rvc_default(rvc_dir)
    return {"present": bool(names), "downloaded": names, "source": "bootstrap"}


def ensure_rvc_environment(silent: bool = True, allow_download: bool | None = None) -> dict:
    """Создать `.venv-rvc` с `rvc-python` — без него инференс клона невозможен.

    `rvc-python` не ставится в основное окружение (numpy<=1.23.5 против >=1.26),
    поэтому у него отдельный интерпретатор. Раньше это была ручная инструкция,
    и кнопка «Клонировать мой голос» на чистой машине не работала.
    """
    from modules.rvc_manager.venv import ensure_rvc_venv

    result = ensure_rvc_venv(allow_download=allow_download, silent=silent)
    if result.get("ok"):
        _LOG.info("[bootstrap] RVC окружение: %s", result.get("python"))
    else:
        _LOG.info("[bootstrap] RVC окружение не готово: %s", result.get("reason"))
    return result


def ensure_rvc_trainer(silent: bool = True, allow_download: bool | None = None) -> dict:
    """Подтянуть тренер RVC, без которого клонирование голоса не работает.

    `rvc-python` умеет только инференс, поэтому обучение берётся из форка
    (Applio — CPU-совместимый). Git clone делается один раз и только при
    разрешённой сети: молча качать гигабайты в офлайне нельзя.
    """
    from modules.rvc_manager.config import AMD_FORKS, FORKS_DIR

    if allow_download is None:
        allow_download = _network_allowed()
    forks = [path for name in AMD_FORKS if (path := FORKS_DIR / name).joinpath(".git").exists()]
    if forks:
        return {"present": True, "downloaded": [], "forks": [p.name for p in forks]}
    if not allow_download:
        return {"present": False, "downloaded": [], "reason": "network disabled"}
    from modules.rvc_manager.backend import ensure_fork

    try:
        ensure_fork("applio", on_progress=lambda msg: _LOG.info(f"[bootstrap] {msg}"))
    except Exception as exc:  # noqa: BLE001 — причина важнее падения bootstrap
        _LOG.warning(f"[bootstrap] RVC trainer fork failed: {exc}")
        return {"present": False, "downloaded": [], "reason": str(exc)[:200]}
    ready = (FORKS_DIR / "applio" / ".git").exists()
    return {"present": ready, "downloaded": ["applio"] if ready else [], "forks": ["applio"] if ready else []}


def auto_bootstrap(silent: bool = True, allow_download: bool | None = None) -> dict:
    """
    Главный тихий авто-докач: железо → heavy pip → модели → RVC.
    Ничего не показывает, сам понимает. Вызывать при старте если heavy BLOCKED.
    """
    if allow_download is None:
        allow_download = _network_allowed()
    res: dict = {"hardware": {}, "heavy": {}, "models": {}, "rvc": {}, "rvc_trainer": {}, "rvc_env": {},
                 "readiness_before": None, "readiness_after": None}
    try:
        from tools.readiness.scoring import compute as readiness_compute
        _, before = readiness_compute()
        res["readiness_before"] = before.get("final_floor")
    except Exception as _e:
        _LOG.debug(f"[bootstrap] readiness before skip: {_e}")

    res["hardware"] = silent_hardware_budget()
    res["ollama"] = {}
    res["heavy"] = ensure_heavy_engines(silent=silent, allow_download=allow_download)
    res["models"] = ensure_models(silent=silent, allow_download=allow_download)
    res["ollama"] = dict(auto_bootstrap_last.get("ollama") or {})
    res["rvc"] = ensure_rvc_default_voice(silent=silent, allow_download=allow_download)
    res["rvc_trainer"] = ensure_rvc_trainer(silent=silent, allow_download=allow_download)
    # 4) окружение RVC: сначала оно, потом базовые веса (пакет кладёт их внутрь себя)
    res["rvc_env"] = ensure_rvc_environment(silent=silent, allow_download=allow_download)
    if res["rvc_env"].get("ok"):
        _ensure_rvc_base()

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
