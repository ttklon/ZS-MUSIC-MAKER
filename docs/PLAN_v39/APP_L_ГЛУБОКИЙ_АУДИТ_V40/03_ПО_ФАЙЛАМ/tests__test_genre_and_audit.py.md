# АУДИТ ФАЙЛА: `tests/test_genre_and_audit.py`

**LOC:** 33  |  **Размер:** 1076 байт  |  **Проблем:** 3  |  **Risk score:** 0

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 5 | `sys` | import |
| 6 | `os` | import |
| 10 | `modules.genre_expansion_100.get_genre_profile` | from |
| 10 | `modules.genre_expansion_100.list_all_supported_genres` | from |
| 11 | `modules.global_audit_fixer.audit_system_integrity` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 13 | `test_genre_expansion` | 9 | 0 | ❌ |
| 24 | `test_audit_fixer` | 4 | 0 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 3 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 22** — print() вместо logger

  ```
         20 |     profile_unknown = get_genre_profile("unknown_cyber_jazz")
         21 |     assert profile_unknown["bpm"] == 120
  >>>    22 |     print("Genre expansion tests passed successfully.")
         23 | 
         24 | def test_audit_fixer():
  ```

- **строка 28** — print() вместо logger

  ```
         26 |     assert report["status"] == "PASSED_WITH_SELF_HEALING"
         27 |     assert report["critical_issues_resolved"] == 10
  >>>    28 |     print("Global audit fixer tests passed successfully.")
         29 | 
         30 | if __name__ == "__main__":
  ```

- **строка 33** — print() вместо logger

  ```
         31 |     test_genre_expansion()
         32 |     test_audit_fixer()
  >>>    33 |     print("ALL TESTS PASSED.")
  ```
