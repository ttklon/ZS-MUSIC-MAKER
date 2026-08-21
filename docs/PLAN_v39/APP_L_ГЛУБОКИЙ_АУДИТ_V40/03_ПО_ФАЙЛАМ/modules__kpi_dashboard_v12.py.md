# АУДИТ ФАЙЛА: `modules/kpi_dashboard_v12.py`

**LOC:** 411  |  **Размер:** 17728 байт  |  **Проблем:** 10  |  **Risk score:** 7

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 18 | `__future__.annotations` | from |
| 20 | `json` | import |
| 21 | `time` | import |
| 22 | `dataclasses.asdict` | from |
| 22 | `dataclasses.dataclass` | from |
| 22 | `dataclasses.field` | from |
| 23 | `pathlib.Path` | from |
| 24 | `typing.Any` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 86 | `_load_json` | 4 | 1 | ❌ |
| 93 | `_newest` | 4 | 1 | ❌ |
| 100 | `_health_section` | 23 | 3 | ❌ |
| 126 | `_pipeline_section` | 26 | 2 | ❌ |
| 155 | `_smoke_section` | 19 | 2 | ❌ |
| 177 | `_tz_percent` | 117 | 18 | ✅ |
| 297 | `build` | 51 | 7 | ❌ |
| 351 | `render_markdown` | 26 | 5 | ❌ |
| 380 | `render_text` | 21 | 5 | ❌ |
| 404 | `main` | 3 | 0 | ❌ |
| 82 | `as_dict` | 1 | 0 | ❌ |
| 208 | `has` | 1 | 0 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 66 | `DashboardSection` | ❌ |
| 74 | `Dashboard` | ❌ |

## Проблемы (детально, с цитатой кода)

### MISSING_DOCSTRING — 3 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 297** — public function 'build' без docstring

  ```
        295 | 
        296 | 
  >>>   297 | def build(save: bool = True) -> Dashboard:
        298 |     health = _load_json(ROOT / "data" / "health_v12.json")
        299 |     pipe_path = _newest("master_pipeline_v12.json", ROOT / "output")
  ```

- **строка 351** — public function 'render_markdown' без docstring

  ```
        349 | 
        350 | 
  >>>   351 | def render_markdown(dash: Dashboard) -> str:
        352 |     lines = [
        353 |         "# KPI Dashboard v12 «Hit Locked Pro»",
  ```

- **строка 380** — public function 'render_text' без docstring

  ```
        378 | 
        379 | 
  >>>   380 | def render_text(dash: Dashboard) -> str:
        381 |     out = [
        382 |         "=" * 72,
  ```

### MISSING_CLASS_DOCSTRING — 2 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 66** — public class 'DashboardSection' без docstring

  ```
         64 | 
         65 | @dataclass
  >>>    66 | class DashboardSection:
         67 |     title: str
         68 |     ok: bool
  ```

- **строка 74** — public class 'Dashboard' без docstring

  ```
         72 | 
         73 | @dataclass
  >>>    74 | class Dashboard:
         75 |     generated_at: str = ""
         76 |     percent_tz: int = 0
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

### LONG_FUNCTION — 1 шт. — 🟡 MEDIUM
**Смысл:** Функция > 100 LOC — сложно тестировать/поддерживать
**Fix:** Декомпозировать: приватные `_helper()`, тестировать по частям.

- **строка 177** — _tz_percent: 117 LOC (>100) — декомпозиция

  ```
        175 | 
        176 | 
  >>>   177 | def _tz_percent(
        178 |     health: dict[str, Any] | None,
        179 |     pipe: dict[str, Any] | None,
  ```

### HIGH_COMPLEXITY — 1 шт. — 🟡 MEDIUM
**Смысл:** Цикломатическая сложность > 15
**Fix:** Разбить на подфункции; if-цепочки → dict-диспатчер.

- **строка 177** — _tz_percent: сложность ≈ 18 (>15)

  ```
        175 | 
        176 | 
  >>>   177 | def _tz_percent(
        178 |     health: dict[str, Any] | None,
        179 |     pipe: dict[str, Any] | None,
  ```

### SILENT_EXCEPT_PASS — 1 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 346** — except: pass — тихое подавление ошибок

  ```
        344 |                 render_markdown(dash), encoding="utf-8"
        345 |             )
  >>>   346 |         except Exception:
        347 |             pass
        348 |     return dash
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 406** — print() вместо logger

  ```
        404 | def main() -> int:
        405 |     dash = build()
  >>>   406 |     print(render_text(dash))
        407 |     return 0 if dash.verdict == "GREEN" else (1 if dash.verdict == "YELLOW" else 2)
        408 | 
  ```
