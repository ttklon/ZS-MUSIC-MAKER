# АУДИТ ФАЙЛА: `modules/mastering_v9.py`

**LOC:** 281  |  **Размер:** 8914 байт  |  **Проблем:** 3  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 18 | `__future__.annotations` | from |
| 20 | `json` | import |
| 21 | `math` | import |
| 22 | `pathlib.Path` | from |
| 25 | `numpy` | import |
| 30 | `soundfile` | import |
| 37 | `scipy.signal` | import |
| 44 | `matchering` | import |
| 264 | `sys` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 52 | `_read` | 4 | 1 | ❌ |
| 59 | `_write` | 2 | 0 | ❌ |
| 64 | `_rms` | 1 | 0 | ❌ |
| 68 | `measure` | 25 | 4 | ✅ |
| 97 | `_apply_gain` | 3 | 1 | ❌ |
| 103 | `_soft_limit` | 4 | 1 | ❌ |
| 110 | `_eq_shelf` | 31 | 6 | ❌ |
| 144 | `_widen_stereo` | 8 | 2 | ❌ |
| 178 | `render_stand` | 49 | 8 | ✅ |
| 230 | `render_all_stands` | 7 | 1 | ❌ |
| 241 | `match_to_reference` | 18 | 3 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 2 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 267** — print() вместо logger

  ```
        265 | 
        266 |     if len(sys.argv) < 3:
  >>>   267 |         print("usage: python mastering_v9.py <in.wav> <out_dir>")
        268 |         sys.exit(1)
        269 |     r = render_all_stands(sys.argv[1], sys.argv[2])
  ```

- **строка 270** — print() вместо logger

  ```
        268 |         sys.exit(1)
        269 |     r = render_all_stands(sys.argv[1], sys.argv[2])
  >>>   270 |     print(
        271 |         json.dumps(
        272 |             {
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 18** — import 'annotations' не используется в теле файла

  ```
         16 | """
         17 | 
  >>>    18 | from __future__ import annotations
         19 | 
         20 | import json
  ```
