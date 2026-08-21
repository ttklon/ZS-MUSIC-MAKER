# АУДИТ ФАЙЛА: `app/plugins/base.py`

**LOC:** 88  |  **Размер:** 3724 байт  |  **Проблем:** 5  |  **Risk score:** 0

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 9 | `os` | import |
| 10 | `importlib` | import |
| 11 | `inspect` | import |
| 12 | `abc.ABC` | from |
| 12 | `abc.abstractmethod` | from |
| 13 | `typing.Dict` | from |
| 13 | `typing.Type` | from |
| 14 | `numpy` | import |
| 48 | `app.core.logger.app_logger` | from |
| 51 | `sys` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 17 | `__init__` | 2 | 0 | ❌ |
| 22 | `process` | 5 | 0 | ✅ |
| 29 | `__repr__` | 1 | 0 | ❌ |
| 33 | `__init__` | 1 | 0 | ❌ |
| 36 | `add` | 2 | 0 | ❌ |
| 40 | `process` | 20 | 4 | ❌ |
| 66 | `__new__` | 4 | 1 | ❌ |
| 72 | `discover` | 16 | 7 | ✅ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 16 | `AudioPlugin` | ❌ |
| 32 | `PluginChain` | ❌ |
| 62 | `PluginRegistry` | ✅ |

## Проблемы (детально, с цитатой кода)

### MISSING_CLASS_DOCSTRING — 2 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 16** — public class 'AudioPlugin' без docstring

  ```
         14 | import numpy as np
         15 | 
  >>>    16 | class AudioPlugin(ABC):
         17 |     def __init__(self, name: str):
         18 |         self.name = name
  ```

- **строка 32** — public class 'PluginChain' без docstring

  ```
         30 |         return f"<Plugin: {self.name} ({'Enabled' if self.enabled else 'Disabled'})>"
         31 | 
  >>>    32 | class PluginChain:
         33 |     def __init__(self):
         34 |         self.plugins = []
  ```

### BARE_PRINT — 2 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 52** — print() вместо logger

  ```
         50 |                     except Exception as _log_err:  # noqa: BLE001 — fallback на stderr, не падаем
         51 |                         import sys as _sys
  >>>    52 |                         print(
         53 |                             f"[plugins/base] logger unavailable ({_log_err}); "
         54 |                             f"sanitizing NaN/Inf in {type(plugin).__name__}",
  ```

- **строка 86** — print() вместо logger

  ```
         84 |                 except Exception as e:  # noqa: BLE001
         85 |                     # v39.4 (ШАГ 005): честный лог причины падения плагина
  >>>    86 |                     print(f"[plugins/base] failed to load {module_name}: "
         87 |                           f"{type(e).__name__}: {e}")
         88 |         return self.discovered
  ```

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 40** — public function 'process' без docstring

  ```
         38 |         return self
         39 | 
  >>>    40 |     def process(self, audio: np.ndarray, sr: int) -> np.ndarray:
         41 |         for plugin in self.plugins:
         42 |             if plugin.enabled:
  ```
