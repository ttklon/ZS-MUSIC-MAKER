# АУДИТ ФАЙЛА: `modules/hit_kpi_monitor_v11.py`

**LOC:** 349  |  **Размер:** 12383 байт  |  **Проблем:** 13  |  **Risk score:** 3

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 12 | `__future__.annotations` | from |
| 14 | `fnmatch` | import |
| 15 | `json` | import |
| 16 | `os` | import |
| 17 | `sys` | import |
| 18 | `time` | import |
| 19 | `dataclasses.asdict` | from |
| 19 | `dataclasses.dataclass` | from |
| 19 | `dataclasses.field` | from |
| 317 | `tempfile` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 22 | `_safe_print` | 4 | 1 | ❌ |
| 114 | `check_release_completeness` | 49 | 10 | ❌ |
| 166 | `check_ai_detector` | 24 | 10 | ❌ |
| 193 | `finalize_session` | 71 | 13 | ❌ |
| 267 | `render_kpi_report_md` | 31 | 4 | ❌ |
| 301 | `latest_sessions` | 12 | 4 | ❌ |
| 316 | `_self_test` | 29 | 2 | ❌ |
| 75 | `duration_min` | 1 | 0 | ❌ |
| 93 | `pipeline_min` | 2 | 1 | ❌ |
| 97 | `start_stage` | 3 | 0 | ❌ |
| 102 | `end_stage` | 3 | 0 | ❌ |
| 107 | `to_dict` | 4 | 0 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 67 | `KpiStage` | ❌ |
| 80 | `KpiSession` | ❌ |

## Проблемы (детально, с цитатой кода)

### MISSING_DOCSTRING — 5 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 114** — public function 'check_release_completeness' без docstring

  ```
        112 | 
        113 | 
  >>>   114 | def check_release_completeness(release_dir, hw_mode="full_hw"):
        115 |     required = KPI_TARGETS.get(hw_mode, KPI_TARGETS["full_hw"])["release_required"]
        116 |     patterns = {
  ```

- **строка 166** — public function 'check_ai_detector' без docstring

  ```
        164 | 
        165 | 
  >>>   166 | def check_ai_detector(report):
        167 |     if not report:
        168 |         return -1.0
  ```

- **строка 193** — public function 'finalize_session' без docstring

  ```
        191 | 
        192 | 
  >>>   193 | def finalize_session(
        194 |     session, release_dir=None, ai_detector_report=None, save_dir="data"
        195 | ):
  ```

- **строка 267** — public function 'render_kpi_report_md' без docstring

  ```
        265 | 
        266 | 
  >>>   267 | def render_kpi_report_md(session):
        268 |     lines = [
        269 |         "# KPI-отчёт по проекту `" + session.project_id + "`",
  ```

- **строка 301** — public function 'latest_sessions' без docstring

  ```
        299 | 
        300 | 
  >>>   301 | def latest_sessions(save_dir="data", limit=20):
        302 |     p = os.path.join(save_dir, "kpi_history.jsonl")
        303 |     if not os.path.exists(p):
  ```

### MISSING_CLASS_DOCSTRING — 2 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 67** — public class 'KpiStage' без docstring

  ```
         65 | 
         66 | @dataclass
  >>>    67 | class KpiStage:
         68 |     name: str
         69 |     started_at: float = 0.0
  ```

- **строка 80** — public class 'KpiSession' без docstring

  ```
         78 | 
         79 | @dataclass
  >>>    80 | class KpiSession:
         81 |     project_id: str
         82 |     hw_mode: str = "full_hw"
  ```

### BARE_PRINT — 2 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 24** — print() вместо logger

  ```
         22 | def _safe_print(msg):
         23 |     try:
  >>>    24 |         print(msg)
         25 |     except UnicodeEncodeError:
         26 |         sys.stdout.buffer.write((msg + "\n").encode("cp866", errors="replace"))
  ```

- **строка 349** — print() вместо logger

  ```
        347 | 
        348 | if __name__ == "__main__":
  >>>   349 |     print("hit_kpi_monitor_v11 self-test:", "OK" if _self_test() else "FAIL")
  ```

### BLOCKING_SLEEP — 2 шт. — 🟢 LOW
**Смысл:** time.sleep() без комментария/аргументации
**Fix:** Комментарий или await asyncio.sleep().

- **строка 322** — time.sleep(...) без пояснения

  ```
        320 |         s = KpiSession(project_id="test01", hw_mode="fallback_hw")
        321 |         st = s.start_stage("mix")
  >>>   322 |         time.sleep(0.02)
        323 |         s.end_stage(st, True)
        324 |         st2 = s.start_stage("rvc_train")
  ```

- **строка 325** — time.sleep(...) без пояснения

  ```
        323 |         s.end_stage(st, True)
        324 |         st2 = s.start_stage("rvc_train")
  >>>   325 |         time.sleep(0.02)
        326 |         s.end_stage(st2, True)
        327 |         rd = os.path.join(tmp, "rel")
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 12** — import 'annotations' не используется в теле файла

  ```
         10 | """
         11 | 
  >>>    12 | from __future__ import annotations
         13 | 
         14 | import fnmatch
  ```

### SILENT_EXCEPT_PASS — 1 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 183** — except: pass — тихое подавление ошибок

  ```
        181 |                 if v <= 1.0:
        182 |                     return v * 100.0
  >>>   183 |             except Exception:
        184 |                 pass
        185 |     for k in ("summary", "verdict", "final"):
  ```
