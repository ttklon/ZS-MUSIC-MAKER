# -*- coding: utf-8 -*-
"""
ZS Music Maker — audio_utils.py (GOD MODE)
========================================================================
Утилиты для работы с аудио: нормализация, санитизация и эффекты.
"""

import numpy as np
import pyloudnorm as pdn
from app.core.i18n import i18n
import logging

logger = logging.getLogger("AudioUtils")

class AudioSanitizer:
    @staticmethod
    def sanitize(audio: np.ndarray) -> np.ndarray:
        """Удаляет NaN и Inf из аудио-буфера."""
        if not np.isfinite(audio).all():
            logger.warning(i18n.t("sanitizer_warning"))
            audio = np.nan_to_num(audio, nan=0.0, posinf=1.0, neginf=-1.0)
        return audio

class LoudnessNormalizer:
    def __init__(self, target_lufs: float = -14.0):
        self.target_lufs = target_lufs

    def process(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Нормализует громкость до целевого значения LUFS."""
        meter = pdn.Meter(sr)
        loudness = meter.integrated_loudness(audio)
        normalized = pdn.normalize.loudness(audio, loudness, self.target_lufs)
        return normalized

def apply_soft_clip(audio: np.ndarray, threshold: float = 0.9) -> np.ndarray:
    """Мягкий клиппинг для предотвращения жестких искажений."""
    return np.tanh(audio / threshold) * threshold
