# АУДИТ ФАЙЛА: `agents/training_texts.py`

**LOC:** 140  |  **Размер:** 9884 байт  |  **Проблем:** 1  |  **Risk score:** 0

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 8 | `json` | import |
| 9 | `os` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 69 | `get_next_text` | 27 | 1 | ✅ |
| 99 | `_styles_remaining` | 1 | 0 | ❌ |
| 103 | `_instruction` | 10 | 0 | ❌ |
| 116 | `all_styles` | 1 | 0 | ❌ |
| 120 | `progress_summary` | 16 | 1 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 140** — print() вместо logger

  ```
        138 | 
        139 | if __name__ == "__main__":
  >>>   140 |     print(json.dumps(get_next_text(), ensure_ascii=False, indent=2))
  ```
