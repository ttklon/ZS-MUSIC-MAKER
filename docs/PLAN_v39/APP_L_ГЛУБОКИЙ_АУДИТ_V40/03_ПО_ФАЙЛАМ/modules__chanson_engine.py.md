# АУДИТ ФАЙЛА: `modules/chanson_engine.py`

**LOC:** 195  |  **Размер:** 7614 байт  |  **Проблем:** 2  |  **Risk score:** 4

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 11 | `os` | import |
| 12 | `typing.Dict` | from |
| 12 | `typing.Any` | from |
| 13 | `numpy` | import |
| 14 | `soundfile` | import |
| 17 | `pedalboard.Chorus` | from |
| 17 | `pedalboard.Compressor` | from |
| 17 | `pedalboard.HighpassFilter` | from |
| 17 | `pedalboard.Limiter` | from |
| 17 | `pedalboard.Pedalboard` | from |
| 17 | `pedalboard.Reverb` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 33 | `__init__` | 1 | 0 | ❌ |
| 36 | `generate_kick` | 7 | 0 | ✅ |
| 45 | `generate_snare` | 8 | 0 | ✅ |
| 55 | `generate_hihat` | 9 | 0 | ✅ |
| 66 | `generate_guitar_chord` | 32 | 4 | ✅ |
| 100 | `synthesize_chanson_track` | 95 | 12 | ✅ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 30 | `ChansonEngine` | ✅ |

## Проблемы (детально, с цитатой кода)

### SILENT_EXCEPT_PASS — 2 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 95** — except: pass — тихое подавление ошибок

  ```
         93 |                 ])
         94 |                 chord_signal = board(chord_signal, self.sr)
  >>>    95 |             except Exception:
         96 |                 pass
         97 | 
  ```

- **строка 182** — except: pass — тихое подавление ошибок

  ```
        180 |                 ])
        181 |                 stereo_mix = master_board(stereo_mix, self.sr)
  >>>   182 |             except Exception:
        183 |                 pass
        184 | 
  ```
