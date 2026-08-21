# АУДИТ ФАЙЛА: `modules/voice_recording.py`

**LOC:** 395  |  **Размер:** 12109 байт  |  **Проблем:** 17  |  **Risk score:** 15

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 19 | `__future__.annotations` | from |
| 21 | `json` | import |
| 22 | `math` | import |
| 23 | `time` | import |
| 24 | `uuid` | import |
| 25 | `wave` | import |
| 26 | `collections.abc.Callable` | from |
| 27 | `dataclasses.asdict` | from |
| 27 | `dataclasses.dataclass` | from |
| 28 | `pathlib.Path` | from |
| 29 | `typing.Any` | from |
| 36 | `numpy` | import |
| 37 | `sounddevice` | import |
| 260 | `numpy` | import |
| 261 | `soundfile` | import |
| 220 | `soundfile` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 253 | `split_wav_into_takes` | 117 | 19 | ❌ |
| 373 | `capability_report` | 18 | 3 | ❌ |
| 70 | `as_dict` | 1 | 0 | ❌ |
| 77 | `__init__` | 21 | 0 | ❌ |
| 100 | `_callback` | 6 | 1 | ❌ |
| 108 | `_emit_metrics` | 32 | 5 | ❌ |
| 142 | `start` | 30 | 2 | ❌ |
| 174 | `stop` | 26 | 6 | ❌ |
| 202 | `_write_wav` | 9 | 2 | ❌ |
| 213 | `ingest_wav` | 24 | 2 | ❌ |
| 239 | `stop_and_split` | 11 | 1 | ❌ |
| 295 | `_finalize` | 44 | 5 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 47 | `RecorderMetrics` | ❌ |
| 58 | `TakeInfo` | ❌ |
| 74 | `RealMicRecorder` | ✅ |

## Проблемы (детально, с цитатой кода)

### MISSING_DOCSTRING — 6 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 253** — public function 'split_wav_into_takes' без docstring

  ```
        251 | 
        252 | 
  >>>   253 | def split_wav_into_takes(
        254 |     wav_path: str,
        255 |     min_silence_ms: int = 600,
  ```

- **строка 373** — public function 'capability_report' без docstring

  ```
        371 | 
        372 | 
  >>>   373 | def capability_report() -> dict[str, Any]:
        374 |     devices = []
        375 |     if SD_OK:
  ```

- **строка 142** — public function 'start' без docstring

  ```
        140 |             pass
        141 | 
  >>>   142 |     def start(self) -> dict[str, Any]:
        143 |         self._buf = []
        144 |         self._start_ts = time.time()
  ```

- **строка 174** — public function 'stop' без docstring

  ```
        172 |             return {"ok": False, "backend": self._backend, "reason": str(e)}
        173 | 
  >>>   174 |     def stop(self) -> dict[str, Any]:
        175 |         self._stop_ts = time.time()
        176 |         if not self._active or self._stream is None:
  ```

- **строка 213** — public function 'ingest_wav' без docstring

  ```
        211 |             w.writeframes(x.tobytes())
        212 | 
  >>>   213 |     def ingest_wav(
        214 |         self, wav_path: str, style: str = "conversational"
        215 |     ) -> dict[str, Any]:
  ```

- **строка 239** — public function 'stop_and_split' без docstring

  ```
        237 |             return {"ok": False, "reason": str(e)}
        238 | 
  >>>   239 |     def stop_and_split(
        240 |         self, min_silence_ms: int = 600, min_take_ms: int = 800
        241 |     ) -> list[TakeInfo]:
  ```

### SILENT_EXCEPT_PASS — 5 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 367** — except: pass — тихое подавление ошибок

  ```
        365 |             encoding="utf-8",
        366 |         )
  >>>   367 |     except Exception:
        368 |         pass
        369 | 
  ```

- **строка 105** — except: pass — тихое подавление ошибок

  ```
        103 |             self._buf.append(chunk)
        104 |             self._emit_metrics(chunk)
  >>>   105 |         except Exception:
        106 |             pass
        107 | 
  ```

- **строка 139** — except: pass — тихое подавление ошибок

  ```
        137 |                 )
        138 |             )
  >>>   139 |         except Exception:
        140 |             pass
        141 | 
  ```

- **строка 181** — except: pass — тихое подавление ошибок

  ```
        179 |             self._stream.stop()
        180 |             self._stream.close()
  >>>   181 |         except Exception:
        182 |             pass
        183 |         self._active = False
  ```

- **строка 383** — except: pass — тихое подавление ошибок

  ```
        381 |                 if d.get("max_input_channels", 0) > 0
        382 |             ]
  >>>   383 |         except Exception:
        384 |             pass
        385 |     return {
  ```

### MISSING_CLASS_DOCSTRING — 2 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 47** — public class 'RecorderMetrics' без docstring

  ```
         45 | 
         46 | @dataclass
  >>>    47 | class RecorderMetrics:
         48 |     rms_db: float = -100.0
         49 |     peak_db: float = -100.0
  ```

- **строка 58** — public class 'TakeInfo' без docstring

  ```
         56 | 
         57 | @dataclass
  >>>    58 | class TakeInfo:
         59 |     take_id: str
         60 |     path: str
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 19** — import 'annotations' не используется в теле файла

  ```
         17 | """
         18 | 
  >>>    19 | from __future__ import annotations
         20 | 
         21 | import json
  ```

### LONG_FUNCTION — 1 шт. — 🟡 MEDIUM
**Смысл:** Функция > 100 LOC — сложно тестировать/поддерживать
**Fix:** Декомпозировать: приватные `_helper()`, тестировать по частям.

- **строка 253** — split_wav_into_takes: 117 LOC (>100) — декомпозиция

  ```
        251 | 
        252 | 
  >>>   253 | def split_wav_into_takes(
        254 |     wav_path: str,
        255 |     min_silence_ms: int = 600,
  ```

### HIGH_COMPLEXITY — 1 шт. — 🟡 MEDIUM
**Смысл:** Цикломатическая сложность > 15
**Fix:** Разбить на подфункции; if-цепочки → dict-диспатчер.

- **строка 253** — split_wav_into_takes: сложность ≈ 19 (>15)

  ```
        251 | 
        252 | 
  >>>   253 | def split_wav_into_takes(
        254 |     wav_path: str,
        255 |     min_silence_ms: int = 600,
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 395** — print() вместо logger

  ```
        393 | 
        394 | if __name__ == "__main__":
  >>>   395 |     print(json.dumps(capability_report(), indent=2))
  ```
