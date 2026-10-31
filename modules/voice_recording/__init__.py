# -*- coding: utf-8 -*-
"""
ZS Music Maker — modules/voice_recording
=======================================

РЕАЛЬНАЯ запись с микрофона (P0.03):

  * `sounddevice.InputStream`, а не приём готового WAV;
  * live-метрики: RMS / peak / LUFS-подобный уровень / клиппинг;
  * VAD с гистерезисом и нарезка на дубли по паузам ≥ 600 мс;
  * сохранение в `voice_vault/` с метаданными дублей.

Если `sounddevice` недоступен (headless-песочница), модуль остаётся честным:
`capability_report()` сообщает `real_recording_possible=False` и причину.

Раскладка:
  * `state`      — пути, логгер, опциональные бэкенды, метрики;
  * `recorder`   — `RealMicRecorder`: живая запись и VAD;
  * `takes`      — `split_wav_into_takes`: нарезка на дубли;
  * `capability` — `capability_report`: что реально доступно на этой машине.
"""

from modules.voice_recording.capability import capability_report  # noqa: F401
from modules.voice_recording.recorder import RealMicRecorder  # noqa: F401
from modules.voice_recording.state import (  # noqa: F401
    SD_OK,
    VAULT_DIR,
    RecorderMetrics,
    TakeInfo,
)
from modules.voice_recording.takes import split_wav_into_takes  # noqa: F401

__all__ = [
    "SD_OK",
    "VAULT_DIR",
    "RealMicRecorder",
    "RecorderMetrics",
    "TakeInfo",
    "capability_report",
    "split_wav_into_takes",
]
