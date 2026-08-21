# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/core/orchestrator_v9_patch.py`

**Всего строк:** 284

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 155 | 54.6 |
| blank | 38 | 13.4 |
| try_block | 24 | 8.5 |
| docstring | 18 | 6.3 |
| import | 16 | 5.6 |
| branch | 13 | 4.6 |
| comment | 12 | 4.2 |
| def | 4 | 1.4 |
| loop | 2 | 0.7 |
| return | 2 | 0.7 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v9] orchestrator_v9_patch.py — накладываемый патч на v8 Orchestrator.
    3 [blank     ] 
    4 [docstring ] НИЧЕГО не удаляет из v7/v8. Только оборачивает.
    5 [blank     ] 
    6 [docstring ] Порядок цепочки в run_pipeline_v9(orch, recipe, hook):
    7 [docstring ]    0. reference_ingest.build_style_vector(refs, weights)          — style vector
    8 [docstring ]    1. arrangement_engine.build_arrangement(sv, sec, seed, variant) — план
    9 [docstring ]    2. sample_hunter_v9.unified_search(sv)                         — сэмплы+манифест
   10 [docstring ]    3. v8 run_pipeline_v8(orch, recipe, hook)                      — core (v7 core)
   11 [docstring ]    4. voice_vault_v9.maybe_trigger_retrain()                      — RVC дотрейн (async)
   12 [docstring ]    5. anti_ai_polish.polish_track(master_wav, ...)                — устранение нейроношности
   13 [docstring ]    6. mastering_v9.render_all_stands(polished, stands_dir)        — 3 стенда
   14 [docstring ]    7. hit_scorer.score_track(streaming_master)                    — HIT score
   15 [docstring ]    8. tiktok_edit_v9.make_all_cuts(streaming_master, ...)         — TikTok cuts
   16 [docstring ]    9. release_pack_v9.build_release_v9(release_dir, ...)          — full pack
   17 [blank     ] 
   18 [docstring ] apply(orch) монки-патчит метод run_pipeline. При отсутствии зависимостей —
   19 [docstring ] gracefully проваливается на v8 (v7 fallback).
   20 [docstring ] """
   21 [blank     ] 
   22 [import    ] from __future__ import annotations
   23 [blank     ] 
   24 [import    ] import json
   25 [import    ] import time
   26 [import    ] import traceback
   27 [import    ] from pathlib import Path
   28 [blank     ] 
   29 [blank     ] 
   30 [def       ] def _stage(hook, name: str, progress: float):
   31 [try_block ]     try:
   32 [branch    ]         if callable(hook):
   33 [code      ]             hook(name, progress)
   34 [try_block ]     except Exception:
   35 [code      ]         pass
   36 [blank     ] 
   37 [blank     ] 
   38 [def       ] def run_pipeline_v9(orch, recipe: dict, stage_hook=None):
   39 [code      ]     log = getattr(orch, "log", lambda *a, **k: None)
   40 [code      ]     project_id = recipe.get("track_id") or f"track_{int(time.time())}"
   41 [code      ]     project_dir = Path(recipe.get("project_dir") or f"output/projects/{project_id}")
   42 [code      ]     project_dir.mkdir(parents=True, exist_ok=True)
   43 [blank     ] 
   44 [comment   ]     # 0. reference ingest
   45 [code      ]     _stage(stage_hook, "reference_ingest", 0.03)
   46 [code      ]     style_fp = None
   47 [try_block ]     try:
   48 [import    ]         from modules.reference_ingest import build_style_vector
   49 [blank     ] 
   50 [code      ]         refs = recipe.get("references") or []
   51 [code      ]         weights = recipe.get("reference_weights") or [1.0] * len(refs)
   52 [branch    ]         if refs:
   53 [code      ]             style_fp = build_style_vector(refs, weights=weights)
   54 [code      ]             recipe["_style_fp"] = style_fp
   55 [code      ]             log(
   56 [code      ]                 f"[v9] style_vector: bpm={style_fp['consensus']['bpm']}, "
   57 [code      ]                 f"genre={style_fp['consensus']['genre_hint']}"
   58 [code      ]             )
   59 [try_block ]     except Exception as e:
   60 [code      ]         log(f"[v9] reference_ingest failed: {e}")
   61 [blank     ] 
   62 [comment   ]     # 1. arrangement plan
   63 [code      ]     _stage(stage_hook, "arrangement", 0.08)
   64 [code      ]     plan = None
   65 [try_block ]     try:
   66 [import    ]         from modules.arrangement_engine import build_arrangement
   67 [blank     ] 
   68 [code      ]         sv = (style_fp or {}).get("style_vector") or {"bpm": recipe.get("bpm", 130.0)}
   69 [code      ]         plan = build_arrangement(
   70 [code      ]             sv,
   71 [code      ]             total_seconds=recipe.get("duration_sec", 150.0),
   72 [code      ]             seed=recipe.get("seed"),
   73 [code      ]             variant=recipe.get("variant", 0),
   74 [code      ]         )
   75 [code      ]         recipe["_arrangement_plan"] = plan
   76 [code      ]         log(
   77 [code      ]             f"[v9] arrangement: {len(plan['sections'])} sections, "
   78 [code      ]             f"{plan['total_sec']}s"
   79 [code      ]         )
   80 [try_block ]     except Exception as e:
   81 [code      ]         log(f"[v9] arrangement failed: {e}")
   82 [blank     ] 
   83 [comment   ]     # 2. sample hunter
   84 [code      ]     _stage(stage_hook, "sample_hunter_v9", 0.12)
   85 [code      ]     sample_manifest = None
   86 [try_block ]     try:
   87 [import    ]         from agents.sample_hunter_v9 import save_manifest, unified_search
   88 [blank     ] 
   89 [code      ]         sv = (style_fp or {}).get("style_vector") or {}
   90 [code      ]         u = unified_search(sv, include_online=recipe.get("online_samples", False))
   91 [code      ]         sample_manifest_path = save_manifest(
   92 [code      ]             (u.get("local", []) + u.get("online", [])), project_id
   93 [code      ]         )
   94 [code      ]         sample_manifest = json.loads(
   95 [code      ]             Path(sample_manifest_path).read_text(encoding="utf-8")
   96 [code      ]         )
   97 [code      ]         log(f"[v9] samples: {u['total']} candidates ({len(u['local'])} local)")
   98 [try_block ]     except Exception as e:
   99 [code      ]         log(f"[v9] sample_hunter_v9 failed: {e}")
  100 [blank     ] 
  101 [comment   ]     # 3. v8 core pipeline
  102 [code      ]     _stage(stage_hook, "v8_core", 0.20)
  103 [code      ]     result = {}
  104 [try_block ]     try:
  105 [import    ]         from app.core.orchestrator_v8_patch import run_pipeline_v8
  106 [blank     ] 
  107 [code      ]         result = run_pipeline_v8(orch, recipe, stage_hook=stage_hook) or {}
  108 [try_block ]     except Exception as e:
  109 [code      ]         log(f"[v9] v8 core failed: {e}\n{traceback.format_exc()}")
  110 [code      ]         result = {"error": str(e)}
  111 [blank     ] 
  112 [code      ]     master_wav = result.get("master_wav") or recipe.get("master_wav")
  113 [blank     ] 
  114 [comment   ]     # 4. voice_vault → возможно триггерим RVC дотрейн (не блокируем pipeline)
  115 [code      ]     _stage(stage_hook, "voice_vault_check", 0.75)
  116 [try_block ]     try:
  117 [import    ]         from modules.voice_vault_v9 import maybe_trigger_retrain
  118 [blank     ] 
  119 [code      ]         rv = maybe_trigger_retrain()
  120 [code      ]         result["voice_vault_retrain"] = rv
  121 [branch    ]         if rv.get("triggered"):
  122 [code      ]             log("[v9] RVC retrain triggered (background)")
  123 [try_block ]     except Exception as e:
  124 [code      ]         log(f"[v9] voice_vault_v9 check failed: {e}")
  125 [blank     ] 
  126 [comment   ]     # 5. anti-ai polish
  127 [code      ]     polished_wav = None
  128 [branch    ]     if master_wav and Path(master_wav).exists():
  129 [code      ]         _stage(stage_hook, "anti_ai_polish", 0.80)
  130 [try_block ]         try:
  131 [import    ]             from modules.anti_ai_polish import polish_track
  132 [blank     ] 
  133 [code      ]             polished_wav = str(project_dir / "master_polished.wav")
  134 [code      ]             preset = recipe.get("polish_preset", "standard")
  135 [code      ]             polish_r = polish_track(
  136 [code      ]                 master_wav,
  137 [code      ]                 polished_wav,
  138 [code      ]                 arrangement_plan=plan,
  139 [code      ]                 preset=preset,
  140 [code      ]                 seed=recipe.get("seed"),
  141 [code      ]             )
  142 [branch    ]             if not polish_r.get("ok"):
  143 [code      ]                 polished_wav = master_wav
  144 [code      ]             log(f"[v9] anti_ai_polish: {polish_r.get('stages_applied')}")
  145 [try_block ]         except Exception as e:
  146 [code      ]             log(f"[v9] anti_ai_polish failed: {e}")
  147 [code      ]             polished_wav = master_wav
  148 [branch    ]     else:
  149 [code      ]         polished_wav = master_wav
  150 [blank     ] 
  151 [comment   ]     # 6. mastering stands
  152 [code      ]     _stage(stage_hook, "mastering_v9", 0.87)
  153 [code      ]     stand_wavs = {}
  154 [try_block ]     try:
  155 [import    ]         from modules.mastering_v9 import render_all_stands
  156 [blank     ] 
  157 [branch    ]         if polished_wav and Path(polished_wav).exists():
  158 [code      ]             stands_dir = project_dir / "stands"
  159 [code      ]             mres = render_all_stands(
  160 [code      ]                 polished_wav, str(stands_dir), artist=recipe.get("artist_name", "")
  161 [code      ]             )
  162 [loop      ]             for name in ("car", "club", "streaming"):
  163 [code      ]                 r = mres.get("results", {}).get(name, {})
  164 [branch    ]                 if r.get("ok"):
  165 [code      ]                     stand_wavs[name] = r.get("output")
  166 [code      ]             log(f"[v9] mastering stands: {list(stand_wavs.keys())}")
  167 [try_block ]     except Exception as e:
  168 [code      ]         log(f"[v9] mastering_v9 failed: {e}")
  169 [blank     ] 
  170 [comment   ]     # 7. hit_scorer на streaming-мастере (или polished если нет)
  171 [code      ]     hit_report = None
  172 [code      ]     _stage(stage_hook, "hit_scorer", 0.92)
  173 [try_block ]     try:
  174 [import    ]         from modules.hit_scorer import score_track
  175 [blank     ] 
  176 [code      ]         target_for_score = stand_wavs.get("streaming") or polished_wav or master_wav
  177 [branch    ]         if target_for_score and Path(target_for_score).exists():
  178 [code      ]             hit_report = score_track(
  179 [code      ]                 target_for_score, out_json=str(project_dir / "hit_score.json")
  180 [code      ]             )
  181 [code      ]             log(
  182 [code      ]                 f"[v9] hit_score={hit_report.get('hit_score')} "
  183 [code      ]                 f"verdict={hit_report.get('verdict')}"
  184 [code      ]             )
  185 [try_block ]     except Exception as e:
  186 [code      ]         log(f"[v9] hit_scorer failed: {e}")
  187 [blank     ] 
  188 [comment   ]     # 8. tiktok cuts
  189 [code      ]     _stage(stage_hook, "tiktok_edit", 0.95)
  190 [code      ]     tiktok_wavs = {}
  191 [try_block ]     try:
  192 [import    ]         from modules.tiktok_edit_v9 import make_all_cuts
  193 [blank     ] 
  194 [code      ]         src = stand_wavs.get("streaming") or polished_wav or master_wav
  195 [branch    ]         if src and Path(src).exists():
  196 [code      ]             tt_dir = project_dir / "tiktok"
  197 [code      ]             tres = make_all_cuts(
  198 [code      ]                 src, str(tt_dir), hit_report=hit_report, arrangement_plan=plan
  199 [code      ]             )
  200 [loop      ]             for name, r in tres.get("results", {}).items():
  201 [branch    ]                 if r.get("ok"):
  202 [code      ]                     tiktok_wavs[name] = r.get("output")
  203 [code      ]             log(f"[v9] tiktok cuts: {list(tiktok_wavs.keys())}")
  204 [try_block ]     except Exception as e:
  205 [code      ]         log(f"[v9] tiktok_edit failed: {e}")
  206 [blank     ] 
  207 [comment   ]     # 9. release pack v9
  208 [code      ]     _stage(stage_hook, "release_pack_v9", 0.98)
  209 [try_block ]     try:
  210 [import    ]         from modules.release_pack_v9 import build_release_v9
  211 [blank     ] 
  212 [code      ]         release_dir = str(project_dir / "release")
  213 [comment   ]         # voice manifest (best-effort)
  214 [code      ]         voice_manifest = None
  215 [try_block ]         try:
  216 [import    ]             from modules.voice_vault_v9 import export_manifest_for_rvc
  217 [blank     ] 
  218 [code      ]             vm_path = export_manifest_for_rvc(
  219 [code      ]                 out_path=str(project_dir / "voice_manifest.json")
  220 [code      ]             )
  221 [code      ]             voice_manifest = json.loads(Path(vm_path).read_text(encoding="utf-8"))
  222 [try_block ]         except Exception:
  223 [code      ]             pass
  224 [blank     ] 
  225 [code      ]         meta = {
  226 [code      ]             "artist": recipe.get("artist_name", ""),
  227 [code      ]             "title": recipe.get("title") or recipe.get("theme", ""),
  228 [code      ]             "bpm": (plan or {}).get("bpm"),
  229 [code      ]             "key": (plan or {}).get("key"),
  230 [code      ]             "mode": (plan or {}).get("mode"),
  231 [code      ]             "genre": (plan or {}).get("genre"),
  232 [code      ]             "mood": (plan or {}).get("mood"),
  233 [code      ]             "duration_s": (plan or {}).get("total_sec"),
  234 [code      ]         }
  235 [code      ]         pack_r = build_release_v9(
  236 [code      ]             release_dir=release_dir,
  237 [code      ]             project_meta=meta,
  238 [code      ]             master_wav=polished_wav or master_wav or "",
  239 [code      ]             hit_report=hit_report,
  240 [code      ]             arrangement_plan=plan,
  241 [code      ]             style_fingerprint=style_fp,
  242 [code      ]             sample_manifest=sample_manifest,
  243 [code      ]             voice_manifest=voice_manifest,
  244 [code      ]             stand_wavs=stand_wavs,
  245 [code      ]             tiktok_wavs=tiktok_wavs,
  246 [code      ]         )
  247 [code      ]         result["release_v9"] = pack_r
  248 [code      ]         log(f"[v9] release: {pack_r.get('n_files_added')} files")
  249 [try_block ]     except Exception as e:
  250 [code      ]         log(f"[v9] release_pack_v9 failed: {e}")
  251 [blank     ] 
  252 [code      ]     _stage(stage_hook, "done_v9", 1.0)
  253 [blank     ] 
  254 [comment   ]     # Собираем итог
  255 [code      ]     result.update(
  256 [code      ]         {
  257 [code      ]             "v9_ok": True,
  258 [code      ]             "master_wav": master_wav,
  259 [code      ]             "polished_wav": polished_wav,
  260 [code      ]             "stand_wavs": stand_wavs,
  261 [code      ]             "tiktok_wavs": tiktok_wavs,
  262 [code      ]             "hit_report": hit_report,
  263 [code      ]             "arrangement_plan_file": (
  264 [code      ]                 str(project_dir / "arrangement_plan.json") if plan else None
  265 [code      ]             ),
  266 [code      ]             "project_id": project_id,
  267 [code      ]             "project_dir": str(project_dir),
  268 [code      ]         }
  269 [code      ]     )
  270 [return    ]     return result
  271 [blank     ] 
  272 [blank     ] 
  273 [def       ] def apply(orch) -> None:
  274 [docstring ]     """Монки-патч. Оборачивает orch.run_pipeline в v9-версию."""
  275 [branch    ]     if not hasattr(orch, "_run_pipeline_v8"):
  276 [code      ]         original = getattr(orch, "run_pipeline", None)
  277 [branch    ]         if original:
  278 [code      ]             orch._run_pipeline_v8 = original
  279 [blank     ] 
  280 [def       ]     def _wrapper(recipe, stage_hook=None):
  281 [return    ]         return run_pipeline_v9(orch, recipe, stage_hook=stage_hook)
  282 [blank     ] 
  283 [code      ]     orch.run_pipeline = _wrapper
  284 [code      ]     orch._v9_applied = True
```