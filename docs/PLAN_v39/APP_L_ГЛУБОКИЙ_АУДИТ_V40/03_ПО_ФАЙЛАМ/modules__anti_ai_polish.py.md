# АУДИТ ФАЙЛА: `modules/anti_ai_polish.py`

**LOC:** 317  |  **Размер:** 10902 байт  |  **Проблем:** 3  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 23 | `__future__.annotations` | from |
| 25 | `math` | import |
| 26 | `random` | import |
| 27 | `time` | import |
| 28 | `pathlib.Path` | from |
| 31 | `numpy` | import |
| 36 | `soundfile` | import |
| 305 | `sys` | import |
| 315 | `json` | import |
| 134 | `scipy.signal` | import |
| 186 | `scipy.interpolate.interp1d` | from |
| 220 | `scipy.signal` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 44 | `_read` | 4 | 1 | ❌ |
| 51 | `_write` | 2 | 0 | ❌ |
| 57 | `_micro_timing_jitter` | 20 | 6 | ❌ |
| 80 | `_breath_insert` | 21 | 8 | ❌ |
| 104 | `_section_dynamics_variation` | 19 | 8 | ❌ |
| 126 | `_ghost_harmonies_kill` | 22 | 6 | ✅ |
| 151 | `_formulaic_structure_bust` | 18 | 5 | ❌ |
| 172 | `_tape_saturation` | 4 | 1 | ❌ |
| 179 | `_imperfect_tuning` | 34 | 4 | ✅ |
| 216 | `_lofi_pass` | 13 | 4 | ❌ |
| 233 | `polish_track` | 68 | 11 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 2 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 308** — print() вместо logger

  ```
        306 | 
        307 |     if len(sys.argv) < 3:
  >>>   308 |         print("usage: python anti_ai_polish.py <in.wav> <out.wav> [preset]")
        309 |         sys.exit(1)
        310 |     r = polish_track(
  ```

- **строка 317** — print() вместо logger

  ```
        315 |     import json
        316 | 
  >>>   317 |     print(json.dumps(r, ensure_ascii=False, indent=2))
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 23** — import 'annotations' не используется в теле файла

  ```
         21 | """
         22 | 
  >>>    23 | from __future__ import annotations
         24 | 
         25 | import math
  ```
