# АУДИТ ФАЙЛА: `modules/health_v12.py`

**LOC:** 381  |  **Размер:** 15900 байт  |  **Проблем:** 26  |  **Risk score:** 3

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 24 | `__future__.annotations` | from |
| 26 | `importlib` | import |
| 27 | `json` | import |
| 28 | `platform` | import |
| 29 | `sys` | import |
| 30 | `time` | import |
| 31 | `traceback` | import |
| 32 | `dataclasses.asdict` | from |
| 32 | `dataclasses.dataclass` | from |
| 32 | `dataclasses.field` | from |
| 33 | `pathlib.Path` | from |
| 34 | `typing.Any` | from |
| 164 | `app.core.hw_autodetect` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 149 | `_probe` | 9 | 4 | ❌ |
| 161 | `_hw_probe` | 23 | 6 | ❌ |
| 192 | `_advice_for` | 26 | 1 | ✅ |
| 221 | `collect` | 96 | 18 | ✅ |
| 325 | `_fmt_row` | 3 | 0 | ❌ |
| 331 | `main` | 46 | 10 | ❌ |
| 119 | `as_dict` | 1 | 0 | ❌ |
| 140 | `as_dict` | 1 | 0 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 111 | `ProbeResult` | ❌ |
| 124 | `HealthReport` | ❌ |

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 21 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 334** — print() вместо logger

  ```
        332 |     argv = argv or sys.argv[1:]
        333 |     rep = collect()
  >>>   334 |     print("=" * 72)
        335 |     print("ZS Music Maker v12 — Health Check")
        336 |     print(f"Generated: {rep.generated_at_human}")
  ```

- **строка 335** — print() вместо logger

  ```
        333 |     rep = collect()
        334 |     print("=" * 72)
  >>>   335 |     print("ZS Music Maker v12 — Health Check")
        336 |     print(f"Generated: {rep.generated_at_human}")
        337 |     print(f"Platform : {rep.platform}   Python: {rep.python}")
  ```

- **строка 336** — print() вместо logger

  ```
        334 |     print("=" * 72)
        335 |     print("ZS Music Maker v12 — Health Check")
  >>>   336 |     print(f"Generated: {rep.generated_at_human}")
        337 |     print(f"Platform : {rep.platform}   Python: {rep.python}")
        338 |     print(
  ```

- **строка 337** — print() вместо logger

  ```
        335 |     print("ZS Music Maker v12 — Health Check")
        336 |     print(f"Generated: {rep.generated_at_human}")
  >>>   337 |     print(f"Platform : {rep.platform}   Python: {rep.python}")
        338 |     print(
        339 |         f"HW mode  : {rep.hw_profile.get('mode', '?')}   "
  ```

- **строка 338** — print() вместо logger

  ```
        336 |     print(f"Generated: {rep.generated_at_human}")
        337 |     print(f"Platform : {rep.platform}   Python: {rep.python}")
  >>>   338 |     print(
        339 |         f"HW mode  : {rep.hw_profile.get('mode', '?')}   "
        340 |         f"GPU: {rep.hw_profile.get('gpu', '?')}"
  ```

- **строка 342** — print() вместо logger

  ```
        340 |         f"GPU: {rep.hw_profile.get('gpu', '?')}"
        341 |     )
  >>>   342 |     print("-" * 72)
        343 |     print("EXTERNAL DEPENDENCIES:")
        344 |     for e in rep.externals:
  ```

- **строка 343** — print() вместо logger

  ```
        341 |     )
        342 |     print("-" * 72)
  >>>   343 |     print("EXTERNAL DEPENDENCIES:")
        344 |     for e in rep.externals:
        345 |         print(_fmt_row(e["name"], e["ok"], e.get("version"), e["requirement"]))
  ```

- **строка 345** — print() вместо logger

  ```
        343 |     print("EXTERNAL DEPENDENCIES:")
        344 |     for e in rep.externals:
  >>>   345 |         print(_fmt_row(e["name"], e["ok"], e.get("version"), e["requirement"]))
        346 |     print("-" * 72)
        347 |     print("INTERNAL MODULES:")
  ```

- **строка 346** — print() вместо logger

  ```
        344 |     for e in rep.externals:
        345 |         print(_fmt_row(e["name"], e["ok"], e.get("version"), e["requirement"]))
  >>>   346 |     print("-" * 72)
        347 |     print("INTERNAL MODULES:")
        348 |     for e in rep.internals:
  ```

- **строка 347** — print() вместо logger

  ```
        345 |         print(_fmt_row(e["name"], e["ok"], e.get("version"), e["requirement"]))
        346 |     print("-" * 72)
  >>>   347 |     print("INTERNAL MODULES:")
        348 |     for e in rep.internals:
        349 |         print(_fmt_row(e["name"], e["ok"], None, e["requirement"]))
  ```

- **строка 349** — print() вместо logger

  ```
        347 |     print("INTERNAL MODULES:")
        348 |     for e in rep.internals:
  >>>   349 |         print(_fmt_row(e["name"], e["ok"], None, e["requirement"]))
        350 |     print("-" * 72)
        351 |     print(
  ```

- **строка 350** — print() вместо logger

  ```
        348 |     for e in rep.internals:
        349 |         print(_fmt_row(e["name"], e["ok"], None, e["requirement"]))
  >>>   350 |     print("-" * 72)
        351 |     print(
        352 |         f"VERDICT: {rep.verdict}  |  READY: {rep.percent_ready}%  |  "
  ```

- **строка 351** — print() вместо logger

  ```
        349 |         print(_fmt_row(e["name"], e["ok"], None, e["requirement"]))
        350 |     print("-" * 72)
  >>>   351 |     print(
        352 |         f"VERDICT: {rep.verdict}  |  READY: {rep.percent_ready}%  |  "
        353 |         f"core_ok={rep.core_ok} quality_ok={rep.quality_ok}  "
  ```

- **строка 366** — print() вместо logger

  ```
        364 |                        if e.get("requirement") == "core_alt" and not e["ok"]]
        365 |         if core_missing:
  >>>   366 |             print(f"  ! RED причина: отсутствует ЯДРО: {', '.join(core_missing)}")
        367 |         elif gui_missing:
        368 |             print(f"  ! RED причина: нет GUI-бэкенда ({', '.join(gui_missing)}).")
  ```

- **строка 368** — print() вместо logger

  ```
        366 |             print(f"  ! RED причина: отсутствует ЯДРО: {', '.join(core_missing)}")
        367 |         elif gui_missing:
  >>>   368 |             print(f"  ! RED причина: нет GUI-бэкенда ({', '.join(gui_missing)}).")
        369 |             print("    Аудио-ядро (beat/mix/mastering) при этом может быть полностью")
        370 |             print("    рабочим — проверь `python tools/smoke_v29.py`. Установи GUI:")
  ```

- **строка 369** — print() вместо logger

  ```
        367 |         elif gui_missing:
        368 |             print(f"  ! RED причина: нет GUI-бэкенда ({', '.join(gui_missing)}).")
  >>>   369 |             print("    Аудио-ядро (beat/mix/mastering) при этом может быть полностью")
        370 |             print("    рабочим — проверь `python tools/smoke_v29.py`. Установи GUI:")
        371 |             print("    `pip install PySide6` или `pip install gradio`.")
  ```

- **строка 370** — print() вместо logger

  ```
        368 |             print(f"  ! RED причина: нет GUI-бэкенда ({', '.join(gui_missing)}).")
        369 |             print("    Аудио-ядро (beat/mix/mastering) при этом может быть полностью")
  >>>   370 |             print("    рабочим — проверь `python tools/smoke_v29.py`. Установи GUI:")
        371 |             print("    `pip install PySide6` или `pip install gradio`.")
        372 |     if rep.advice:
  ```

- **строка 371** — print() вместо logger

  ```
        369 |             print("    Аудио-ядро (beat/mix/mastering) при этом может быть полностью")
        370 |             print("    рабочим — проверь `python tools/smoke_v29.py`. Установи GUI:")
  >>>   371 |             print("    `pip install PySide6` или `pip install gradio`.")
        372 |     if rep.advice:
        373 |         print("ADVICE:")
  ```

- **строка 373** — print() вместо logger

  ```
        371 |             print("    `pip install PySide6` или `pip install gradio`.")
        372 |     if rep.advice:
  >>>   373 |         print("ADVICE:")
        374 |         for a in rep.advice[:20]:
        375 |             print(f"  - {a}")
  ```

- **строка 375** — print() вместо logger

  ```
        373 |         print("ADVICE:")
        374 |         for a in rep.advice[:20]:
  >>>   375 |             print(f"  - {a}")
        376 |     print("=" * 72)
        377 |     return 0 if rep.core_ok else 2
  ```

- **строка 376** — print() вместо logger

  ```
        374 |         for a in rep.advice[:20]:
        375 |             print(f"  - {a}")
  >>>   376 |     print("=" * 72)
        377 |     return 0 if rep.core_ok else 2
        378 | 
  ```

### MISSING_CLASS_DOCSTRING — 2 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 111** — public class 'ProbeResult' без docstring

  ```
        109 | 
        110 | @dataclass
  >>>   111 | class ProbeResult:
        112 |     key: str
        113 |     name: str
  ```

- **строка 124** — public class 'HealthReport' без docstring

  ```
        122 | 
        123 | @dataclass
  >>>   124 | class HealthReport:
        125 |     generated_at: float = field(default_factory=lambda: time.time())
        126 |     generated_at_human: str = ""
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
         26 | import importlib
  ```

### HIGH_COMPLEXITY — 1 шт. — 🟡 MEDIUM
**Смысл:** Цикломатическая сложность > 15
**Fix:** Разбить на подфункции; if-цепочки → dict-диспатчер.

- **строка 221** — collect: сложность ≈ 18 (>15)

  ```
        219 | 
        220 | 
  >>>   221 | def collect(save_to: Path | None = None) -> HealthReport:
        222 |     """Собрать полный health-report."""
        223 |     rep = HealthReport()
  ```

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 331** — public function 'main' без docstring

  ```
        329 | 
        330 | 
  >>>   331 | def main(argv: list[str] | None = None) -> int:
        332 |     argv = argv or sys.argv[1:]
        333 |     rep = collect()
  ```
