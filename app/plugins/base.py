# -*- coding: utf-8 -*-
"""
ZS Music Maker — plugins/base.py (GOD MODE)
========================================================================
Базовый класс для аудио-плагинов.
Позволяет создавать цепочки обработки с единым интерфейсом.
"""

from abc import ABC, abstractmethod
import numpy as np

class AudioPlugin(ABC):
    def __init__(self, name: str):
        self.name = name
        self.enabled = True

    @abstractmethod
    def process(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """
        Обработка аудио. 
        audio: np.ndarray (frames, channels)
        """
        pass

    def __repr__(self):
        return f"<Plugin: {self.name} ({'Enabled' if self.enabled else 'Disabled'})>"

class PluginChain:
    def __init__(self):
        self.plugins = []

    def add(self, plugin: AudioPlugin):
        self.plugins.append(plugin)
        return self

    def process(self, audio: np.ndarray, sr: int) -> np.ndarray:
        for plugin in self.plugins:
            if plugin.enabled:
                audio = plugin.process(audio, sr)
        return audio
