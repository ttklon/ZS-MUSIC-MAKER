# -*- coding: utf-8 -*-
"""
ZS Music Maker — plugins/mastering.py (GOD MODE)
========================================================================
Финальный мастеринг: LUFS нормализация и Soft-Clipping.
"""

import numpy as np
from app.plugins.base import AudioPlugin
from app.core.audio_utils import LoudnessNormalizer, apply_soft_clip

class ProfessionalMastering(AudioPlugin):
    def __init__(self, target_lufs: float = -14.0, clip_threshold: float = 0.95):
        super().__init__("ProfessionalMastering")
        self.norm = LoudnessNormalizer(target_lufs)
        self.clip_threshold = clip_threshold

    def process(self, audio: np.ndarray, sr: int) -> np.ndarray:
        # 1. Нормализация
        try:
            audio = self.norm.process(audio, sr)
        except Exception as e:
            print(f"Mastering Normalization failed: {e}")
            
        # 2. Мягкий клиппинг
        audio = apply_soft_clip(audio, self.clip_threshold)
        
        return audio
