# АУДИТ ФАЙЛА: `modules/arrangement_engine.py`

**LOC:** 325  |  **Размер:** 12120 байт  |  **Проблем:** 4  |  **Risk score:** 5

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 23 | `__future__.annotations` | from |
| 25 | `json` | import |
| 26 | `random` | import |
| 27 | `time` | import |
| 28 | `pathlib.Path` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 120 | `_pick` | 5 | 2 | ❌ |
| 128 | `_bars_to_seconds` | 1 | 0 | ❌ |
| 132 | `_clamp` | 1 | 0 | ❌ |
| 137 | `build_arrangement` | 152 | 24 | ✅ |
| 292 | `_guess_genre` | 12 | 5 | ❌ |
| 307 | `save_plan` | 5 | 0 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 23** — import 'annotations' не используется в теле файла

  ```
         21 | """
         22 | 
  >>>    23 | from __future__ import annotations
         24 | 
         25 | import json
  ```

### LONG_FUNCTION — 1 шт. — 🟡 MEDIUM
**Смысл:** Функция > 100 LOC — сложно тестировать/поддерживать
**Fix:** Декомпозировать: приватные `_helper()`, тестировать по частям.

- **строка 137** — build_arrangement: 152 LOC (>100) — декомпозиция

  ```
        135 | 
        136 | # ============================================================ main API
  >>>   137 | def build_arrangement(
        138 |     style_vector: dict,
        139 |     total_seconds: float = 150.0,
  ```

### HIGH_COMPLEXITY — 1 шт. — 🟡 MEDIUM
**Смысл:** Цикломатическая сложность > 15
**Fix:** Разбить на подфункции; if-цепочки → dict-диспатчер.

- **строка 137** — build_arrangement: сложность ≈ 24 (>15)

  ```
        135 | 
        136 | # ============================================================ main API
  >>>   137 | def build_arrangement(
        138 |     style_vector: dict,
        139 |     total_seconds: float = 150.0,
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 325** — print() вместо logger

  ```
        323 |     }
        324 |     p = build_arrangement(sv, total_seconds=180, seed=42, variant=1)
  >>>   325 |     print(json.dumps(p, ensure_ascii=False, indent=2)[:3000])
  ```
