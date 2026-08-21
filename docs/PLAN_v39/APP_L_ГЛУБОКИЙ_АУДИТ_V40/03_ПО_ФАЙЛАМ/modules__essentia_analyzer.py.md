# АУДИТ ФАЙЛА: `modules/essentia_analyzer.py`

**LOC:** 172  |  **Размер:** 5601 байт  |  **Проблем:** 3  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 20 | `__future__.annotations` | from |
| 22 | `json` | import |
| 23 | `logging` | import |
| 24 | `pathlib.Path` | from |
| 25 | `typing.Any` | from |
| 30 | `essentia.standard` | import |
| 38 | `librosa` | import |
| 39 | `numpy` | import |
| 166 | `sys` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 45 | `analyze_advanced` | 17 | 3 | ✅ |
| 65 | `_analyze_essentia` | 48 | 0 | ❌ |
| 116 | `_analyze_librosa_fallback` | 40 | 3 | ❌ |
| 159 | `save_report` | 3 | 1 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 2 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 169** — print() вместо logger

  ```
        167 | 
        168 |     if len(sys.argv) < 2:
  >>>   169 |         print(json.dumps({"engine_available": ESSENTIA_OK}, ensure_ascii=False))
        170 |     else:
        171 |         rep = analyze_advanced(sys.argv[1])
  ```

- **строка 172** — print() вместо logger

  ```
        170 |     else:
        171 |         rep = analyze_advanced(sys.argv[1])
  >>>   172 |         print(json.dumps(rep, ensure_ascii=False, indent=2))
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 20** — import 'annotations' не используется в теле файла

  ```
         18 | """
         19 | 
  >>>    20 | from __future__ import annotations
         21 | 
         22 | import json
  ```
