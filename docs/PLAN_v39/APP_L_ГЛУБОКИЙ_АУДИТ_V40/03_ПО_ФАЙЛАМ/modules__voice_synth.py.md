# АУДИТ ФАЙЛА: `modules/voice_synth.py`

**LOC:** 195  |  **Размер:** 7826 байт  |  **Проблем:** 11  |  **Risk score:** 4

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 13 | `os` | import |
| 14 | `pathlib.Path` | from |
| 24 | `torch` | import |
| 35 | `torchaudio` | import |
| 49 | `TTS.api.TTS` | from |
| 68 | `soundfile` | import |
| 69 | `bark.SAMPLE_RATE` | from |
| 69 | `bark.generate_audio` | from |
| 82 | `pyttsx3` | import |
| 97 | `gtts.gTTS` | from |
| 136 | `time` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 21 | `_synth_silero` | 20 | 1 | ✅ |
| 44 | `_synth_xtts` | 16 | 3 | ✅ |
| 63 | `_synth_bark` | 13 | 1 | ✅ |
| 79 | `_synth_pyttsx3` | 12 | 3 | ✅ |
| 94 | `_synth_gtts` | 10 | 2 | ✅ |
| 107 | `synth` | 79 | 17 | ✅ |
| 156 | `_produced` | 4 | 2 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 9 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 40** — print() вместо logger

  ```
         38 |         return True
         39 |     except Exception as e:
  >>>    40 |         print(f"[voice_synth.silero] {e}")
         41 |         return False
         42 | 
  ```

- **строка 59** — print() вместо logger

  ```
         57 |         return True
         58 |     except Exception as e:
  >>>    59 |         print(f"[voice_synth.xtts] {e}")
         60 |         return False
         61 | 
  ```

- **строка 75** — print() вместо logger

  ```
         73 |         return True
         74 |     except Exception as e:
  >>>    75 |         print(f"[voice_synth.bark] {e}")
         76 |         return False
         77 | 
  ```

- **строка 90** — print() вместо logger

  ```
         88 |             return True
         89 |     except Exception as e:
  >>>    90 |         print(f"[voice_synth.pyttsx3] {e}")
         91 |     return False
         92 | 
  ```

- **строка 103** — print() вместо logger

  ```
        101 |         return os.path.exists(out_path) and os.path.getsize(out_path) > 100
        102 |     except Exception as e:
  >>>   103 |         print(f"[voice_synth.gtts] {e}")
        104 |         return False
        105 | 
  ```

- **строка 167** — print() вместо logger

  ```
        165 |             if engines[e]() and _produced():
        166 |                 return out_path
  >>>   167 |         print("[voice_synth] ALL engines failed/unavailable — honest empty return")
        168 |         return ""
        169 | 
  ```

- **строка 172** — print() вместо logger

  ```
        170 |     fn = engines.get(engine)
        171 |     if not fn:
  >>>   172 |         print(f"[voice_synth] unknown engine={engine}, fallback silero")
        173 |         fn = engines["silero"]
        174 | 
  ```

- **строка 185** — print() вместо logger

  ```
        183 |                 return out_path
        184 | 
  >>>   185 |     print("[voice_synth] no engine produced a file — honest empty return")
        186 |     return ""
        187 | 
  ```

- **строка 195** — print() вместо logger

  ```
        193 |         out_name="test_v7.wav",
        194 |     )
  >>>   195 |     print(f"WAV: {r}, exists: {os.path.exists(r)}")
  ```

### HIGH_COMPLEXITY — 1 шт. — 🟡 MEDIUM
**Смысл:** Цикломатическая сложность > 15
**Fix:** Разбить на подфункции; if-цепочки → dict-диспатчер.

- **строка 107** — synth: сложность ≈ 17 (>15)

  ```
        105 | 
        106 | 
  >>>   107 | def synth(
        108 |     text: str,
        109 |     engine: str = "silero",
  ```

### SILENT_EXCEPT_PASS — 1 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 130** — except: pass — тихое подавление ошибок

  ```
        128 |     try:
        129 |         OUT_DIR.mkdir(parents=True, exist_ok=True)
  >>>   130 |     except Exception:
        131 |         pass
        132 |     # v33 FIX (P0, SESSION_LOG v32.4): дефолтное имя draft.wav молча
  ```
