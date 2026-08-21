# АУДИТ ФАЙЛА: `tools/p0_truth_test.py`

**LOC:** 43  |  **Размер:** 1497 байт  |  **Проблем:** 5  |  **Risk score:** 0

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 1 | `struct` | import |
| 2 | `sys` | import |
| 3 | `tempfile` | import |
| 4 | `wave` | import |
| 5 | `pathlib.Path` | from |
| 26 | `modules.matchering_master` | from |
| 26 | `modules.rvc_manager` | from |
| 36 | `app.core.musicgen_texture` | from |
| 40 | `modules.master_pipeline_v12` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 15 | `wav` | 5 | 1 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 5 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 30** — print() вместо logger

  ```
         28 |     try:
         29 |         rvc_manager.infer(str(src), voice_name="definitely_missing")
  >>>    30 |         print("RVC_FAIL: fallback still active")
         31 |     except RuntimeError as e:
         32 |         print("RVC_HONEST_FAIL_PASS:", e)
  ```

- **строка 32** — print() вместо logger

  ```
         30 |         print("RVC_FAIL: fallback still active")
         31 |     except RuntimeError as e:
  >>>    32 |         print("RVC_HONEST_FAIL_PASS:", e)
         33 |     out = Path(d) / "master.wav"
         34 |     r = matchering_master.master_to_stand(str(src), str(out), "streaming")
  ```

- **строка 35** — print() вместо logger

  ```
         33 |     out = Path(d) / "master.wav"
         34 |     r = matchering_master.master_to_stand(str(src), str(out), "streaming")
  >>>    35 |     print("MASTER_RESULT:", r)
         36 |     from app.core import musicgen_texture
         37 | 
  ```

- **строка 39** — print() вместо logger

  ```
         37 | 
         38 |     m = musicgen_texture.generate_texture("test", duration_sec=1, vram_gb=0.0)
  >>>    39 |     print("MUSICGEN_RESULT:", m)
         40 |     from modules import master_pipeline_v12
         41 | 
  ```

- **строка 43** — print() вместо logger

  ```
         41 | 
         42 |     x = master_pipeline_v12.run("api_test", {"references": []}, dry_run=True)
  >>>    43 |     print("PIPELINE_API:", x.get("verdict"), x.get("percent_ready"))
  ```
