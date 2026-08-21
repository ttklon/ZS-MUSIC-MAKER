# АУДИТ ФАЙЛА: `tools/smoke_v26.py`

**LOC:** 217  |  **Размер:** 6908 байт  |  **Проблем:** 10  |  **Risk score:** 5

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 19 | `__future__.annotations` | from |
| 21 | `shutil` | import |
| 22 | `sys` | import |
| 23 | `pathlib.Path` | from |
| 25 | `numpy` | import |
| 26 | `soundfile` | import |
| 39 | `app.core.orchestrator.run_full_pipeline` | from |
| 189 | `json` | import |
| 190 | `time` | import |
| 191 | `pathlib.Path` | from |
| 158 | `modules.hit_scorer` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 33 | `check` | 2 | 0 | ❌ |
| 38 | `_run` | 6 | 1 | ❌ |
| 47 | `_corr` | 4 | 1 | ❌ |
| 54 | `_dbfs` | 3 | 0 | ❌ |
| 60 | `main` | 122 | 15 | ❌ |
| 185 | `_write_report` | 28 | 1 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 6 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 35** — print() вместо logger

  ```
         33 | def check(name, ok, detail=""):
         34 |     RESULTS.append((name, bool(ok), detail))
  >>>    35 |     print(f"[{'PASS' if ok else 'FAIL'}] {name:38s} {detail}")
         36 | 
         37 | 
  ```

- **строка 61** — print() вместо logger

  ```
         59 | 
         60 | def main():
  >>>    61 |     print("=" * 64)
         62 |     print("ZS Music Maker v26 — smoke_v26 (stereo + loudness + drop)")
         63 |     print("=" * 64)
  ```

- **строка 62** — print() вместо logger

  ```
         60 | def main():
         61 |     print("=" * 64)
  >>>    62 |     print("ZS Music Maker v26 — smoke_v26 (stereo + loudness + drop)")
         63 |     print("=" * 64)
         64 | 
  ```

- **строка 63** — print() вместо logger

  ```
         61 |     print("=" * 64)
         62 |     print("ZS Music Maker v26 — smoke_v26 (stereo + loudness + drop)")
  >>>    63 |     print("=" * 64)
         64 | 
         65 |     res = _run(
  ```

- **строка 177** — print() вместо logger

  ```
        175 |         check("v26.hook_repeat_fallback", False, f"crash: {e}")
        176 | 
  >>>   177 |     print("-" * 64)
        178 |     p = sum(1 for _, o, _ in RESULTS if o)
        179 |     f = len(RESULTS) - p
  ```

- **строка 180** — print() вместо logger

  ```
        178 |     p = sum(1 for _, o, _ in RESULTS if o)
        179 |     f = len(RESULTS) - p
  >>>   180 |     print(f"RESULT: {p} PASS / {f} FAIL / {len(RESULTS)} total")
        181 |     _write_report("smoke_v26", p, f)
        182 |     return 0 if f == 0 else 1
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
         21 | import shutil
  ```

### LONG_FUNCTION — 1 шт. — 🟡 MEDIUM
**Смысл:** Функция > 100 LOC — сложно тестировать/поддерживать
**Fix:** Декомпозировать: приватные `_helper()`, тестировать по частям.

- **строка 60** — main: 122 LOC (>100) — декомпозиция

  ```
         58 | 
         59 | 
  >>>    60 | def main():
         61 |     print("=" * 64)
         62 |     print("ZS Music Maker v26 — smoke_v26 (stereo + loudness + drop)")
  ```

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 60** — public function 'main' без docstring

  ```
         58 | 
         59 | 
  >>>    60 | def main():
         61 |     print("=" * 64)
         62 |     print("ZS Music Maker v26 — smoke_v26 (stereo + loudness + drop)")
  ```

### SILENT_EXCEPT_PASS — 1 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 212** — except: pass — тихое подавление ошибок

  ```
        210 |             encoding="utf-8",
        211 |         )
  >>>   212 |     except Exception:
        213 |         pass  # отчёт — nice-to-have, не должен валить smoke
        214 | 
  ```
