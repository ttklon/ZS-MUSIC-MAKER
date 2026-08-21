# АУДИТ ФАЙЛА: `modules/track_templates.py`

**LOC:** 99  |  **Размер:** 2703 байт  |  **Проблем:** 2  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 10 | `__future__.annotations` | from |
| 12 | `json` | import |
| 13 | `time` | import |
| 14 | `uuid` | import |
| 15 | `pathlib.Path` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 25 | `_load_history` | 6 | 2 | ❌ |
| 34 | `_save_history` | 3 | 0 | ❌ |
| 41 | `save_template` | 11 | 0 | ❌ |
| 55 | `list_templates` | 8 | 2 | ❌ |
| 66 | `load_template` | 7 | 2 | ❌ |
| 76 | `delete_template` | 5 | 1 | ❌ |
| 85 | `push_history` | 6 | 0 | ❌ |
| 94 | `get_history` | 1 | 0 | ❌ |
| 98 | `clear_history` | 1 | 0 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 10** — import 'annotations' не используется в теле файла

  ```
          8 | """
          9 | 
  >>>    10 | from __future__ import annotations
         11 | 
         12 | import json
  ```

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 41** — public function 'save_template' без docstring

  ```
         39 | 
         40 | # ------------------------------------------------------- templates
  >>>    41 | def save_template(name: str, recipe: dict) -> str:
         42 |     tid = uuid.uuid4().hex[:10]
         43 |     data = {
  ```
