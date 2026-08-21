# АУДИТ ФАЙЛА: `tools/fallback_audit.py`

**LOC:** 171  |  **Размер:** 6571 байт  |  **Проблем:** 5  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 11 | `__future__.annotations` | from |
| 13 | `json` | import |
| 14 | `re` | import |
| 15 | `pathlib.Path` | from |
| 16 | `typing.Any` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 44 | `_is_hard_refusal` | 16 | 2 | ✅ |
| 63 | `scan_file` | 41 | 7 | ❌ |
| 107 | `scan_all` | 39 | 9 | ❌ |
| 149 | `main` | 18 | 0 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### MISSING_DOCSTRING — 3 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 63** — public function 'scan_file' без docstring

  ```
         61 | 
         62 | 
  >>>    63 | def scan_file(path: Path) -> dict[str, list[dict[str, Any]]]:
         64 |     rel = str(path.relative_to(ROOT))
         65 |     if rel in SELF_SKIP:
  ```

- **строка 107** — public function 'scan_all' без docstring

  ```
        105 | 
        106 | 
  >>>   107 | def scan_all() -> dict[str, Any]:
        108 |     all_hits: dict[str, list[dict[str, Any]]] = {}
        109 |     files_scanned = 0
  ```

- **строка 149** — public function 'main' без docstring

  ```
        147 | 
        148 | 
  >>>   149 | def main() -> int:
        150 |     r = scan_all()
        151 |     out_dir = ROOT / "output" / "audit_v14"
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 11** — import 'annotations' не используется в теле файла

  ```
          9 | """
         10 | 
  >>>    11 | from __future__ import annotations
         12 | 
         13 | import json
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 155** — print() вместо logger

  ```
        153 |     out = out_dir / "fallback_report.json"
        154 |     out.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
  >>>   155 |     print(
        156 |         json.dumps(
        157 |             {
  ```
