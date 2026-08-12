# -*- coding: utf-8 -*-
"""
ZS Music Maker — plugins/advanced.py (GOD MODE)
========================================================================
Продвинутые плагины: сатурация, пространственные эффекты и Anti-AI аугментация.
"""

import numpy as np
from app.plugins.base import AudioPlugin

# v27 FIX (P0): pedalboard / audiomentations были жёсткими top-level импортами —
# без них падал весь plugin-слой. Теперь ленивые, с честными no-op заглушками.
try:
    from pedalboard import Pedalboard, Distortion, Reverb, Compressor, HighpassFilter  # type: ignore
    _HAS_PB = True
except Exception:  # pragma: no cover
    _HAS_PB = False

    class _NoopFx:  # минимальная заглушка, не ломающая сборку
        def __init__(self, *a, **k):
            pass

    class Pedalboard:  # type: ignore
        def __init__(self, effects=None):
            self.effects = effects or []

        def __call__(self, audio, sr):
            return audio  # passthrough

    Distortion = Reverb = Compressor = HighpassFilter = _NoopFx  # type: ignore

try:
    from audiomentations import Compose, PitchShift, TimeStretch, AddGaussianNoise, RoomSimulator  # type: ignore
    _HAS_AUG = True
except Exception:  # pragma: no cover
    _HAS_AUG = False

    class Compose:  # type: ignore
        def __init__(self, transforms=None):
            self.transforms = transforms or []

        def __call__(self, samples, sample_rate):
            return samples  # passthrough

    PitchShift = TimeStretch = AddGaussianNoise = RoomSimulator = object  # type: ignore

class PedalboardPlugin(AudioPlugin):
    def __init__(self, name: str, effects: list):
        super().__init__(name)
        self.board = Pedalboard(effects)

    def process(self, audio: np.ndarray, sr: int) -> np.ndarray:
        # Pedalboard expects (channels, frames)
        if audio.ndim == 2:
            audio_t = audio.T
            processed = self.board(audio_t, sr)
            return processed.T
        else:
            return self.board(audio, sr)

class PhonkDistortion(PedalboardPlugin):
    def __init__(self, drive_db: float = 20.0):
        super().__init__("PhonkDistortion", [
            Distortion(drive_db=drive_db),
            HighpassFilter(cutoff_frequency_hz=300),
            Compressor(threshold_db=-15, ratio=4.0)
        ])

class AntiAINeuroObfuscator(AudioPlugin):
    def __init__(self, intensity: float = 0.5):
        super().__init__("AntiAINeuroObfuscator")
        self.augment = Compose([
            PitchShift(min_semitones=-0.2, max_semitones=0.2, p=intensity),
            TimeStretch(min_rate=0.98, max_rate=1.02, p=intensity),
            AddGaussianNoise(min_amplitude=0.001, max_amplitude=0.005, p=intensity * 0.5),
            RoomSimulator(p=intensity * 0.3)
        ])

    def process(self, audio: np.ndarray, sr: int) -> np.ndarray:
        # Audiomentations expects (channels, frames) or (frames,)
        if audio.ndim == 2:
            audio_t = audio.T
            processed = self.augment(samples=audio_t, sample_rate=sr)
            return processed.T
        else:
            return self.augment(samples=audio, sample_rate=sr)
