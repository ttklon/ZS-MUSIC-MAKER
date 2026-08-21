# АУДИТ ФАЙЛА: `modules/self_diag_v13.py`

**LOC:** 333  |  **Размер:** 13068 байт  |  **Проблем:** 5  |  **Risk score:** 3

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 29 | `__future__.annotations` | from |
| 31 | `json` | import |
| 32 | `os` | import |
| 33 | `sys` | import |
| 34 | `time` | import |
| 35 | `pathlib.Path` | from |
| 36 | `typing.Any` | from |
| 47 | `ctypes` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 56 | `_c` | 1 | 0 | ❌ |
| 89 | `_read_json_silent` | 4 | 1 | ❌ |
| 96 | `check_layout` | 38 | 4 | ✅ |
| 137 | `check_health` | 1 | 0 | ❌ |
| 141 | `check_kpi` | 1 | 0 | ❌ |
| 145 | `check_smoke_recent` | 8 | 2 | ❌ |
| 156 | `collect_action_plan` | 77 | 26 | ✅ |
| 236 | `render_report` | 55 | 8 | ❌ |
| 294 | `run` | 30 | 1 | ❌ |
| 327 | `main_entry` | 2 | 0 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### MISSING_DOCSTRING — 2 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 236** — public function 'render_report' без docstring

  ```
        234 | 
        235 | 
  >>>   236 | def render_report(
        237 |     layout: list[dict[str, Any]],
        238 |     health: dict[str, Any] | None,
  ```

- **строка 294** — public function 'run' без docstring

  ```
        292 | 
        293 | 
  >>>   294 | def run(save_to_log: bool = True) -> dict[str, Any]:
        295 |     layout = check_layout()
        296 |     health = check_health()
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 29** — import 'annotations' не используется в теле файла

  ```
         27 | """
         28 | 
  >>>    29 | from __future__ import annotations
         30 | 
         31 | import json
  ```

### HIGH_COMPLEXITY — 1 шт. — 🟡 MEDIUM
**Смысл:** Цикломатическая сложность > 15
**Fix:** Разбить на подфункции; if-цепочки → dict-диспатчер.

- **строка 156** — collect_action_plan: сложность ≈ 26 (>15)

  ```
        154 | 
        155 | 
  >>>   156 | def collect_action_plan(
        157 |     layout: list[dict[str, Any]],
        158 |     health: dict[str, Any] | None,
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 302** — print() вместо logger

  ```
        300 | 
        301 |     report = render_report(layout, health, kpi, smoke, plan)
  >>>   302 |     print(report)
        303 | 
        304 |     out = {
  ```
