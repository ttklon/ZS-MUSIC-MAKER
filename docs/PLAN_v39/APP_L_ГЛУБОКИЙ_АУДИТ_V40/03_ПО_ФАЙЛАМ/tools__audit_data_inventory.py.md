# АУДИТ ФАЙЛА: `tools/audit_data_inventory.py`

**LOC:** 136  |  **Размер:** 5148 байт  |  **Проблем:** 6  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 12 | `__future__.annotations` | from |
| 14 | `argparse` | import |
| 15 | `json` | import |
| 16 | `pathlib.Path` | from |
| 17 | `typing.Any` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 40 | `classify_data_file` | 7 | 3 | ✅ |
| 50 | `_validate_jsonl` | 8 | 3 | ❌ |
| 61 | `validate_data_file` | 14 | 5 | ✅ |
| 78 | `scan_data` | 32 | 5 | ✅ |
| 113 | `main` | 19 | 4 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 4 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 120** — print() вместо logger

  ```
        118 | 
        119 |     if args.json:
  >>>   120 |         print(json.dumps(report, ensure_ascii=False, indent=2))
        121 |     else:
        122 |         print(
  ```

- **строка 122** — print() вместо logger

  ```
        120 |         print(json.dumps(report, ensure_ascii=False, indent=2))
        121 |     else:
  >>>   122 |         print(
        123 |             "data inventory: "
        124 |             f"files={len(report['files'])} managed={report['managed_count']} "
  ```

- **строка 128** — print() вместо logger

  ```
        126 |         )
        127 |         for entry in report["invalid"]:
  >>>   128 |             print(f"INVALID {entry['path']}: {entry['error']}")
        129 |         for path in report["unknown"]:
        130 |             print(f"UNKNOWN {path}")
  ```

- **строка 130** — print() вместо logger

  ```
        128 |             print(f"INVALID {entry['path']}: {entry['error']}")
        129 |         for path in report["unknown"]:
  >>>   130 |             print(f"UNKNOWN {path}")
        131 | 
        132 |     return 0 if not report["unknown"] and not report["invalid"] else 1
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 12** — import 'annotations' не используется в теле файла

  ```
         10 |     python tools/audit_data_inventory.py --json
         11 | """
  >>>    12 | from __future__ import annotations
         13 | 
         14 | import argparse
  ```

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 113** — public function 'main' без docstring

  ```
        111 | 
        112 | 
  >>>   113 | def main(argv: list[str] | None = None) -> int:
        114 |     parser = argparse.ArgumentParser(description="Validate and inventory versioned data assets")
        115 |     parser.add_argument("--json", action="store_true", help="print the complete report as JSON")
  ```
