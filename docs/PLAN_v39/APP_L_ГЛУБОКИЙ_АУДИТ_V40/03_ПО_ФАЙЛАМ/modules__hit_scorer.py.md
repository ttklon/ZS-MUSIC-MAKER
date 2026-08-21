# АУДИТ ФАЙЛА: `modules/hit_scorer.py`

**LOC:** 588  |  **Размер:** 22110 байт  |  **Проблем:** 4  |  **Risk score:** 3

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 36 | `__future__.annotations` | from |
| 38 | `json` | import |
| 39 | `math` | import |
| 40 | `time` | import |
| 41 | `pathlib.Path` | from |
| 45 | `numpy` | import |
| 50 | `librosa` | import |
| 56 | `soundfile` | import |
| 62 | `pyloudnorm` | import |
| 582 | `sys` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 69 | `_load_audio` | 10 | 4 | ✅ |
| 82 | `_rms` | 3 | 2 | ❌ |
| 88 | `_db` | 1 | 0 | ❌ |
| 93 | `_hook_energy` | 16 | 4 | ✅ |
| 112 | `_hook_repeatability` | 48 | 12 | ✅ |
| 163 | `_chorus_catchiness` | 23 | 2 | ✅ |
| 189 | `_drop_impact` | 14 | 3 | ✅ |
| 206 | `_tiktok_hookability` | 31 | 7 | ✅ |
| 240 | `_bpm_dance_fitness` | 15 | 4 | ❌ |
| 258 | `_loudness_lufs` | 40 | 10 | ✅ |
| 301 | `_stereo_width` | 21 | 7 | ✅ |
| 325 | `_low_end_power` | 22 | 5 | ❌ |
| 350 | `_vocal_presence` | 13 | 2 | ❌ |
| 366 | `_structure_clarity` | 20 | 5 | ❌ |
| 389 | `_novelty` | 13 | 2 | ✅ |
| 422 | `_verdict` | 7 | 3 | ❌ |
| 432 | `_actions` | 58 | 14 | ❌ |
| 494 | `score_track` | 83 | 3 | ✅ |
| 515 | `_add` | 2 | 0 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 2 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 585** — print() вместо logger

  ```
        583 | 
        584 |     if len(sys.argv) < 2:
  >>>   585 |         print("usage: python hit_scorer.py <master.wav> [out.json]")
        586 |         sys.exit(1)
        587 |     r = score_track(sys.argv[1], out_json=sys.argv[2] if len(sys.argv) > 2 else None)
  ```

- **строка 588** — print() вместо logger

  ```
        586 |         sys.exit(1)
        587 |     r = score_track(sys.argv[1], out_json=sys.argv[2] if len(sys.argv) > 2 else None)
  >>>   588 |     print(json.dumps(r, ensure_ascii=False, indent=2))
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 36** — import 'annotations' не используется в теле файла

  ```
         34 | """
         35 | 
  >>>    36 | from __future__ import annotations
         37 | 
         38 | import json
  ```

### SILENT_EXCEPT_PASS — 1 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 282** — except: pass — тихое подавление ошибок

  ```
        280 |                 score = 50.0
        281 |             return score, lufs
  >>>   282 |         except Exception:
        283 |             pass
        284 | 
  ```
