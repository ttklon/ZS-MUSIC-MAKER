# АУДИТ ФАЙЛА: `modules/vocal_fx.py`

**LOC:** 370  |  **Размер:** 12245 байт  |  **Проблем:** 5  |  **Risk score:** 5

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 24 | `__future__.annotations` | from |
| 26 | `json` | import |
| 27 | `math` | import |
| 28 | `dataclasses.dataclass` | from |
| 29 | `pathlib.Path` | from |
| 30 | `typing.Any` | from |
| 33 | `numpy` | import |
| 34 | `soundfile` | import |
| 330 | `shutil` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 48 | `_read` | 2 | 0 | ❌ |
| 53 | `_write` | 3 | 0 | ❌ |
| 59 | `_resample_linear` | 18 | 3 | ✅ |
| 80 | `_detune_cents` | 3 | 0 | ✅ |
| 86 | `_fit_len` | 6 | 2 | ❌ |
| 95 | `_rms_db` | 2 | 0 | ❌ |
| 100 | `_find_phrase_ends` | 35 | 9 | ✅ |
| 156 | `apply_vocal_double` | 57 | 4 | ✅ |
| 216 | `apply_delay_throw` | 76 | 9 | ✅ |
| 295 | `process_vocal` | 63 | 10 | ✅ |
| 361 | `capability_report` | 5 | 0 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 144 | `VocalFxResult` | ❌ |

## Проблемы (детально, с цитатой кода)

### SILENT_EXCEPT_PASS — 2 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 346** — except: pass — тихое подавление ошибок

  ```
        344 |         if p.exists() and cur != tmp_double:
        345 |             p.unlink()
  >>>   346 |     except Exception:
        347 |         pass
        348 | 
  ```

- **строка 334** — except: pass — тихое подавление ошибок

  ```
        332 |                 shutil.copy(cur, out_wav)
        333 |                 cur = out_wav
  >>>   334 |             except Exception:
        335 |                 pass
        336 | 
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 24** — import 'annotations' не используется в теле файла

  ```
         22 | """
         23 | 
  >>>    24 | from __future__ import annotations
         25 | 
         26 | import json
  ```

### MISSING_CLASS_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 144** — public class 'VocalFxResult' без docstring

  ```
        142 | 
        143 | @dataclass
  >>>   144 | class VocalFxResult:
        145 |     ok: bool
        146 |     out_wav: str
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 370** — print() вместо logger

  ```
        368 | 
        369 | if __name__ == "__main__":
  >>>   370 |     print(json.dumps(capability_report(), indent=2))
  ```
