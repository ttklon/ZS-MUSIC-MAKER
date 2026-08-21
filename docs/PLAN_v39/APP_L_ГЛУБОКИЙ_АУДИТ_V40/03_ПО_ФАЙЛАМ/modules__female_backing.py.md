# АУДИТ ФАЙЛА: `modules/female_backing.py`

**LOC:** 225  |  **Размер:** 8185 байт  |  **Проблем:** 11  |  **Risk score:** 9

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 15 | `__future__.annotations` | from |
| 17 | `pathlib.Path` | from |
| 27 | `torch` | import |
| 45 | `soundfile` | import |
| 56 | `soundfile` | import |
| 57 | `bark.SAMPLE_RATE` | from |
| 57 | `bark.generate_audio` | from |
| 69 | `pyttsx3` | import |
| 96 | `numpy` | import |
| 97 | `soundfile` | import |
| 114 | `numpy` | import |
| 115 | `soundfile` | import |
| 163 | `numpy` | import |
| 164 | `soundfile` | import |
| 197 | `numpy` | import |
| 198 | `soundfile` | import |
| 123 | `librosa` | import |
| 136 | `scipy.signal.butter` | from |
| 136 | `scipy.signal.sosfilt` | from |
| 208 | `librosa` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 25 | `_synth_silero` | 26 | 4 | ❌ |
| 54 | `_synth_bark` | 10 | 2 | ❌ |
| 67 | `_synth_pyttsx` | 18 | 6 | ❌ |
| 88 | `synth_female_line` | 14 | 4 | ✅ |
| 106 | `sweeten_backing` | 46 | 5 | ✅ |
| 156 | `make_chorus_backing` | 31 | 6 | ✅ |
| 190 | `mix_backing_into_vocal` | 35 | 7 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 6 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 50** — print() вместо logger

  ```
         48 |         return True
         49 |     except Exception as e:
  >>>    50 |         print(f"[female_backing] silero failed: {e}")
         51 |         return False
         52 | 
  ```

- **строка 63** — print() вместо logger

  ```
         61 |         return True
         62 |     except Exception as e:
  >>>    63 |         print(f"[female_backing] bark failed: {e}")
         64 |         return False
         65 | 
  ```

- **строка 84** — print() вместо logger

  ```
         82 |         return out_wav.exists() and out_wav.stat().st_size > 500
         83 |     except Exception as e:
  >>>    84 |         print(f"[female_backing] pyttsx failed: {e}")
         85 |         return False
         86 | 
  ```

- **строка 151** — print() вместо logger

  ```
        149 |         return out
        150 |     except Exception as e:
  >>>   151 |         print(f"[female_backing] sweeten failed: {e}")
        152 |         return wav_path
        153 | 
  ```

- **строка 186** — print() вместо logger

  ```
        184 |         return sweeten_backing(out_wav)
        185 |     except Exception as e:
  >>>   186 |         print(f"[female_backing] make_chorus_backing failed: {e}")
        187 |         return out_wav
        188 | 
  ```

- **строка 224** — print() вместо logger

  ```
        222 |         return out
        223 |     except Exception as e:
  >>>   224 |         print(f"[female_backing] mix failed: {e}")
        225 |         return main_vocal_wav
  ```

### SILENT_EXCEPT_PASS — 4 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 131** — except: pass — тихое подавление ошибок

  ```
        129 |             )  # noqa: ZSMM_NOT_RVC
        130 |             y = np.stack([shifted, shifted], axis=-1)
  >>>   131 |         except Exception:
        132 |             pass
        133 | 
  ```

- **строка 141** — except: pass — тихое подавление ошибок

  ```
        139 |             for ch in range(y.shape[1]):
        140 |                 y[:, ch] = sosfilt(sos, y[:, ch])
  >>>   141 |         except Exception:
        142 |             pass
        143 | 
  ```

- **строка 40** — except: pass — тихое подавление ошибок

  ```
         38 |             try:
         39 |                 torch.save(model, model_path)
  >>>    40 |             except Exception:
         41 |                 pass
         42 |         else:
  ```

- **строка 211** — except: pass — тихое подавление ошибок

  ```
        209 | 
        210 |                 b = librosa.resample(b.T, orig_sr=sr2, target_sr=sr).T
  >>>   211 |             except Exception:
        212 |                 pass
        213 |         n = max(len(v), len(b))
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 15** — import 'annotations' не используется в теле файла

  ```
         13 | """
         14 | 
  >>>    15 | from __future__ import annotations
         16 | 
         17 | from pathlib import Path
  ```
