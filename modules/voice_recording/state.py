# -*- coding: utf-8 -*-
"""
modules/voice_recording/state.py — общее состояние модуля записи.

Здесь живут пути, логгер, опциональный бэкенд `sounddevice`/`numpy` и
dataclass-метрики. Если `sounddevice` нет (headless-песочница, сервер без
аудио), `SD_OK=False` — это честный флаг, а не повод притворяться, что запись
сработала.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
VAULT_DIR = ROOT / "voice_vault"
LOGGER = logging.getLogger(__name__)

try:
    import numpy as _np
    import sounddevice as _sd  # type: ignore

    SD_OK = True
except Exception:
    _sd = None
    _np = None
    SD_OK = False


@dataclass
class RecorderMetrics:
    rms_db: float = -100.0
    peak_db: float = -100.0
    lufs_short: float = -70.0
    clipping_pct: float = 0.0
    snr_db_estimate: float = 0.0
    elapsed_sec: float = 0.0
    is_speaking: bool = False


@dataclass
class TakeInfo:
    take_id: str
    path: str
    start_sec: float
    end_sec: float
    duration_sec: float
    rms_db: float
    peak_db: float
    clipping_pct: float
    quality: str
    style: str = "conversational"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
