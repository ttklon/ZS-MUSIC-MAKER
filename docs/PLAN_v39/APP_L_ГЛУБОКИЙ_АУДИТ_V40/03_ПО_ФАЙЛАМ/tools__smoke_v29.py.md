# АУДИТ ФАЙЛА: `tools/smoke_v29.py`

**LOC:** 188  |  **Размер:** 6721 байт  |  **Проблем:** 13  |  **Risk score:** 3

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 16 | `__future__.annotations` | from |
| 18 | `json` | import |
| 19 | `shutil` | import |
| 20 | `subprocess` | import |
| 21 | `sys` | import |
| 22 | `pathlib.Path` | from |
| 24 | `numpy` | import |
| 25 | `soundfile` | import |
| 58 | `modules.midi_generator` | from |
| 80 | `app.core.orchestrator_god.run_god_pipeline` | from |
| 123 | `modules.mastering_pro` | from |
| 160 | `json` | import |
| 161 | `time` | import |
| 162 | `pathlib.Path` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 33 | `_ok` | 2 | 0 | ❌ |
| 38 | `_fail` | 2 | 0 | ❌ |
| 43 | `test_version_cli` | 11 | 3 | ❌ |
| 57 | `test_midi_generator` | 16 | 5 | ❌ |
| 76 | `test_god_mode_e2e` | 42 | 9 | ❌ |
| 121 | `test_mastering_pro_metrics` | 17 | 2 | ✅ |
| 141 | `main` | 14 | 0 | ❌ |
| 158 | `_write_report` | 26 | 1 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 7 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 35** — print() вместо logger

  ```
         33 | def _ok(name: str, extra: str = "") -> None:
         34 |     RESULTS.append((True, name, extra))
  >>>    35 |     print(f"[PASS] {name:40s} {extra}")
         36 | 
         37 | 
  ```

- **строка 40** — print() вместо logger

  ```
         38 | def _fail(name: str, extra: str = "") -> None:
         39 |     RESULTS.append((False, name, extra))
  >>>    40 |     print(f"[FAIL] {name:40s} {extra}")
         41 | 
         42 | 
  ```

- **строка 142** — print() вместо logger

  ```
        140 | 
        141 | def main() -> int:
  >>>   142 |     print("=" * 64)
        143 |     print("ZS Music Maker v29 — smoke_v29 (God Mode E2E)")
        144 |     print("=" * 64)
  ```

- **строка 143** — print() вместо logger

  ```
        141 | def main() -> int:
        142 |     print("=" * 64)
  >>>   143 |     print("ZS Music Maker v29 — smoke_v29 (God Mode E2E)")
        144 |     print("=" * 64)
        145 |     test_version_cli()
  ```

- **строка 144** — print() вместо logger

  ```
        142 |     print("=" * 64)
        143 |     print("ZS Music Maker v29 — smoke_v29 (God Mode E2E)")
  >>>   144 |     print("=" * 64)
        145 |     test_version_cli()
        146 |     test_midi_generator()
  ```

- **строка 149** — print() вместо logger

  ```
        147 |     test_god_mode_e2e()
        148 |     test_mastering_pro_metrics()
  >>>   149 |     print("-" * 64)
        150 |     passed = sum(1 for r in RESULTS if r[0])
        151 |     total = len(RESULTS)
  ```

- **строка 153** — print() вместо logger

  ```
        151 |     total = len(RESULTS)
        152 |     failed = total - passed
  >>>   153 |     print(f"RESULT: {passed} PASS / {failed} FAIL / {total} total")
        154 |     _write_report("smoke_v29", passed, failed)
        155 |     return 0 if failed == 0 else 1
  ```

### MISSING_DOCSTRING — 4 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 43** — public function 'test_version_cli' без docstring

  ```
         41 | 
         42 | 
  >>>    43 | def test_version_cli() -> None:
         44 |     try:
         45 |         out = subprocess.run(
  ```

- **строка 57** — public function 'test_midi_generator' без docstring

  ```
         55 | 
         56 | 
  >>>    57 | def test_midi_generator() -> None:
         58 |     from modules import midi_generator
         59 |     st = midi_generator.MIDIGenerator.get_status()
  ```

- **строка 76** — public function 'test_god_mode_e2e' без docstring

  ```
         74 | 
         75 | 
  >>>    76 | def test_god_mode_e2e() -> None:
         77 |     out_root = ROOT / "output" / "smoke_v29" / "god"
         78 |     if out_root.exists():
  ```

- **строка 141** — public function 'main' без docstring

  ```
        139 | 
        140 | 
  >>>   141 | def main() -> int:
        142 |     print("=" * 64)
        143 |     print("ZS Music Maker v29 — smoke_v29 (God Mode E2E)")
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 16** — import 'annotations' не используется в теле файла

  ```
         14 | """
         15 | 
  >>>    16 | from __future__ import annotations
         17 | 
         18 | import json
  ```

### SILENT_EXCEPT_PASS — 1 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 183** — except: pass — тихое подавление ошибок

  ```
        181 |             encoding="utf-8",
        182 |         )
  >>>   183 |     except Exception:
        184 |         pass  # отчёт — nice-to-have, не должен валить smoke
        185 | 
  ```
