# АУДИТ ФАЙЛА: `tests/test_ast_dead_imports.py`

**LOC:** 49  |  **Размер:** 1502 байт  |  **Проблем:** 1  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 3 | `__future__.annotations` | from |
| 5 | `sys` | import |
| 6 | `pathlib.Path` | from |
| 10 | `tools.ast_dead_imports.DEFAULT_DIRS` | from |
| 10 | `tools.ast_dead_imports.scan_all` | from |
| 10 | `tools.ast_dead_imports.scan_file` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 13 | `test_scan_finds_dead_import` | 6 | 0 | ❌ |
| 22 | `test_scan_ignores_noqa_import` | 4 | 0 | ❌ |
| 29 | `test_scan_keeps_attr_root` | 6 | 0 | ❌ |
| 38 | `test_scan_line_with_two_imports` | 6 | 0 | ❌ |
| 47 | `test_repo_is_clean_of_dead_imports` | 2 | 0 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 3** — import 'annotations' не используется в теле файла

  ```
          1 | # -*- coding: utf-8 -*-
          2 | """ZS Music Maker — AST dead-imports аудит (ШАГ 010)."""
  >>>     3 | from __future__ import annotations
          4 | 
          5 | import sys
  ```
