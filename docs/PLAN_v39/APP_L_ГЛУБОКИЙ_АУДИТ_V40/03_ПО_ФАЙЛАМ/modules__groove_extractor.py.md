# АУДИТ ФАЙЛА: `modules/groove_extractor.py`

**LOC:** 234  |  **Размер:** 8823 байт  |  **Проблем:** 4  |  **Risk score:** 4

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 11 | `json` | import |
| 12 | `os` | import |
| 14 | `numpy` | import |
| 17 | `librosa` | import |
| 229 | `sys` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 22 | `extract_groove` | 160 | 22 | ✅ |
| 185 | `merge_grooves` | 40 | 6 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 2 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 232** — print() вместо logger

  ```
        230 | 
        231 |     if len(sys.argv) < 2:
  >>>   232 |         print("Usage: python groove_extractor.py <track.mp3>")
        233 |     else:
        234 |         print(json.dumps(extract_groove(sys.argv[1]), ensure_ascii=False, indent=2))
  ```

- **строка 234** — print() вместо logger

  ```
        232 |         print("Usage: python groove_extractor.py <track.mp3>")
        233 |     else:
  >>>   234 |         print(json.dumps(extract_groove(sys.argv[1]), ensure_ascii=False, indent=2))
  ```

### LONG_FUNCTION — 1 шт. — 🟡 MEDIUM
**Смысл:** Функция > 100 LOC — сложно тестировать/поддерживать
**Fix:** Декомпозировать: приватные `_helper()`, тестировать по частям.

- **строка 22** — extract_groove: 160 LOC (>100) — декомпозиция

  ```
         20 | 
         21 | 
  >>>    22 | def extract_groove(audio_path: str, bpm: float = None) -> dict:
         23 |     """
         24 |     Извлекает ритмический шаблон из трека.
  ```

### HIGH_COMPLEXITY — 1 шт. — 🟡 MEDIUM
**Смысл:** Цикломатическая сложность > 15
**Fix:** Разбить на подфункции; if-цепочки → dict-диспатчер.

- **строка 22** — extract_groove: сложность ≈ 22 (>15)

  ```
         20 | 
         21 | 
  >>>    22 | def extract_groove(audio_path: str, bpm: float = None) -> dict:
         23 |     """
         24 |     Извлекает ритмический шаблон из трека.
  ```
