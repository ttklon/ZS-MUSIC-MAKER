# АУДИТ ФАЙЛА: `modules/stem_splitter.py`

**LOC:** 75  |  **Размер:** 2467 байт  |  **Проблем:** 2  |  **Risk score:** 0

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 7 | `os` | import |
| 8 | `subprocess` | import |
| 9 | `sys` | import |
| 18 | `demucs.separate` | import |
| 56 | `librosa` | import |
| 57 | `numpy` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 14 | `split_stems` | 36 | 5 | ✅ |
| 53 | `analyze_arrangement` | 15 | 4 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 2 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 73** — print() вместо logger

  ```
         71 | if __name__ == "__main__":
         72 |     if len(sys.argv) < 2:
  >>>    73 |         print("Usage: python stem_splitter.py <track.mp3>")
         74 |     else:
         75 |         print(split_stems(sys.argv[1]))
  ```

- **строка 75** — print() вместо logger

  ```
         73 |         print("Usage: python stem_splitter.py <track.mp3>")
         74 |     else:
  >>>    75 |         print(split_stems(sys.argv[1]))
  ```
