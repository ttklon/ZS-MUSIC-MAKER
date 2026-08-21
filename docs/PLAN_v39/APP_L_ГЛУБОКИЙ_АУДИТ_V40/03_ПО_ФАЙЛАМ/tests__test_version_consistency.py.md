# АУДИТ ФАЙЛА: `tests/test_version_consistency.py`

**LOC:** 64  |  **Размер:** 1801 байт  |  **Проблем:** 1  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 3 | `__future__.annotations` | from |
| 5 | `json` | import |
| 6 | `subprocess` | import |
| 7 | `sys` | import |
| 8 | `pathlib.Path` | from |
| 26 | `app.version_info.__version__` | from |
| 15 | `tomllib` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 13 | `_version_from_pyproject` | 9 | 2 | ❌ |
| 25 | `_version_from_app` | 3 | 0 | ❌ |
| 31 | `test_version_json_matches_app_version_info` | 2 | 0 | ❌ |
| 36 | `test_pyproject_static_version_if_present_matches` | 4 | 1 | ❌ |
| 43 | `test_cli_version_exit_zero` | 6 | 0 | ❌ |
| 52 | `test_cli_version_shows_config_path` | 6 | 0 | ❌ |
| 61 | `test_build_id_mentions_version` | 3 | 0 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 3** — import 'annotations' не используется в теле файла

  ```
          1 | # -*- coding: utf-8 -*-
          2 | """ZS Music Maker — единый источник версии (ШАГ 009)."""
  >>>     3 | from __future__ import annotations
          4 | 
          5 | import json
  ```
