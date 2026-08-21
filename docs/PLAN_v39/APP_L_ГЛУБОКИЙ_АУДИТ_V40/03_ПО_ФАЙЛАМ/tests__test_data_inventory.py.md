# АУДИТ ФАЙЛА: `tests/test_data_inventory.py`

**LOC:** 27  |  **Размер:** 940 байт  |  **Проблем:** 2  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 3 | `__future__.annotations` | from |
| 5 | `tools.audit_data_inventory.scan_data` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 8 | `test_repository_data_inventory_is_clean` | 5 | 0 | ❌ |
| 16 | `test_inventory_reports_unknown_and_invalid_assets` | 11 | 0 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 3** — import 'annotations' не используется в теле файла

  ```
          1 | # -*- coding: utf-8 -*-
          2 | """Регрессии для versioned-каталога data и его статического аудита."""
  >>>     3 | from __future__ import annotations
          4 | 
          5 | from tools.audit_data_inventory import scan_data
  ```

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 16** — public function 'test_inventory_reports_unknown_and_invalid_assets' без docstring

  ```
         14 | 
         15 | 
  >>>    16 | def test_inventory_reports_unknown_and_invalid_assets(tmp_path) -> None:
         17 |     (tmp_path / "genre_presets").mkdir()
         18 |     (tmp_path / "genre_presets" / "valid.json").write_text("{}", encoding="utf-8")
  ```
