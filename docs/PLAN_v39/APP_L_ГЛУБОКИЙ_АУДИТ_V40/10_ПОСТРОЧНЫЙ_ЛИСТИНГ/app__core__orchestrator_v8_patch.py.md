# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/core/orchestrator_v8_patch.py`

**Всего строк:** 136

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 62 | 45.6 |
| blank | 19 | 14.0 |
| docstring | 17 | 12.5 |
| try_block | 10 | 7.4 |
| branch | 9 | 6.6 |
| comment | 7 | 5.1 |
| import | 6 | 4.4 |
| def | 3 | 2.2 |
| return | 3 | 2.2 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v8] orchestrator_v8_patch.py — накладываемый патч на v7 Orchestrator.
    3 [blank     ] 
    4 [docstring ] Не переписываем orchestrator.py v7 (сохраняем как есть). Вместо этого:
    5 [docstring ]   • Обёртка `run_pipeline_v8(orch, recipe, stage_hook)` вызывает v7 pipeline,
    6 [docstring ]     а сверху добавляет:
    7 [docstring ]       1. lyrics_gen_v8 (автор-референс + trend_scout_v3 + слэнг сегодня);
    8 [docstring ]       2. female_backing (женский бэк на припеве, если включён);
    9 [docstring ]       3. auto_qa (аудит финального master.wav);
   10 [docstring ]       4. авто-рестарт нужных узлов при verdict="rebuild"/"patch".
   11 [blank     ] 
   12 [docstring ] Экспорт для orchestrator.py: apply(orch) — монки-патчит метод run_pipeline
   13 [docstring ] на v8-версию.
   14 [docstring ] """
   15 [blank     ] 
   16 [import    ] from __future__ import annotations
   17 [blank     ] 
   18 [import    ] import traceback
   19 [import    ] from pathlib import Path
   20 [blank     ] 
   21 [blank     ] 
   22 [def       ] def _stage(hook, name: str, progress: float):
   23 [try_block ]     try:
   24 [branch    ]         if callable(hook):
   25 [code      ]             hook(name, progress)
   26 [try_block ]     except Exception:
   27 [code      ]         pass
   28 [blank     ] 
   29 [blank     ] 
   30 [def       ] def run_pipeline_v8(orch, recipe: dict, stage_hook=None):
   31 [docstring ]     """
   32 [docstring ]     Полный v8 pipeline. `orch` — экземпляр v7 Orchestrator.
   33 [docstring ]     Возвращает dict с результатами (пути к файлам).
   34 [docstring ]     """
   35 [code      ]     log = getattr(orch, "log", lambda *a, **k: None)
   36 [blank     ] 
   37 [comment   ]     # ---------- 0) v8 lyrics с автором-референсом ------------------
   38 [code      ]     _stage(stage_hook, "lyrics_v8", 0.10)
   39 [try_block ]     try:
   40 [import    ]         from modules.lyrics_gen_v8 import generate_lyrics_v8
   41 [blank     ] 
   42 [code      ]         lyrics_res = generate_lyrics_v8(
   43 [code      ]             theme=recipe.get("theme", "лето тачки"),
   44 [code      ]             user_words=recipe.get("user_lyrics_lines", []),
   45 [code      ]             bpm=int(recipe.get("bpm", 130)),
   46 [code      ]             author=recipe.get("author_ref", None),
   47 [code      ]             target_lines=recipe.get("target_lines", 16),
   48 [code      ]             want_female_backing=recipe.get("female_backing", False),
   49 [code      ]             lang_mix=recipe.get("lang_mix", "ru+en"),
   50 [code      ]         )
   51 [code      ]         recipe["lyrics_text"] = lyrics_res["text"]
   52 [code      ]         recipe["chorus_lines"] = lyrics_res["chorus_lines"]
   53 [code      ]         recipe["used_slang"] = lyrics_res["used_slang"]
   54 [code      ]         log(
   55 [code      ]             f"[v8] lyrics: author_style={lyrics_res['author_style_used']}, "
   56 [code      ]             f"slang={len(lyrics_res['used_slang'])}"
   57 [code      ]         )
   58 [try_block ]     except Exception as e:
   59 [code      ]         log(f"[v8] lyrics_v8 FAILED, use v7 default: {e}")
   60 [blank     ] 
   61 [comment   ]     # ---------- 1) v7 core pipeline (analyze → beat → voice → mix) ---
   62 [code      ]     _stage(stage_hook, "v7_core", 0.20)
   63 [code      ]     result = {}
   64 [branch    ]     if hasattr(orch, "_run_pipeline_v7"):
   65 [code      ]         result = orch._run_pipeline_v7(recipe, stage_hook=stage_hook) or {}
   66 [branch    ]     else:
   67 [comment   ]         # v7 exposes run_pipeline directly
   68 [try_block ]         try:
   69 [code      ]             result = orch.run_pipeline(recipe, stage_hook=stage_hook) or {}
   70 [try_block ]         except Exception as e:
   71 [code      ]             log(f"[v8] v7 pipeline failed: {e}\n{traceback.format_exc()}")
   72 [code      ]             result = {"error": str(e)}
   73 [blank     ] 
   74 [comment   ]     # ---------- 2) female backing (после сборки основного вокала) ----
   75 [branch    ]     if recipe.get("female_backing") and result.get("vocal_wav"):
   76 [code      ]         _stage(stage_hook, "female_backing", 0.78)
   77 [try_block ]         try:
   78 [import    ]             from modules.female_backing import (
   79 [code      ]                 make_chorus_backing,
   80 [code      ]                 mix_backing_into_vocal,
   81 [code      ]             )
   82 [blank     ] 
   83 [code      ]             chorus_lines = recipe.get("chorus_lines", []) or [
   84 [code      ]                 "night ride, we don't stop"
   85 [code      ]             ]
   86 [code      ]             backing = make_chorus_backing(chorus_lines)
   87 [code      ]             new_vocal = mix_backing_into_vocal(
   88 [code      ]                 result["vocal_wav"], backing, backing_gain_db=-9.0
   89 [code      ]             )
   90 [code      ]             result["vocal_wav"] = str(new_vocal)
   91 [code      ]             result["backing_wav"] = str(backing)
   92 [code      ]             log(f"[v8] female_backing mixed: {backing}")
   93 [try_block ]         except Exception as e:
   94 [code      ]             log(f"[v8] female_backing failed: {e}")
   95 [blank     ] 
   96 [comment   ]     # ---------- 3) Auto QA ------------------------------------------
   97 [code      ]     master_path = result.get("master_wav") or result.get("master") or ""
   98 [branch    ]     if master_path and Path(master_path).exists():
   99 [code      ]         _stage(stage_hook, "auto_qa", 0.92)
  100 [try_block ]         try:
  101 [import    ]             from modules.auto_qa import audit_track, should_retry
  102 [blank     ] 
  103 [code      ]             report = audit_track(master_path)
  104 [code      ]             result["auto_qa"] = report
  105 [code      ]             log(f"[v8] auto_qa verdict: {report.get('verdict_text')}")
  106 [blank     ] 
  107 [comment   ]             # автоматическая пересборка узлов при verdict != release
  108 [branch    ]             if recipe.get("auto_qa_loop", False):
  109 [code      ]                 retry, targets = should_retry(
  110 [code      ]                     report,
  111 [code      ]                     max_iterations=recipe.get("max_qa_iters", 2),
  112 [code      ]                     current_iter=recipe.get("_qa_iter", 0),
  113 [code      ]                 )
  114 [branch    ]                 if retry:
  115 [code      ]                     recipe["_qa_iter"] = recipe.get("_qa_iter", 0) + 1
  116 [code      ]                     recipe["rebuild_targets"] = targets
  117 [code      ]                     log(f"[v8] auto_qa retry #{recipe['_qa_iter']} → {targets}")
  118 [comment   ]                     # рекурсивно повторяем только нужные узлы
  119 [return    ]                     return run_pipeline_v8(orch, recipe, stage_hook)
  120 [try_block ]         except Exception as e:
  121 [code      ]             log(f"[v8] auto_qa failed: {e}")
  122 [blank     ] 
  123 [code      ]     _stage(stage_hook, "done_v8", 1.0)
  124 [return    ]     return result
  125 [blank     ] 
  126 [blank     ] 
  127 [def       ] def apply(orch):
  128 [docstring ]     """Монки-патчим экземпляр orchestrator: run_pipeline → v8-версия."""
  129 [branch    ]     if hasattr(orch, "_v8_applied"):
  130 [return    ]         return
  131 [branch    ]     if hasattr(orch, "run_pipeline"):
  132 [code      ]         orch._run_pipeline_v7 = orch.run_pipeline
  133 [code      ]         orch.run_pipeline = lambda recipe, stage_hook=None: run_pipeline_v8(
  134 [code      ]             orch, recipe, stage_hook
  135 [code      ]         )
  136 [code      ]     orch._v8_applied = True
```