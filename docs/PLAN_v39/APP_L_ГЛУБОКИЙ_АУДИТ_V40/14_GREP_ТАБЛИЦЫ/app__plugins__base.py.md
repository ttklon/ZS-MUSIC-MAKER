# grep-таблицы `app/plugins/base.py`

## `import` — 8 совпадений
```
    9 | import os
   10 | import importlib
   11 | import inspect
   12 | from abc import ABC, abstractmethod
   13 | from typing import Dict, Type
   14 | import numpy as np
   48 |                         from app.core.logger import app_logger
   51 |                         import sys as _sys
```

## `print` — 2 совпадений
```
   52 |                         print(
   86 |                     print(f"[plugins/base] failed to load {module_name}: "
```

## `except` — 2 совпадений
```
   50 |                     except Exception as _log_err:  # noqa: BLE001 — fallback на stderr, не падаем
   84 |                 except Exception as e:  # noqa: BLE001
```

## `try` — 2 совпадений
```
   47 |                     try:
   79 |                 try:
```

## `def` — 8 совпадений
```
   17 |     def __init__(self, name: str):
   22 |     def process(self, audio: np.ndarray, sr: int) -> np.ndarray:
   29 |     def __repr__(self):
   33 |     def __init__(self):
   36 |     def add(self, plugin: AudioPlugin):
   40 |     def process(self, audio: np.ndarray, sr: int) -> np.ndarray:
   66 |     def __new__(cls):
   72 |     def discover(self):
```

## `class` — 3 совпадений
```
   16 | class AudioPlugin(ABC):
   32 | class PluginChain:
   62 | class PluginRegistry:
```

## `return` — 5 совпадений
```
   30 |         return f"<Plugin: {self.name} ({'Enabled' if self.enabled else 'Disabled'})>"
   38 |         return self
   60 |         return audio
   70 |         return cls._instance
   88 |         return self.discovered
```

## `if` — 5 совпадений
```
   42 |             if plugin.enabled:
   44 |                 if not np.all(np.isfinite(audio)):
   67 |         if not cls._instance:
   76 |             if filename.endswith(".py") and filename != "base.py":
   82 |                         if inspect.isclass(obj) and issubclass(obj, AudioPlugin) and obj is not AudioPlugin:
```

## `for` — 3 совпадений
```
   41 |         for plugin in self.plugins:
   75 |         for filename in os.listdir(plugins_dir):
   81 |                     for name, obj in inspect.getmembers(module):
```

## `np` — 5 совпадений
```
   22 |     def process(self, audio: np.ndarray, sr: int) -> np.ndarray:
   25 |         audio: np.ndarray (frames, channels)
   40 |     def process(self, audio: np.ndarray, sr: int) -> np.ndarray:
   44 |                 if not np.all(np.isfinite(audio)):
   57 |                     audio = np.nan_to_num(audio, nan=0.0, posinf=1.0, neginf=-1.0)
```
