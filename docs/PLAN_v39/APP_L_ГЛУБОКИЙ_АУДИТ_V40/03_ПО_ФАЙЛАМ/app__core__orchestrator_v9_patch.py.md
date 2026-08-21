# АУДИТ ФАЙЛА: `app/core/orchestrator_v9_patch.py`

**LOC:** 284  |  **Размер:** 10660 байт  |  **Проблем:** 6  |  **Risk score:** 9

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 22 | `__future__.annotations` | from |
| 24 | `json` | import |
| 25 | `time` | import |
| 26 | `traceback` | import |
| 27 | `pathlib.Path` | from |
| 48 | `modules.reference_ingest.build_style_vector` | from |
| 66 | `modules.arrangement_engine.build_arrangement` | from |
| 87 | `agents.sample_hunter_v9.save_manifest` | from |
| 87 | `agents.sample_hunter_v9.unified_search` | from |
| 105 | `app.core.orchestrator_v8_patch.run_pipeline_v8` | from |
| 117 | `modules.voice_vault_v9.maybe_trigger_retrain` | from |
| 155 | `modules.mastering_v9.render_all_stands` | from |
| 174 | `modules.hit_scorer.score_track` | from |
| 192 | `modules.tiktok_edit_v9.make_all_cuts` | from |
| 210 | `modules.release_pack_v9.build_release_v9` | from |
| 131 | `modules.anti_ai_polish.polish_track` | from |
| 216 | `modules.voice_vault_v9.export_manifest_for_rvc` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 30 | `_stage` | 5 | 2 | ❌ |
| 38 | `run_pipeline_v9` | 232 | 46 | ❌ |
| 273 | `apply` | 11 | 2 | ✅ |
| 280 | `_wrapper` | 1 | 0 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### SILENT_EXCEPT_PASS — 2 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 34** — except: pass — тихое подавление ошибок

  ```
         32 |         if callable(hook):
         33 |             hook(name, progress)
  >>>    34 |     except Exception:
         35 |         pass
         36 | 
  ```

- **строка 222** — except: pass — тихое подавление ошибок

  ```
        220 |             )
        221 |             voice_manifest = json.loads(Path(vm_path).read_text(encoding="utf-8"))
  >>>   222 |         except Exception:
        223 |             pass
        224 | 
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 22** — import 'annotations' не используется в теле файла

  ```
         20 | """
         21 | 
  >>>    22 | from __future__ import annotations
         23 | 
         24 | import json
  ```

### LONG_FUNCTION — 1 шт. — 🟡 MEDIUM
**Смысл:** Функция > 100 LOC — сложно тестировать/поддерживать
**Fix:** Декомпозировать: приватные `_helper()`, тестировать по частям.

- **строка 38** — run_pipeline_v9: 232 LOC (>100) — декомпозиция

  ```
         36 | 
         37 | 
  >>>    38 | def run_pipeline_v9(orch, recipe: dict, stage_hook=None):
         39 |     log = getattr(orch, "log", lambda *a, **k: None)
         40 |     project_id = recipe.get("track_id") or f"track_{int(time.time())}"
  ```

### HIGH_COMPLEXITY — 1 шт. — 🟡 MEDIUM
**Смысл:** Цикломатическая сложность > 15
**Fix:** Разбить на подфункции; if-цепочки → dict-диспатчер.

- **строка 38** — run_pipeline_v9: сложность ≈ 46 (>15)

  ```
         36 | 
         37 | 
  >>>    38 | def run_pipeline_v9(orch, recipe: dict, stage_hook=None):
         39 |     log = getattr(orch, "log", lambda *a, **k: None)
         40 |     project_id = recipe.get("track_id") or f"track_{int(time.time())}"
  ```

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 38** — public function 'run_pipeline_v9' без docstring

  ```
         36 | 
         37 | 
  >>>    38 | def run_pipeline_v9(orch, recipe: dict, stage_hook=None):
         39 |     log = getattr(orch, "log", lambda *a, **k: None)
         40 |     project_id = recipe.get("track_id") or f"track_{int(time.time())}"
  ```
