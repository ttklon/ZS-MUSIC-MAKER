# -*- coding: utf-8 -*-
"""
ZS Music Maker — audio_utils.py (GOD MODE V7)
========================================================================
Утилиты для работы с аудио: нормализация, санитизация и выравнивание буферов.
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

class BufferAligner:
    @staticmethod
    def align(audio: np.ndarray, target_channels: int = 2) -> np.ndarray:
        """Принудительно выравнивает аудио-буфер под заданное число каналов."""
        if audio.ndim == 1:
            if target_channels == 2:
                return np.stack([audio, audio], axis=1)
            return audio[:, np.newaxis]
        elif audio.ndim == 2:
            current_channels = audio.shape[1]
            if current_channels == target_channels:
                return audio
            elif current_channels < target_channels:
                padded = np.pad(audio, ((0, 0), (0, target_channels - current_channels)), mode='edge')
                return padded
            else:
                return audio[:, :target_channels]
        return audio

class LoudnessNormalizer:
    def __init__(self, target_lufs: float = -14.0):
        self.target_lufs = target_lufs

    def process(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Нормализует громкость до целевого значения LUFS."""
        try:
            meter = pdn.Meter(sr)
            loudness = meter.integrated_loudness(audio)
            if np.isnan(loudness) or np.isinf(loudness):
                return audio
            normalized = pdn.normalize.loudness(audio, loudness, self.target_lufs)
            return normalized
        except Exception:
            return audio

def apply_soft_clip(audio: np.ndarray, threshold: float = 0.95) -> np.ndarray:
    """Мягкий клиппинг для предотвращения жестких искажений."""
    return np.tanh(audio / threshold) * threshold
