# АУДИТ ФАЙЛА: `modules/ai_detector_pro.py`

**LOC:** 190  |  **Размер:** 8636 байт  |  **Проблем:** 4  |  **Risk score:** 5

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 12 | `__future__.annotations` | from |
| 14 | `os` | import |
| 185 | `sys` | import |
| 188 | `json` | import |
| 51 | `librosa` | import |
| 52 | `numpy` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 43 | `analyze_track` | 138 | 19 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 12** — import 'annotations' не используется в теле файла

  ```
         10 | """
         11 | 
  >>>    12 | from __future__ import annotations
         13 | 
         14 | import os
  ```

### LONG_FUNCTION — 1 шт. — 🟡 MEDIUM
**Смысл:** Функция > 100 LOC — сложно тестировать/поддерживать
**Fix:** Декомпозировать: приватные `_helper()`, тестировать по частям.

- **строка 43** — analyze_track: 138 LOC (>100) — декомпозиция

  ```
         41 | 
         42 | 
  >>>    43 | def analyze_track(audio_path: str) -> dict:
         44 |     """
         45 |     Основная функция. Возвращает JSON с метриками, вердиктом и советами.
  ```

### HIGH_COMPLEXITY — 1 шт. — 🟡 MEDIUM
**Смысл:** Цикломатическая сложность > 15
**Fix:** Разбить на подфункции; if-цепочки → dict-диспатчер.

- **строка 43** — analyze_track: сложность ≈ 19 (>15)

  ```
         41 | 
         42 | 
  >>>    43 | def analyze_track(audio_path: str) -> dict:
         44 |     """
         45 |     Основная функция. Возвращает JSON с метриками, вердиктом и советами.
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 190** — print() вместо logger

  ```
        188 |     import json
        189 | 
  >>>   190 |     print(json.dumps(r, ensure_ascii=False, indent=2))
  ```
