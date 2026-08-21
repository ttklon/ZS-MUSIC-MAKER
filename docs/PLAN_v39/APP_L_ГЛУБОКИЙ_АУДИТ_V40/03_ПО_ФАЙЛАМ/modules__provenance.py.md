# АУДИТ ФАЙЛА: `modules/provenance.py`

**LOC:** 142  |  **Размер:** 4711 байт  |  **Проблем:** 1  |  **Risk score:** 0

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 7 | `json` | import |
| 8 | `os` | import |
| 9 | `time` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 62 | `_load` | 6 | 2 | ❌ |
| 71 | `_save` | 1 | 0 | ❌ |
| 75 | `add_sample` | 26 | 1 | ✅ |
| 104 | `list_samples` | 1 | 0 | ❌ |
| 108 | `check_commercial_safe` | 17 | 0 | ✅ |
| 128 | `generate_attribution_text` | 10 | 2 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 142** — print() вместо logger

  ```
        140 | 
        141 | if __name__ == "__main__":
  >>>   142 |     print(json.dumps(check_commercial_safe(), ensure_ascii=False, indent=2))
  ```
