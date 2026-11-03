# -*- coding: utf-8 -*-
"""
modules/rvc_manager — оркестрация RVC v2 (FALLBACK-путь, не основной).

Основной вокальный путь проекта — запись живого голоса пользователя.
RVC применяется как «полировка» поверх своей записи или как честный fallback,
когда записанного вокала нет.

  * `detect_backend()` — подобрать рабочее железо/форк;
  * `ensure_fork()`    — подтянуть AMD-форк один раз (git clone);
  * `RVCTrainer`       — подготовка dataset; встроенное обучение пока заблокировано;
  * `infer()`          — рендер, `is_trained()` / `get_state()` — состояние.

Раскладка: `config`, `backend`, `trainer`, `infer`.
"""

from modules.rvc_manager.backend import (  # noqa: F401
    RVCBackend,
    detect_backend,
    ensure_fork,
)
from modules.rvc_manager.config import (  # noqa: F401
    AMD_FORKS,
    FORKS_DIR,
    MODELS_DIR,
    STATE_FILE,
)
from modules.rvc_manager.infer import (  # noqa: F401
    _fallback_pitch,
    get_state,
    infer,
    is_trained,
)
from modules.rvc_manager.trainer import RVCTrainer, TrainingJob  # noqa: F401

__all__ = [
    "AMD_FORKS",
    "FORKS_DIR",
    "MODELS_DIR",
    "RVCBackend",
    "RVCTrainer",
    "STATE_FILE",
    "TrainingJob",
    "detect_backend",
    "ensure_fork",
    "get_state",
    "infer",
    "is_trained",
]
