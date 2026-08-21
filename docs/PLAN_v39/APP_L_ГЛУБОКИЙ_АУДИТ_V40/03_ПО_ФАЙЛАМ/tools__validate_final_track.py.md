# АУДИТ ФАЙЛА: `tools/validate_final_track.py`

**LOC:** 65  |  **Размер:** 2259 байт  |  **Проблем:** 12  |  **Risk score:** 0

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 12 | `sys` | import |
| 13 | `pathlib.Path` | from |
| 17 | `tests.test_audio_quality.validate_audio_file` | from |
| 18 | `soundfile` | import |
| 19 | `numpy` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 24 | `_find_latest_master` | 2 | 0 | ❌ |
| 29 | `main` | 32 | 4 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 11 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 35** — print() вместо logger

  ```
         33 |         found = _find_latest_master()
         34 |         if not found:
  >>>    35 |             print("USAGE: python tools/validate_final_track.py <path/to/track.wav>")
         36 |             print("(мастера в output/**/masters/*.wav не найдены)")
         37 |             return 2
  ```

- **строка 36** — print() вместо logger

  ```
         34 |         if not found:
         35 |             print("USAGE: python tools/validate_final_track.py <path/to/track.wav>")
  >>>    36 |             print("(мастера в output/**/masters/*.wav не найдены)")
         37 |             return 2
         38 |         track_path = found
  ```

- **строка 40** — print() вместо logger

  ```
         38 |         track_path = found
         39 | 
  >>>    40 |     print(f"--- Final Quality Audit for: {track_path} ---")
         41 |     try:
         42 |         if not track_path.exists():
  ```

- **строка 51** — print() вместо logger

  ```
         49 |         channels = data.shape[1] if data.ndim > 1 else 1
         50 | 
  >>>    51 |         print("STATUS: PASS ✅")
         52 |         print(f"Peak Level: {peak:.4f} (Target <= 1.0)")
         53 |         print(f"RMS Level: {rms:.4f}")
  ```

- **строка 52** — print() вместо logger

  ```
         50 | 
         51 |         print("STATUS: PASS ✅")
  >>>    52 |         print(f"Peak Level: {peak:.4f} (Target <= 1.0)")
         53 |         print(f"RMS Level: {rms:.4f}")
         54 |         print(f"Duration: {duration:.2f}s")
  ```

- **строка 53** — print() вместо logger

  ```
         51 |         print("STATUS: PASS ✅")
         52 |         print(f"Peak Level: {peak:.4f} (Target <= 1.0)")
  >>>    53 |         print(f"RMS Level: {rms:.4f}")
         54 |         print(f"Duration: {duration:.2f}s")
         55 |         print(f"Sample Rate: {sr}Hz")
  ```

- **строка 54** — print() вместо logger

  ```
         52 |         print(f"Peak Level: {peak:.4f} (Target <= 1.0)")
         53 |         print(f"RMS Level: {rms:.4f}")
  >>>    54 |         print(f"Duration: {duration:.2f}s")
         55 |         print(f"Sample Rate: {sr}Hz")
         56 |         print(f"Channels: {channels}")
  ```

- **строка 55** — print() вместо logger

  ```
         53 |         print(f"RMS Level: {rms:.4f}")
         54 |         print(f"Duration: {duration:.2f}s")
  >>>    55 |         print(f"Sample Rate: {sr}Hz")
         56 |         print(f"Channels: {channels}")
         57 |         return 0
  ```

- **строка 56** — print() вместо logger

  ```
         54 |         print(f"Duration: {duration:.2f}s")
         55 |         print(f"Sample Rate: {sr}Hz")
  >>>    56 |         print(f"Channels: {channels}")
         57 |         return 0
         58 |     except Exception as e:
  ```

- **строка 59** — print() вместо logger

  ```
         57 |         return 0
         58 |     except Exception as e:
  >>>    59 |         print("STATUS: FAIL ❌")
         60 |         print(f"Error: {e}")
         61 |         return 1
  ```

- **строка 60** — print() вместо logger

  ```
         58 |     except Exception as e:
         59 |         print("STATUS: FAIL ❌")
  >>>    60 |         print(f"Error: {e}")
         61 |         return 1
         62 | 
  ```

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 29** — public function 'main' без docstring

  ```
         27 | 
         28 | 
  >>>    29 | def main() -> int:
         30 |     if len(sys.argv) > 1:
         31 |         track_path = Path(sys.argv[1])
  ```
