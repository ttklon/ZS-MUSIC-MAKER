# АУДИТ ФАЙЛА: `modules/cyber_synth.py`

**LOC:** 134  |  **Размер:** 5143 байт  |  **Проблем:** 2  |  **Risk score:** 4

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 9 | `typing.Dict` | from |
| 9 | `typing.Any` | from |
| 10 | `numpy` | import |
| 11 | `soundfile` | import |
| 14 | `pedalboard.Chorus` | from |
| 14 | `pedalboard.Compressor` | from |
| 14 | `pedalboard.Distortion` | from |
| 14 | `pedalboard.HighpassFilter` | from |
| 14 | `pedalboard.Limiter` | from |
| 14 | `pedalboard.Pedalboard` | from |
| 14 | `pedalboard.Reverb` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 31 | `__init__` | 1 | 0 | ❌ |
| 34 | `generate_sub_bass` | 14 | 0 | ✅ |
| 50 | `generate_cyber_lead` | 24 | 2 | ✅ |
| 76 | `synthesize_track` | 47 | 5 | ✅ |
| 125 | `sub_bass_pattern` | 9 | 1 | ✅ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 28 | `CyberSynth` | ✅ |

## Проблемы (детально, с цитатой кода)

### SILENT_EXCEPT_PASS — 2 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 71** — except: pass — тихое подавление ошибок

  ```
         69 |                 ])
         70 |                 lead = board(lead, self.sr)
  >>>    71 |             except Exception:
         72 |                 pass
         73 | 
  ```

- **строка 112** — except: pass — тихое подавление ошибок

  ```
        110 |                 ])
        111 |                 stereo_mix = master_board(stereo_mix, self.sr)
  >>>   112 |             except Exception:
        113 |                 pass
        114 | 
  ```
