# АУДИТ ФАЙЛА: `modules/mastering_pro.py`

**LOC:** 188  |  **Размер:** 7756 байт  |  **Проблем:** 6  |  **Risk score:** 4

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 18 | `os` | import |
| 19 | `numpy` | import |
| 20 | `soundfile` | import |
| 24 | `pyloudnorm` | import |
| 30 | `pedalboard.Chorus` | from |
| 30 | `pedalboard.Compressor` | from |
| 30 | `pedalboard.Distortion` | from |
| 30 | `pedalboard.HighpassFilter` | from |
| 30 | `pedalboard.Limiter` | from |
| 30 | `pedalboard.Pedalboard` | from |
| 38 | `pedalboard.io.AudioFile` | from |
| 79 | `pydub.AudioSegment` | from |
| 131 | `warnings` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 44 | `_sanitize` | 4 | 1 | ✅ |
| 51 | `_apply_ceiling` | 11 | 2 | ✅ |
| 65 | `process_mastering` | 123 | 20 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 3 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 88** — print() вместо logger

  ```
         86 |             input_wav = temp_mix
         87 |         except Exception as e:
  >>>    88 |             print(f"[mastering_pro] Mix failed: {e}")
         89 | 
         90 |     mastered = None
  ```

- **строка 112** — print() вместо logger

  ```
        110 |             engine = "pedalboard_pro_safe"
        111 |         except Exception as e:
  >>>   112 |             print(f"[mastering_pro] Pedalboard execution error: {e}, falling back to numpy/soundfile")
        113 |             HAS_PEDALBOARD = False
        114 | 
  ```

- **строка 137** — print() вместо logger

  ```
        135 |             mastered = mastered.T  # back to (channels, frames)
        136 |         except Exception as e:
  >>>   137 |             print(f"[mastering_pro] pyloudnorm error: {e}, using RMS fallback")
        138 |             HAS_PYLOUDNORM = False
        139 | 
  ```

### LONG_FUNCTION — 1 шт. — 🟡 MEDIUM
**Смысл:** Функция > 100 LOC — сложно тестировать/поддерживать
**Fix:** Декомпозировать: приватные `_helper()`, тестировать по частям.

- **строка 65** — process_mastering: 123 LOC (>100) — декомпозиция

  ```
         63 | 
         64 | 
  >>>    65 | def process_mastering(input_wav: str, output_wav: str, vocal_path: str = None, target_lufs: float = -14.0):
         66 |     """
         67 |     Профессиональный мастеринг трека с автоматическими фоллбеками.
  ```

### HIGH_COMPLEXITY — 1 шт. — 🟡 MEDIUM
**Смысл:** Цикломатическая сложность > 15
**Fix:** Разбить на подфункции; if-цепочки → dict-диспатчер.

- **строка 65** — process_mastering: сложность ≈ 20 (>15)

  ```
         63 | 
         64 | 
  >>>    65 | def process_mastering(input_wav: str, output_wav: str, vocal_path: str = None, target_lufs: float = -14.0):
         66 |     """
         67 |     Профессиональный мастеринг трека с автоматическими фоллбеками.
  ```

### GLOBAL_STATEMENT — 1 шт. — 🟡 MEDIUM
**Смысл:** global — обычно антипаттерн
**Fix:** Инкапсулировать в класс или get_*().

- **строка 72** — global — антипаттерн

  ```
         70 |     v29: добавлен true-peak ceiling (-1 dBTP) и honest output-метрики.
         71 |     """
  >>>    72 |     global HAS_PEDALBOARD, HAS_PYLOUDNORM
         73 |     if not os.path.exists(input_wav):
         74 |         raise FileNotFoundError(f"Input wav not found: {input_wav}")
  ```
