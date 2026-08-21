# АУДИТ ФАЙЛА: `modules/auto_qa.py`

**LOC:** 204  |  **Размер:** 7642 байт  |  **Проблем:** 2  |  **Risk score:** 3

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 21 | `__future__.annotations` | from |
| 23 | `json` | import |
| 24 | `math` | import |
| 25 | `time` | import |
| 26 | `pathlib.Path` | from |
| 35 | `numpy` | import |
| 58 | `librosa` | import |
| 59 | `numpy` | import |
| 105 | `modules.ai_detector_pro.analyze_track` | from |
| 131 | `soundfile` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 33 | `_loudness` | 19 | 1 | ✅ |
| 55 | `_structure_check` | 29 | 5 | ✅ |
| 87 | `audit_track` | 101 | 13 | ✅ |
| 191 | `should_retry` | 13 | 2 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 21** — import 'annotations' не используется в теле файла

  ```
         19 | """
         20 | 
  >>>    21 | from __future__ import annotations
         22 | 
         23 | import json
  ```

### LONG_FUNCTION — 1 шт. — 🟡 MEDIUM
**Смысл:** Функция > 100 LOC — сложно тестировать/поддерживать
**Fix:** Декомпозировать: приватные `_helper()`, тестировать по частям.

- **строка 87** — audit_track: 101 LOC (>100) — декомпозиция

  ```
         85 | 
         86 | 
  >>>    87 | def audit_track(master_wav: str | Path, target_lufs: float = -9.0) -> dict:
         88 |     """
         89 |     Полный аудит финального трека. Возвращает dict с 3 блоками:
  ```
