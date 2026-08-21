# -*- coding: utf-8 -*-
"""
ZS Music Maker — plugins/base.py (GOD MODE)
========================================================================
Базовый класс для аудио-плагинов.
Позволяет создавать цепочки обработки с единым интерфейсом.
"""

import os
import importlib
import inspect
from abc import ABC, abstractmethod
from typing import Dict, Type
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
                # v26: Защита от NaN/Inf (Audio Buffer Safety)
                if not np.all(np.isfinite(audio)):
                    # v36 FIX (P2): раньше except:pass полностью глотал
                    # ошибку и мы не видели, почему логгер недоступен.
                    try:
                        from app.core.logger import app_logger
                        app_logger.warning(f"Sanitizing audio buffer in plugin {type(plugin).__name__}")
                    except Exception as _log_err:  # noqa: BLE001 — fallback на stderr, не падаем
                        import sys as _sys
                        print(
                            f"[plugins/base] logger unavailable ({_log_err}); "
                            f"sanitizing NaN/Inf in {type(plugin).__name__}",
                            file=_sys.stderr,
                        )
                    audio = np.nan_to_num(audio, nan=0.0, posinf=1.0, neginf=-1.0)
                
                audio = plugin.process(audio, sr)
        return audio

class PluginRegistry:
    """Автоматическое обнаружение плагинов."""
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(PluginRegistry, cls).__new__(cls)
            cls._instance.discovered: Dict[str, Type[AudioPlugin]] = {}
        return cls._instance

    def discover(self):
        """Сканирует папку plugins на наличие новых эффектов."""
        plugins_dir = os.path.dirname(__file__)
        for filename in os.listdir(plugins_dir):
            if filename.endswith(".py") and filename != "base.py":
                # Пытаемся импортировать модуль динамически
                module_name = f"app.plugins.{filename[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and issubclass(obj, AudioPlugin) and obj is not AudioPlugin:
                            self.discovered[name] = obj
                except Exception as e:  # noqa: BLE001
                    # v39.4 (ШАГ 005): честный лог причины падения плагина
                    print(f"[plugins/base] failed to load {module_name}: "
                          f"{type(e).__name__}: {e}")
        return self.discovered
