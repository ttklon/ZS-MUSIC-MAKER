# АУДИТ ФАЙЛА: `modules/musical_intelligence.py`

**LOC:** 90  |  **Размер:** 3121 байт  |  **Проблем:** 2  |  **Risk score:** 0

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 9 | `os` | import |
| 10 | `numpy` | import |
| 14 | `pyAudioAnalysis.audioBasicIO` | from |
| 15 | `pyAudioAnalysis.ShortTermFeatures` | from |
| 21 | `mingus.core.chords` | import |
| 22 | `mingus.core.keys` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 29 | `__init__` | 1 | 0 | ❌ |
| 32 | `analyze_key` | 35 | 4 | ✅ |
| 69 | `suggest_chords` | 16 | 3 | ✅ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 28 | `MusicalIntelligence` | ❌ |

## Проблемы (детально, с цитатой кода)

### MISSING_CLASS_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 28** — public class 'MusicalIntelligence' без docstring

  ```
         26 | 
         27 | 
  >>>    28 | class MusicalIntelligence:
         29 |     def __init__(self, sr: int = 44100):
         30 |         self.sr = sr
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 90** — print() вместо logger

  ```
         88 | if __name__ == "__main__":
         89 |     intel = MusicalIntelligence()
  >>>    90 |     print(intel.suggest_chords("A", "minor"))
  ```
