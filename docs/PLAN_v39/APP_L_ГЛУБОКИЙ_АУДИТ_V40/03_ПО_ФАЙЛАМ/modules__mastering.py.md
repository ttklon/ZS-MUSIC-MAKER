# АУДИТ ФАЙЛА: `modules/mastering.py`

**LOC:** 210  |  **Размер:** 8053 байт  |  **Проблем:** 4  |  **Risk score:** 3

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 25 | `__future__.annotations` | from |
| 27 | `os` | import |
| 28 | `pathlib.Path` | from |
| 29 | `typing.Any` | from |
| 31 | `numpy` | import |
| 32 | `soundfile` | import |
| 35 | `pyloudnorm` | import |
| 205 | `sys` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 57 | `_one_pole_shelf` | 23 | 3 | ✅ |
| 83 | `_apply_stand_eq` | 15 | 2 | ✅ |
| 101 | `_loudness_dbfs` | 2 | 0 | ❌ |
| 106 | `_loudness_lufs` | 10 | 2 | ✅ |
| 119 | `_tanh_limit` | 2 | 0 | ✅ |
| 124 | `_try_numpy_dsp` | 18 | 1 | ✅ |
| 145 | `master_one` | 20 | 4 | ✅ |
| 168 | `master_all_stands` | 33 | 4 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 2 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 208** — print() вместо logger

  ```
        206 | 
        207 |     if len(sys.argv) > 2:
  >>>   208 |         print(master_all_stands(sys.argv[1], sys.argv[2]))
        209 |     else:
        210 |         print("usage: python -m modules.mastering <mix.wav> <out_dir>")
  ```

- **строка 210** — print() вместо logger

  ```
        208 |         print(master_all_stands(sys.argv[1], sys.argv[2]))
        209 |     else:
  >>>   210 |         print("usage: python -m modules.mastering <mix.wav> <out_dir>")
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 25** — import 'annotations' не используется в теле файла

  ```
         23 | """
         24 | 
  >>>    25 | from __future__ import annotations
         26 | 
         27 | import os
  ```

### SILENT_EXCEPT_PASS — 1 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 114** — except: pass — тихое подавление ошибок

  ```
        112 |             mono = y.mean(axis=1) if y.ndim > 1 else y
        113 |             return float(meter.integrated_loudness(mono))
  >>>   114 |         except Exception:
        115 |             pass
        116 |     return _loudness_dbfs(y) - 3.0
  ```
