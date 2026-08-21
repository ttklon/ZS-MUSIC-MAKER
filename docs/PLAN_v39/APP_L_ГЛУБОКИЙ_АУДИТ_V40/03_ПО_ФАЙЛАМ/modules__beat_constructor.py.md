# АУДИТ ФАЙЛА: `modules/beat_constructor.py`

**LOC:** 658  |  **Размер:** 27968 байт  |  **Проблем:** 8  |  **Risk score:** 10

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 19 | `json` | import |
| 20 | `math` | import |
| 21 | `os` | import |
| 22 | `random` | import |
| 24 | `numpy` | import |
| 101 | `pydub.AudioSegment` | from |
| 547 | `scipy.signal.butter` | from |
| 548 | `scipy.signal.sosfilt` | from |
| 590 | `soundfile` | import |
| 595 | `scipy.io.wavfile` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 621 | `construct_beat` | 24 | 1 | ✅ |
| 38 | `__init__` | 20 | 2 | ❌ |
| 60 | `_classify_samples` | 36 | 7 | ✅ |
| 98 | `_load_audio` | 14 | 2 | ✅ |
| 114 | `_generate_kick` | 35 | 7 | ✅ |
| 151 | `_generate_snare` | 27 | 4 | ✅ |
| 180 | `_generate_hihat` | 26 | 5 | ✅ |
| 208 | `_generate_bass_line` | 45 | 4 | ✅ |
| 255 | `_generate_melody` | 17 | 6 | ✅ |
| 274 | `_generate_fx` | 16 | 5 | ✅ |
| 292 | `_pan_audio` | 8 | 1 | ✅ |
| 302 | `_build_section` | 90 | 8 | ✅ |
| 394 | `build_track` | 224 | 25 | ✅ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 35 | `BeatConstructor` | ✅ |

## Проблемы (детально, с цитатой кода)

### SILENT_EXCEPT_PASS — 3 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 468** — except: pass — тихое подавление ошибок

  ```
        466 |                     ]
        467 |                     full_track[_idx - _fade : _idx] *= _env
  >>>   468 |         except Exception:
        469 |             pass
        470 | 
  ```

- **строка 526** — except: pass — тихое подавление ошибок

  ```
        524 |                     _pos += _ns
        525 |                     _mi += 1
  >>>   526 |         except Exception:
        527 |             pass
        528 | 
  ```

- **строка 599** — except: pass — тихое подавление ошибок

  ```
        597 |                 # Стерео запись через wavfile
        598 |                 wavfile.write(out_path, self.sr, (stereo * 32767).astype(np.int16))
  >>>   599 |             except Exception:
        600 |                 pass
        601 | 
  ```

### BARE_PRINT — 3 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 111** — print() вместо logger

  ```
        109 |             return samples
        110 |         except Exception as e:
  >>>   111 |             print(f"[beat_constructor] load fail {path}: {e}")
        112 |             return np.zeros(self.sr, dtype=np.float32)
        113 | 
  ```

- **строка 585** — print() вместо logger

  ```
        583 |                 stereo = stereo / _pk * 0.95
        584 |         except Exception as exc:
  >>>   585 |             print(f"[beat_constructor] stereo width fallback: {exc}")
        586 | 
        587 |         os.makedirs(OUTPUT_DIR, exist_ok=True)
  ```

- **строка 658** — print() вместо logger

  ```
        656 |     sv = {"target_bpm": 130, "target_mode": "minor"}
        657 |     result = construct_beat(groove, [], sv, duration_sec=90)
  >>>   658 |     print(json.dumps(result, ensure_ascii=False, indent=2))
  ```

### LONG_FUNCTION — 1 шт. — 🟡 MEDIUM
**Смысл:** Функция > 100 LOC — сложно тестировать/поддерживать
**Fix:** Декомпозировать: приватные `_helper()`, тестировать по частям.

- **строка 394** — build_track: 224 LOC (>100) — декомпозиция

  ```
        392 |         return section_audio
        393 | 
  >>>   394 |     def build_track(
        395 |         self,
        396 |         duration_sec: int = 120,
  ```

### HIGH_COMPLEXITY — 1 шт. — 🟡 MEDIUM
**Смысл:** Цикломатическая сложность > 15
**Fix:** Разбить на подфункции; if-цепочки → dict-диспатчер.

- **строка 394** — build_track: сложность ≈ 25 (>15)

  ```
        392 |         return section_audio
        393 | 
  >>>   394 |     def build_track(
        395 |         self,
        396 |         duration_sec: int = 120,
  ```
