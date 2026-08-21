# АУДИТ ФАЙЛА: `tools/ast_dead_imports.py`

**LOC:** 124  |  **Размер:** 4507 байт  |  **Проблем:** 7  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 22 | `__future__.annotations` | from |
| 24 | `ast` | import |
| 25 | `sys` | import |
| 26 | `pathlib.Path` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 35 | `_top_level_imports` | 20 | 13 | ✅ |
| 58 | `_used_names_and_attr_roots` | 8 | 4 | ✅ |
| 69 | `scan_file` | 10 | 1 | ❌ |
| 82 | `scan_all` | 22 | 8 | ❌ |
| 107 | `main` | 13 | 4 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 4 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 111** — print() вместо logger

  ```
        109 |     report = scan_all(dirs)
        110 |     if not report:
  >>>   111 |         print("AST dead-imports: CLEAN (0)")
        112 |         return 0
        113 |     print("AST dead-imports: FOUND")
  ```

- **строка 113** — print() вместо logger

  ```
        111 |         print("AST dead-imports: CLEAN (0)")
        112 |         return 0
  >>>   113 |     print("AST dead-imports: FOUND")
        114 |     total = 0
        115 |     for rel, items in sorted(report.items()):
  ```

- **строка 117** — print() вместо logger

  ```
        115 |     for rel, items in sorted(report.items()):
        116 |         for lineno, name in items:
  >>>   117 |             print(f"  {rel}:{lineno}  {name}")
        118 |             total += 1
        119 |     print(f"total: {total}")
  ```

- **строка 119** — print() вместо logger

  ```
        117 |             print(f"  {rel}:{lineno}  {name}")
        118 |             total += 1
  >>>   119 |     print(f"total: {total}")
        120 |     return 1
        121 | 
  ```

### MISSING_DOCSTRING — 2 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 82** — public function 'scan_all' без docstring

  ```
         80 | 
         81 | 
  >>>    82 | def scan_all(dirs: list[str]) -> dict[str, list[tuple[int, str]]]:
         83 |     report: dict[str, list[tuple[int, str]]] = {}
         84 |     files: list[Path] = []
  ```

- **строка 107** — public function 'main' без docstring

  ```
        105 | 
        106 | 
  >>>   107 | def main() -> int:
        108 |     dirs = sys.argv[1:] or DEFAULT_DIRS
        109 |     report = scan_all(dirs)
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 22** — import 'annotations' не используется в теле файла

  ```
         20 | Exit code: 0 если чисто, 1 если есть кандидаты.
         21 | """
  >>>    22 | from __future__ import annotations
         23 | 
         24 | import ast
  ```
