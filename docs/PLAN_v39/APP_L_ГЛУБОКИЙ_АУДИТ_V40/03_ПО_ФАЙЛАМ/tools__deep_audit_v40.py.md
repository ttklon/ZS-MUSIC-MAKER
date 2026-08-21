# АУДИТ ФАЙЛА: `tools/deep_audit_v40.py`

**LOC:** 281  |  **Размер:** 11400 байт  |  **Проблем:** 11  |  **Risk score:** 5

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 22 | `__future__.annotations` | from |
| 24 | `ast` | import |
| 25 | `json` | import |
| 26 | `re` | import |
| 27 | `collections.Counter` | from |
| 28 | `pathlib.Path` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 33 | `all_py_files` | 8 | 3 | ❌ |
| 44 | `read_src` | 7 | 2 | ❌ |
| 54 | `audit_file` | 202 | 60 | ❌ |
| 259 | `main` | 18 | 4 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 4 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 273** — print() вместо logger

  ```
        271 |         for it in r["issues"]:
        272 |             stats[it["kind"]] += 1
  >>>   273 |     print("=== AUDIT STATS ===")
        274 |     for k, v in stats.most_common():
        275 |         print(f"  {k:32s}  {v}")
  ```

- **строка 275** — print() вместо logger

  ```
        273 |     print("=== AUDIT STATS ===")
        274 |     for k, v in stats.most_common():
  >>>   275 |         print(f"  {k:32s}  {v}")
        276 |     print(f"Total files: {len(reports)}")
        277 |     print(f"Total issues: {sum(stats.values())}")
  ```

- **строка 276** — print() вместо logger

  ```
        274 |     for k, v in stats.most_common():
        275 |         print(f"  {k:32s}  {v}")
  >>>   276 |     print(f"Total files: {len(reports)}")
        277 |     print(f"Total issues: {sum(stats.values())}")
        278 | 
  ```

- **строка 277** — print() вместо logger

  ```
        275 |         print(f"  {k:32s}  {v}")
        276 |     print(f"Total files: {len(reports)}")
  >>>   277 |     print(f"Total issues: {sum(stats.values())}")
        278 | 
        279 | 
  ```

### MISSING_DOCSTRING — 2 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 54** — public function 'audit_file' без docstring

  ```
         52 | 
         53 | 
  >>>    54 | def audit_file(p: Path) -> dict:
         55 |     src = read_src(p)
         56 |     lines = src.splitlines()
  ```

- **строка 259** — public function 'main' без docstring

  ```
        257 | 
        258 | 
  >>>   259 | def main():
        260 |     files = all_py_files()
        261 |     reports = []
  ```

### BLOCKING_SLEEP — 2 шт. — 🟢 LOW
**Смысл:** time.sleep() без комментария/аргументации
**Fix:** Комментарий или await asyncio.sleep().

- **строка 17** — time.sleep(...) без пояснения

  ```
         15 |   • сложность (упрощённо: количество if/for/while/try)
         16 |   • голые print (не через logger)
  >>>    17 |   • голые time.sleep() без комментария
         18 |   • assert в production-коде
         19 |   • риски безопасности: eval/exec/os.system/subprocess.shell=True
  ```

- **строка 249** — time.sleep(...) без пояснения

  ```
        247 |             report["issues"].append(
        248 |                 {"line": i, "kind": "BLOCKING_SLEEP",
  >>>   249 |                  "msg": "time.sleep(...) без пояснения"}
        250 |             )
        251 |         if re.match(r"^\s*global\s+\w", line):
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 22** — import 'annotations' не используется в теле файла

  ```
         20 |   • отсутствие явных таймаутов у HTTP-запросов
         21 | """
  >>>    22 | from __future__ import annotations
         23 | 
         24 | import ast
  ```

### LONG_FUNCTION — 1 шт. — 🟡 MEDIUM
**Смысл:** Функция > 100 LOC — сложно тестировать/поддерживать
**Fix:** Декомпозировать: приватные `_helper()`, тестировать по частям.

- **строка 54** — audit_file: 202 LOC (>100) — декомпозиция

  ```
         52 | 
         53 | 
  >>>    54 | def audit_file(p: Path) -> dict:
         55 |     src = read_src(p)
         56 |     lines = src.splitlines()
  ```

### HIGH_COMPLEXITY — 1 шт. — 🟡 MEDIUM
**Смысл:** Цикломатическая сложность > 15
**Fix:** Разбить на подфункции; if-цепочки → dict-диспатчер.

- **строка 54** — audit_file: сложность ≈ 60 (>15)

  ```
         52 | 
         53 | 
  >>>    54 | def audit_file(p: Path) -> dict:
         55 |     src = read_src(p)
         56 |     lines = src.splitlines()
  ```
