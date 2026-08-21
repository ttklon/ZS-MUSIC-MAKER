# АУДИТ ФАЙЛА: `modules/onboarding_tour.py`

**LOC:** 213  |  **Размер:** 7691 байт  |  **Проблем:** 6  |  **Risk score:** 3

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 10 | `__future__.annotations` | from |
| 12 | `json` | import |
| 13 | `logging` | import |
| 14 | `pathlib.Path` | from |
| 15 | `typing.Any` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 20 | `_tour_state_path` | 18 | 5 | ✅ |
| 162 | `load_state` | 6 | 2 | ❌ |
| 171 | `save_state` | 3 | 0 | ❌ |
| 177 | `should_show` | 1 | 0 | ❌ |
| 181 | `steps` | 1 | 0 | ❌ |
| 185 | `get_step` | 3 | 1 | ❌ |
| 191 | `mark_done` | 1 | 0 | ❌ |
| 195 | `reset` | 1 | 0 | ❌ |
| 199 | `run_console_demo` | 10 | 2 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 4 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 204** — print() вместо logger

  ```
        202 |     """
        203 |     for i, step in enumerate(TOUR_STEPS):
  >>>   204 |         print(f"\n=== Шаг {i+1}/{len(TOUR_STEPS)}: {step['title']} ===")
        205 |         print(step["text"])
        206 |         if step.get("anchor"):
  ```

- **строка 205** — print() вместо logger

  ```
        203 |     for i, step in enumerate(TOUR_STEPS):
        204 |         print(f"\n=== Шаг {i+1}/{len(TOUR_STEPS)}: {step['title']} ===")
  >>>   205 |         print(step["text"])
        206 |         if step.get("anchor"):
        207 |             print(f"  → элемент интерфейса: {step['anchor']}")
  ```

- **строка 207** — print() вместо logger

  ```
        205 |         print(step["text"])
        206 |         if step.get("anchor"):
  >>>   207 |             print(f"  → элемент интерфейса: {step['anchor']}")
        208 |     mark_done()
        209 |     print("\nТур завершён.")
  ```

- **строка 209** — print() вместо logger

  ```
        207 |             print(f"  → элемент интерфейса: {step['anchor']}")
        208 |     mark_done()
  >>>   209 |     print("\nТур завершён.")
        210 | 
        211 | 
  ```

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

### SILENT_EXCEPT_PASS — 1 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 166** — except: pass — тихое подавление ошибок

  ```
        164 |         try:
        165 |             return json.loads(TOUR_STATE.read_text(encoding="utf-8"))
  >>>   166 |         except Exception:
        167 |             pass
        168 |     return {"tour_done": False, "last_step": 0}
  ```
