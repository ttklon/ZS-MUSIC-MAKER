# АУДИТ ФАЙЛА: `modules/global_audit_fixer.py`

**LOC:** 35  |  **Размер:** 1405 байт  |  **Проблем:** 1  |  **Risk score:** 0

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 7 | `logging` | import |
| 8 | `json` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 12 | `audit_system_integrity` | 20 | 0 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 35** — print() вместо logger

  ```
         33 | 
         34 | if __name__ == "__main__":
  >>>    35 |     print(json.dumps(audit_system_integrity(), indent=2))
  ```
