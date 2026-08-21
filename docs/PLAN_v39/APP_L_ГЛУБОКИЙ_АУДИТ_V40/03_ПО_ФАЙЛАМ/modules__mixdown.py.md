# АУДИТ ФАЙЛА: `modules/mixdown.py`

**LOC:** 177  |  **Размер:** 5679 байт  |  **Проблем:** 4  |  **Risk score:** 2

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 10 | `os` | import |
| 11 | `shutil` | import |
| 13 | `numpy` | import |
| 27 | `pydub.AudioSegment` | from |
| 58 | `scipy.io.wavfile` | from |
| 59 | `scipy.signal.butter` | from |
| 59 | `scipy.signal.sosfilt` | from |
| 107 | `matchering` | import |
| 126 | `pydub.AudioSegment` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 19 | `mix_beat_and_vocal` | 28 | 1 | ✅ |
| 50 | `apply_eq` | 37 | 5 | ✅ |
| 90 | `master_with_matchering` | 5 | 0 | ✅ |
| 98 | `master_with_matchering_status` | 39 | 2 | ✅ |
| 143 | `full_mixdown` | 30 | 1 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 3 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 119** — print() вместо logger

  ```
        117 |     except ImportError:
        118 |         shutil.copy(mix_path, out)
  >>>   119 |         print("[matchering] MISSING — fallback: copy")
        120 |     except Exception as e:
        121 |         shutil.copy(mix_path, out)
  ```

- **строка 122** — print() вместо logger

  ```
        120 |     except Exception as e:
        121 |         shutil.copy(mix_path, out)
  >>>   122 |         print(f"[matchering error] {e} — fallback: copy")
        123 | 
        124 |     # Дополнительно: mp3 320
  ```

- **строка 177** — print() вместо logger

  ```
        175 | 
        176 | if __name__ == "__main__":
  >>>   177 |     print("mixdown module ready v2")
  ```

### SILENT_EXCEPT_PASS — 1 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 130** — except: pass — тихое подавление ошибок

  ```
        128 |             out.replace(".wav", ".mp3"), format="mp3", bitrate="320k"
        129 |         )
  >>>   130 |     except Exception:
        131 |         pass
        132 | 
  ```
