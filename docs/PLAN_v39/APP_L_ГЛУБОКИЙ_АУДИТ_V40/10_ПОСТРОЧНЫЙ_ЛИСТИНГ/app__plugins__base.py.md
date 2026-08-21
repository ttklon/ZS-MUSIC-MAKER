# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/plugins/base.py`

**Всего строк:** 88

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 22 | 25.0 |
| docstring | 12 | 13.6 |
| blank | 11 | 12.5 |
| import | 8 | 9.1 |
| def | 8 | 9.1 |
| comment | 6 | 6.8 |
| return | 5 | 5.7 |
| branch | 5 | 5.7 |
| try_block | 4 | 4.5 |
| class | 3 | 3.4 |
| loop | 3 | 3.4 |
| decorator | 1 | 1.1 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """
    3 [docstring ] ZS Music Maker — plugins/base.py (GOD MODE)
    4 [docstring ] ========================================================================
    5 [docstring ] Базовый класс для аудио-плагинов.
    6 [docstring ] Позволяет создавать цепочки обработки с единым интерфейсом.
    7 [docstring ] """
    8 [blank     ] 
    9 [import    ] import os
   10 [import    ] import importlib
   11 [import    ] import inspect
   12 [import    ] from abc import ABC, abstractmethod
   13 [import    ] from typing import Dict, Type
   14 [import    ] import numpy as np
   15 [blank     ] 
   16 [class     ] class AudioPlugin(ABC):
   17 [def       ]     def __init__(self, name: str):
   18 [code      ]         self.name = name
   19 [code      ]         self.enabled = True
   20 [blank     ] 
   21 [decorator ]     @abstractmethod
   22 [def       ]     def process(self, audio: np.ndarray, sr: int) -> np.ndarray:
   23 [docstring ]         """
   24 [docstring ]         Обработка аудио. 
   25 [docstring ]         audio: np.ndarray (frames, channels)
   26 [docstring ]         """
   27 [code      ]         pass
   28 [blank     ] 
   29 [def       ]     def __repr__(self):
   30 [return    ]         return f"<Plugin: {self.name} ({'Enabled' if self.enabled else 'Disabled'})>"
   31 [blank     ] 
   32 [class     ] class PluginChain:
   33 [def       ]     def __init__(self):
   34 [code      ]         self.plugins = []
   35 [blank     ] 
   36 [def       ]     def add(self, plugin: AudioPlugin):
   37 [code      ]         self.plugins.append(plugin)
   38 [return    ]         return self
   39 [blank     ] 
   40 [def       ]     def process(self, audio: np.ndarray, sr: int) -> np.ndarray:
   41 [loop      ]         for plugin in self.plugins:
   42 [branch    ]             if plugin.enabled:
   43 [comment   ]                 # v26: Защита от NaN/Inf (Audio Buffer Safety)
   44 [branch    ]                 if not np.all(np.isfinite(audio)):
   45 [comment   ]                     # v36 FIX (P2): раньше except:pass полностью глотал
   46 [comment   ]                     # ошибку и мы не видели, почему логгер недоступен.
   47 [try_block ]                     try:
   48 [import    ]                         from app.core.logger import app_logger
   49 [code      ]                         app_logger.warning(f"Sanitizing audio buffer in plugin {type(plugin).__name__}")
   50 [try_block ]                     except Exception as _log_err:  # noqa: BLE001 — fallback на stderr, не падаем
   51 [import    ]                         import sys as _sys
   52 [code      ]                         print(
   53 [code      ]                             f"[plugins/base] logger unavailable ({_log_err}); "
   54 [code      ]                             f"sanitizing NaN/Inf in {type(plugin).__name__}",
   55 [code      ]                             file=_sys.stderr,
   56 [code      ]                         )
   57 [code      ]                     audio = np.nan_to_num(audio, nan=0.0, posinf=1.0, neginf=-1.0)
   58 [blank     ]                 
   59 [code      ]                 audio = plugin.process(audio, sr)
   60 [return    ]         return audio
   61 [blank     ] 
   62 [class     ] class PluginRegistry:
   63 [docstring ]     """Автоматическое обнаружение плагинов."""
   64 [code      ]     _instance = None
   65 [blank     ] 
   66 [def       ]     def __new__(cls):
   67 [branch    ]         if not cls._instance:
   68 [code      ]             cls._instance = super(PluginRegistry, cls).__new__(cls)
   69 [code      ]             cls._instance.discovered: Dict[str, Type[AudioPlugin]] = {}
   70 [return    ]         return cls._instance
   71 [blank     ] 
   72 [def       ]     def discover(self):
   73 [docstring ]         """Сканирует папку plugins на наличие новых эффектов."""
   74 [code      ]         plugins_dir = os.path.dirname(__file__)
   75 [loop      ]         for filename in os.listdir(plugins_dir):
   76 [branch    ]             if filename.endswith(".py") and filename != "base.py":
   77 [comment   ]                 # Пытаемся импортировать модуль динамически
   78 [code      ]                 module_name = f"app.plugins.{filename[:-3]}"
   79 [try_block ]                 try:
   80 [code      ]                     module = importlib.import_module(module_name)
   81 [loop      ]                     for name, obj in inspect.getmembers(module):
   82 [branch    ]                         if inspect.isclass(obj) and issubclass(obj, AudioPlugin) and obj is not AudioPlugin:
   83 [code      ]                             self.discovered[name] = obj
   84 [try_block ]                 except Exception as e:  # noqa: BLE001
   85 [comment   ]                     # v39.4 (ШАГ 005): честный лог причины падения плагина
   86 [code      ]                     print(f"[plugins/base] failed to load {module_name}: "
   87 [code      ]                           f"{type(e).__name__}: {e}")
   88 [return    ]         return self.discovered
```