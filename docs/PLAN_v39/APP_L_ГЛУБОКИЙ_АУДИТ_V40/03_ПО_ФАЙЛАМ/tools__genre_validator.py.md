# АУДИТ ФАЙЛА: `tools/genre_validator.py`

**LOC:** 53  |  **Размер:** 1903 байт  |  **Проблем:** 6  |  **Risk score:** 0

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 9 | `sys` | import |
| 10 | `pathlib.Path` | from |
| 15 | `modules.genre_engine.StyleRegistry` | from |
| 15 | `modules.genre_engine.GenreFactory` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 17 | `validate_all` | 32 | 7 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 5 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 18** — print() вместо logger

  ```
         16 | 
         17 | def validate_all():
  >>>    18 |     print("=== Genre Integrity Audit (100+ Styles) ===")
         19 |     reg = StyleRegistry()
         20 |     factory = GenreFactory(reg)
  ```

- **строка 23** — print() вместо logger

  ```
         21 | 
         22 |     genres = reg.list_genres()
  >>>    23 |     print(f"Total genres found: {len(genres)}")
         24 | 
         25 |     errors = []
  ```

- **строка 43** — print() вместо logger

  ```
         41 | 
         42 |     if not errors:
  >>>    43 |         print("✅ All 119+ genres are VALID and BATTLE-READY.")
         44 |         return True
         45 |     else:
  ```

- **строка 46** — print() вместо logger

  ```
         44 |         return True
         45 |     else:
  >>>    46 |         print(f"❌ Found {len(errors)} issues:")
         47 |         for err in errors:
         48 |             print(f"  - {err}")
  ```

- **строка 48** — print() вместо logger

  ```
         46 |         print(f"❌ Found {len(errors)} issues:")
         47 |         for err in errors:
  >>>    48 |             print(f"  - {err}")
         49 |         return False
         50 | 
  ```

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 17** — public function 'validate_all' без docstring

  ```
         15 | from modules.genre_engine import StyleRegistry, GenreFactory
         16 | 
  >>>    17 | def validate_all():
         18 |     print("=== Genre Integrity Audit (100+ Styles) ===")
         19 |     reg = StyleRegistry()
  ```
