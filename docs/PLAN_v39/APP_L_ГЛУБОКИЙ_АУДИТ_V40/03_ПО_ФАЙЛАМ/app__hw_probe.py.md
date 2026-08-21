# АУДИТ ФАЙЛА: `app/hw_probe.py`

**LOC:** 65  |  **Размер:** 1651 байт  |  **Проблем:** 6  |  **Risk score:** 5

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 3 | `__future__.annotations` | from |
| 5 | `json` | import |
| 6 | `platform` | import |
| 7 | `dataclasses.asdict` | from |
| 7 | `dataclasses.dataclass` | from |
| 23 | `psutil` | import |
| 32 | `torch` | import |
| 46 | `torch_directml` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 21 | `probe` | 36 | 5 | ❌ |
| 60 | `main` | 1 | 0 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 11 | `HW` | ❌ |

## Проблемы (детально, с цитатой кода)

### SILENT_EXCEPT_PASS — 2 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 40** — except: pass — тихое подавление ошибок

  ```
         38 |             )
         39 |             hw.backend = "cuda"
  >>>    40 |     except Exception:
         41 |         pass
         42 | 
  ```

- **строка 53** — except: pass — тихое подавление ошибок

  ```
         51 |             hw.vram_gb = 4.0  # оценочно — уточняется через DXGI
         52 |             hw.backend = "directml"
  >>>    53 |         except Exception:
         54 |             pass
         55 | 
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 3** — import 'annotations' не используется в теле файла

  ```
          1 | """Автодетект железа: CUDA / DirectML / CPU + VRAM + режим full/fallback."""
          2 | 
  >>>     3 | from __future__ import annotations
          4 | 
          5 | import json
  ```

### MISSING_CLASS_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 11** — public class 'HW' без docstring

  ```
          9 | 
         10 | @dataclass
  >>>    11 | class HW:
         12 |     gpu_name: str = "CPU"
         13 |     vram_gb: float = 0.0
  ```

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 21** — public function 'probe' без docstring

  ```
         19 | 
         20 | 
  >>>    21 | def probe() -> HW:
         22 |     try:
         23 |         import psutil
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 61** — print() вместо logger

  ```
         59 | 
         60 | def main():
  >>>    61 |     print(json.dumps(asdict(probe()), ensure_ascii=False, indent=2))
         62 | 
         63 | 
  ```
