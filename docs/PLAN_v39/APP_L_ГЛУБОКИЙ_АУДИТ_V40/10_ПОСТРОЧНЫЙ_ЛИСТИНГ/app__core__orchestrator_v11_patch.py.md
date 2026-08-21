# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/core/orchestrator_v11_patch.py`

**Всего строк:** 401

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 268 | 66.8 |
| blank | 34 | 8.5 |
| try_block | 30 | 7.5 |
| branch | 22 | 5.5 |
| import | 10 | 2.5 |
| comment | 8 | 2.0 |
| docstring | 7 | 1.7 |
| def | 7 | 1.7 |
| loop | 5 | 1.2 |
| return | 5 | 1.2 |
| stmt | 5 | 1.2 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v11 — orchestrator_v11_patch.py
    3 [blank     ] 
    4 [docstring ] Master orchestrator для v11. Соединяет ВСЕ модули (v7 → v8 → v9 → v10 → v11)
    5 [docstring ] в единый `run_full_pipeline_v11()`, реализующий ТЗ 20.5 KPI.
    6 [docstring ] """
    7 [blank     ] 
    8 [import    ] from __future__ import annotations
    9 [blank     ] 
   10 [import    ] import json
   11 [import    ] import os
   12 [import    ] import sys
   13 [import    ] import time
   14 [import    ] import traceback
   15 [import    ] from pathlib import Path
   16 [blank     ] 
   17 [code      ] ROOT = Path(__file__).resolve().parents[2]
   18 [code      ] sys.path.insert(0, str(ROOT))
   19 [blank     ] 
   20 [blank     ] 
   21 [def       ] def _safe_print(msg):
   22 [try_block ]     try:
   23 [code      ]         print(msg)
   24 [try_block ]     except UnicodeEncodeError:
   25 [code      ]         sys.stdout.buffer.write((msg + "\n").encode("cp866", errors="replace"))
   26 [blank     ] 
   27 [blank     ] 
   28 [def       ] def _load_deps():
   29 [code      ]     deps = {}
   30 [loop      ]     for name, path in [
   31 [code      ]         ("video_edit", "modules.video_edit_v11"),
   32 [code      ]         ("dist", "modules.distribution_export_v11"),
   33 [code      ]         ("kpi", "modules.hit_kpi_monitor_v11"),
   34 [code      ]         ("expert", "modules.expert_mode_v11"),
   35 [code      ]     ]:
   36 [try_block ]         try:
   37 [code      ]             deps[name] = __import__(path, fromlist=["*"])
   38 [try_block ]         except Exception as e:
   39 [code      ]             _safe_print(f"[orch_v11] {path} unavailable: {e}")
   40 [loop      ]     for name, path in [
   41 [code      ]         ("v10_patch", "app.core.orchestrator_v10_patch"),
   42 [code      ]         ("v9_patch", "app.core.orchestrator_v9_patch"),
   43 [code      ]         ("hw", "app.core.hw_autodetect"),
   44 [code      ]     ]:
   45 [try_block ]         try:
   46 [code      ]             deps[name] = __import__(path, fromlist=["*"])
   47 [try_block ]         except Exception as e:
   48 [code      ]             _safe_print(f"[orch_v11] {path} unavailable: {e}")
   49 [return    ]     return deps
   50 [blank     ] 
   51 [blank     ] 
   52 [def       ] def run_full_pipeline_v11(
   53 [code      ]     project_id, wizard_state, expert_config=None, progress_cb=None, project_root=None
   54 [code      ] ):
   55 [docstring ]     """Единая точка входа полного пайплайна v11."""
   56 [code      ]     t0 = time.time()
   57 [code      ]     errors, warnings, stages_ran = [], [], []
   58 [code      ]     root = Path(project_root) if project_root else ROOT
   59 [blank     ] 
   60 [def       ]     def prog(stage, pct, msg=""):
   61 [code      ]         _safe_print(f"[orch_v11][{pct*100:5.1f}%] {stage}: {msg}")
   62 [branch    ]         if progress_cb:
   63 [try_block ]             try:
   64 [code      ]                 progress_cb(stage, pct, msg)
   65 [try_block ]             except Exception:
   66 [code      ]                 pass
   67 [blank     ] 
   68 [code      ]     prog("init", 0.0, f"start project_id={project_id}")
   69 [code      ]     deps = _load_deps()
   70 [blank     ] 
   71 [comment   ]     # 1. HW mode
   72 [code      ]     hw_mode = "fallback_hw"
   73 [code      ]     hw_profile = {}
   74 [try_block ]     try:
   75 [branch    ]         if "hw" in deps:
   76 [code      ]             probe = None
   77 [loop      ]             for m in ("detect_hardware", "detect"):
   78 [branch    ]                 if hasattr(deps["hw"], m):
   79 [code      ]                     probe = getattr(deps["hw"], m)()
   80 [code      ]                     break
   81 [branch    ]             if isinstance(probe, dict):
   82 [code      ]                 hw_profile = probe
   83 [branch    ]                 if (
   84 [code      ]                     probe.get("mode") in ("full", "full_hw", "cuda", "directml")
   85 [code      ]                     or probe.get("vram_gb", 0) >= 10
   86 [code      ]                 ):
   87 [code      ]                     hw_mode = "full_hw"
   88 [try_block ]     except Exception as e:
   89 [code      ]         warnings.append(f"hw detect failed: {e}")
   90 [code      ]     prog("hw", 0.03, f"mode={hw_mode}")
   91 [blank     ] 
   92 [comment   ]     # 2. KPI session
   93 [code      ]     kpi_session = None
   94 [branch    ]     if "kpi" in deps:
   95 [code      ]         kpi_session = deps["kpi"].KpiSession(project_id=project_id, hw_mode=hw_mode)
   96 [blank     ] 
   97 [comment   ]     # 3. Expert config
   98 [code      ]     expert_flat = {"expert_mode_enabled": False}
   99 [branch    ]     if expert_config and "expert" in deps:
  100 [try_block ]         try:
  101 [code      ]             cfg = deps["expert"].ExpertConfig.from_dict(expert_config)
  102 [code      ]             v = deps["expert"].validate(cfg)
  103 [branch    ]             if v["errors"]:
  104 [code      ]                 warnings.extend([f"expert.{e}" for e in v["errors"]])
  105 [code      ]                 cfg.enabled = False
  106 [code      ]             expert_flat = cfg.to_flat_dict()
  107 [code      ]             wizard_state = deps["expert"].merge_with_wizard_state(wizard_state, cfg)
  108 [try_block ]         except Exception as e:
  109 [code      ]             warnings.append(f"expert_config bad: {e}")
  110 [blank     ] 
  111 [comment   ]     # 4. v10 pipeline (delegated)
  112 [code      ]     v10_out = {}
  113 [code      ]     release_dir = str(root / "output" / "releases" / project_id)
  114 [code      ]     os.makedirs(release_dir, exist_ok=True)
  115 [code      ]     st = kpi_session.start_stage("v10_pipeline") if kpi_session else None
  116 [try_block ]     try:
  117 [branch    ]         if "v10_patch" in deps and hasattr(deps["v10_patch"], "full_v10_pipeline"):
  118 [code      ]             prog("v10_pipeline", 0.15, "delegating to v10")
  119 [try_block ]             try:
  120 [code      ]                 v10_out = (
  121 [code      ]                     deps["v10_patch"].full_v10_pipeline(
  122 [code      ]                         project_id=project_id,
  123 [code      ]                         wizard_state=wizard_state,
  124 [code      ]                         release_dir=release_dir,
  125 [code      ]                     )
  126 [code      ]                     or {}
  127 [code      ]                 )
  128 [try_block ]             except TypeError:
  129 [try_block ]                 try:
  130 [code      ]                     v10_out = (
  131 [code      ]                         deps["v10_patch"].full_v10_pipeline(project_id, wizard_state)
  132 [code      ]                         or {}
  133 [code      ]                     )
  134 [try_block ]                 except Exception as e2:
  135 [code      ]                     warnings.append(f"v10 old sig failed: {e2}")
  136 [code      ]                     v10_out = _minimal_pipeline_fallback(
  137 [code      ]                         project_id, wizard_state, release_dir, prog
  138 [code      ]                     )
  139 [branch    ]         else:
  140 [code      ]             v10_out = _minimal_pipeline_fallback(
  141 [code      ]                 project_id, wizard_state, release_dir, prog
  142 [code      ]             )
  143 [code      ]         stages_ran.append("v10_pipeline")
  144 [branch    ]         if st:
  145 [code      ]             kpi_session.end_stage(st, ok=True)
  146 [try_block ]     except Exception as e:
  147 [code      ]         errors.append(f"v10_pipeline: {e}\n{traceback.format_exc()}")
  148 [code      ]         v10_out = _minimal_pipeline_fallback(
  149 [code      ]             project_id, wizard_state, release_dir, prog
  150 [code      ]         )
  151 [branch    ]         if st:
  152 [code      ]             kpi_session.end_stage(st, ok=False, note=str(e))
  153 [code      ]     prog("v10_pipeline", 0.55, "done")
  154 [blank     ] 
  155 [comment   ]     # 5. Video edits
  156 [code      ]     video_edits = {}
  157 [branch    ]     if "video_edit" in deps:
  158 [code      ]         st = kpi_session.start_stage("video_edits") if kpi_session else None
  159 [try_block ]         try:
  160 [code      ]             master_wav = v10_out.get("master_wav") or os.path.join(
  161 [code      ]                 release_dir, "master.wav"
  162 [code      ]             )
  163 [code      ]             cover_png = v10_out.get("cover_png") or os.path.join(
  164 [code      ]                 release_dir, "cover.png"
  165 [code      ]             )
  166 [code      ]             lyrics_lrc = v10_out.get("lyrics_lrc") or os.path.join(
  167 [code      ]                 release_dir, "lyrics.lrc"
  168 [code      ]             )
  169 [code      ]             bpm = float(wizard_state.get("bpm", 140.0))
  170 [code      ]             title = str(wizard_state.get("track_title", project_id))
  171 [code      ]             artist = str(wizard_state.get("artist_name", "ZS"))
  172 [code      ]             video_edits = deps["video_edit"].build_release_edits(
  173 [code      ]                 master_wav=master_wav,
  174 [code      ]                 cover_png=cover_png if os.path.exists(cover_png) else None,
  175 [code      ]                 lyrics_lrc=lyrics_lrc if os.path.exists(lyrics_lrc) else None,
  176 [code      ]                 bpm=bpm,
  177 [code      ]                 title=title,
  178 [code      ]                 artist=artist,
  179 [code      ]                 out_dir=release_dir,
  180 [code      ]             )
  181 [code      ]             stages_ran.append("video_edits")
  182 [branch    ]             if st:
  183 [code      ]                 kpi_session.end_stage(st, ok=True)
  184 [try_block ]         except Exception as e:
  185 [code      ]             errors.append(f"video_edits: {e}")
  186 [branch    ]             if st:
  187 [code      ]                 kpi_session.end_stage(st, ok=False, note=str(e))
  188 [code      ]     prog("video_edits", 0.75, f"{len(video_edits)} clips")
  189 [blank     ] 
  190 [comment   ]     # 6. Distribution packages
  191 [code      ]     distribution = {}
  192 [branch    ]     if "dist" in deps:
  193 [code      ]         st = kpi_session.start_stage("distribution") if kpi_session else None
  194 [try_block ]         try:
  195 [code      ]             meta = deps["dist"].TrackMetadata(
  196 [code      ]                 title=str(wizard_state.get("track_title", project_id)),
  197 [code      ]                 artist=str(wizard_state.get("artist_name", "ZS")),
  198 [code      ]                 bpm=float(wizard_state.get("bpm", 140.0)),
  199 [code      ]                 duration_sec=float(
  200 [code      ]                     v10_out.get("duration_sec", wizard_state.get("length_sec", 150.0))
  201 [code      ]                 ),
  202 [code      ]                 language=str(wizard_state.get("language", "ru")),
  203 [code      ]                 tags=list(wizard_state.get("tags", ["car", "summer", "trap"])),
  204 [code      ]                 lyrics_ru=str(v10_out.get("lyrics_ru", "")),
  205 [code      ]                 lyrics_en_hook=str(v10_out.get("lyrics_en_hook", "")),
  206 [code      ]                 genre=str(wizard_state.get("genre", "Hip-Hop/Rap")),
  207 [code      ]                 subgenre=str(wizard_state.get("subgenre", "Phonk / Trap / Hyperpop")),
  208 [code      ]                 key=str(wizard_state.get("key", "")),
  209 [code      ]                 explicit=bool(wizard_state.get("explicit", False)),
  210 [code      ]             )
  211 [code      ]             files = deps["dist"].ReleaseFiles(
  212 [code      ]                 master_wav=v10_out.get(
  213 [code      ]                     "master_wav", os.path.join(release_dir, "master.wav")
  214 [code      ]                 ),
  215 [code      ]                 mp3_320=v10_out.get("mp3_320", os.path.join(release_dir, "master.mp3")),
  216 [code      ]                 flac=v10_out.get("flac", os.path.join(release_dir, "master.flac")),
  217 [code      ]                 instrumental_wav=v10_out.get(
  218 [code      ]                     "instrumental", os.path.join(release_dir, "instrumental.wav")
  219 [code      ]                 ),
  220 [code      ]                 acapella_wav=v10_out.get(
  221 [code      ]                     "acapella", os.path.join(release_dir, "acapella.wav")
  222 [code      ]                 ),
  223 [code      ]                 stems_dir=v10_out.get("stems_dir", os.path.join(release_dir, "stems")),
  224 [code      ]                 tiktok_mp4=os.path.join(release_dir, "tiktok_edit.mp4"),
  225 [code      ]                 reels_mp4=os.path.join(release_dir, "reels_edit.mp4"),
  226 [code      ]                 shorts_mp4=os.path.join(release_dir, "shorts_edit.mp4"),
  227 [code      ]                 cover_png=v10_out.get(
  228 [code      ]                     "cover_png", os.path.join(release_dir, "cover.png")
  229 [code      ]                 ),
  230 [code      ]                 lyrics_txt=v10_out.get(
  231 [code      ]                     "lyrics_txt", os.path.join(release_dir, "lyrics.txt")
  232 [code      ]                 ),
  233 [code      ]                 lyrics_lrc=v10_out.get(
  234 [code      ]                     "lyrics_lrc", os.path.join(release_dir, "lyrics.lrc")
  235 [code      ]                 ),
  236 [code      ]             )
  237 [code      ]             distribution = deps["dist"].build_all_distribution_packages(
  238 [code      ]                 meta, files, out_dir=os.path.join(release_dir, "distribution")
  239 [code      ]             )
  240 [code      ]             stages_ran.append("distribution")
  241 [branch    ]             if st:
  242 [code      ]                 kpi_session.end_stage(st, ok=True)
  243 [try_block ]         except Exception as e:
  244 [code      ]             errors.append(f"distribution: {e}")
  245 [branch    ]             if st:
  246 [code      ]                 kpi_session.end_stage(st, ok=False, note=str(e))
  247 [code      ]     prog("distribution", 0.9, f"{len(distribution)} platforms")
  248 [blank     ] 
  249 [comment   ]     # 7. KPI finalize
  250 [code      ]     kpi_report = None
  251 [code      ]     kpi_md = ""
  252 [branch    ]     if kpi_session and "kpi" in deps:
  253 [try_block ]         try:
  254 [code      ]             ai_report = (
  255 [code      ]                 v10_out.get("ai_detector_report") or v10_out.get("auto_qa_report") or {}
  256 [code      ]             )
  257 [code      ]             kpi_session = deps["kpi"].finalize_session(
  258 [code      ]                 kpi_session,
  259 [code      ]                 release_dir=release_dir,
  260 [code      ]                 ai_detector_report=ai_report,
  261 [code      ]                 save_dir=str(root / "data"),
  262 [code      ]             )
  263 [code      ]             kpi_report = kpi_session.to_dict()
  264 [code      ]             kpi_md = deps["kpi"].render_kpi_report_md(kpi_session)
  265 [stmt      ]             with open(
  266 [code      ]                 os.path.join(release_dir, "KPI_REPORT_v11.md"), "w", encoding="utf-8"
  267 [code      ]             ) as f:
  268 [code      ]                 f.write(kpi_md)
  269 [code      ]             stages_ran.append("kpi")
  270 [try_block ]         except Exception as e:
  271 [code      ]             errors.append(f"kpi_finalize: {e}")
  272 [blank     ] 
  273 [comment   ]     # 8. Master manifest
  274 [code      ]     manifest_path = os.path.join(release_dir, "manifest_v11.json")
  275 [code      ]     manifest = {
  276 [code      ]         "project_id": project_id,
  277 [code      ]         "generator": "ZS Music Maker v11",
  278 [code      ]         "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
  279 [code      ]         "wizard_state": wizard_state,
  280 [code      ]         "expert_flat": expert_flat,
  281 [code      ]         "hw_mode": hw_mode,
  282 [code      ]         "hw_profile": hw_profile,
  283 [code      ]         "v10_out_summary": {
  284 [code      ]             k: (v if isinstance(v, (str, int, float, bool)) else str(type(v).__name__))
  285 [loop      ]             for k, v in (v10_out or {}).items()
  286 [code      ]         },
  287 [code      ]         "video_edits": video_edits,
  288 [code      ]         "distribution_dirs": {
  289 [code      ]             k: v.get("dir") for k, v in distribution.items() if isinstance(v, dict)
  290 [code      ]         },
  291 [code      ]         "kpi_verdict": kpi_report.get("verdict") if kpi_report else "N/A",
  292 [code      ]         "stages_ran": stages_ran,
  293 [code      ]         "errors": errors,
  294 [code      ]         "warnings": warnings,
  295 [code      ]         "total_seconds": time.time() - t0,
  296 [code      ]     }
  297 [try_block ]     try:
  298 [stmt      ]         with open(manifest_path, "w", encoding="utf-8") as f:
  299 [code      ]             json.dump(manifest, f, ensure_ascii=False, indent=2, default=str)
  300 [try_block ]     except Exception as e:
  301 [code      ]         errors.append(f"manifest_write: {e}")
  302 [blank     ] 
  303 [code      ]     prog(
  304 [code      ]         "done",
  305 [code      ]         1.0,
  306 [code      ]         f"total={manifest['total_seconds']:.1f}s " f"verdict={manifest['kpi_verdict']}",
  307 [code      ]     )
  308 [blank     ] 
  309 [return    ]     return {
  310 [code      ]         "ok": len(errors) == 0,
  311 [code      ]         "release_dir": release_dir,
  312 [code      ]         "manifest_path": manifest_path,
  313 [code      ]         "distribution": distribution,
  314 [code      ]         "video_edits": video_edits,
  315 [code      ]         "kpi": kpi_report,
  316 [code      ]         "kpi_md": kpi_md,
  317 [code      ]         "errors": errors,
  318 [code      ]         "warnings": warnings,
  319 [code      ]         "stages_ran": stages_ran,
  320 [code      ]         "total_seconds": time.time() - t0,
  321 [code      ]     }
  322 [blank     ] 
  323 [blank     ] 
  324 [def       ] def _minimal_pipeline_fallback(project_id, wizard_state, release_dir, prog):
  325 [docstring ]     """Плейсхолдеры чтобы v11 не крашился если v10 недоступен."""
  326 [code      ]     prog("fallback", 0.2, "v10 unavailable; placeholders")
  327 [code      ]     os.makedirs(release_dir, exist_ok=True)
  328 [import    ]     import struct
  329 [import    ]     import wave
  330 [blank     ] 
  331 [code      ]     p = os.path.join(release_dir, "master.wav")
  332 [branch    ]     if not os.path.exists(p):
  333 [try_block ]         try:
  334 [stmt      ]             with wave.open(p, "wb") as wf:
  335 [code      ]                 wf.setnchannels(1)
  336 [code      ]                 wf.setsampwidth(2)
  337 [code      ]                 wf.setframerate(44100)
  338 [code      ]                 wf.writeframes(struct.pack("<" + "h" * 44100, *([0] * 44100)))
  339 [try_block ]         except Exception:
  340 [code      ]             pass
  341 [code      ]     lp = os.path.join(release_dir, "lyrics.txt")
  342 [branch    ]     if not os.path.exists(lp):
  343 [stmt      ]         with open(lp, "w", encoding="utf-8") as f:
  344 [code      ]             f.write(str(wizard_state.get("lyrics_theme", "placeholder\n")))
  345 [return    ]     return {
  346 [code      ]         "master_wav": p,
  347 [code      ]         "mp3_320": p,
  348 [code      ]         "cover_png": "",
  349 [code      ]         "lyrics_txt": lp,
  350 [code      ]         "lyrics_lrc": "",
  351 [code      ]         "lyrics_ru": wizard_state.get("lyrics_theme", ""),
  352 [code      ]         "duration_sec": 1.0,
  353 [code      ]         "fallback": True,
  354 [code      ]     }
  355 [blank     ] 
  356 [blank     ] 
  357 [code      ] REGISTERED_MODULES_V11 = [
  358 [code      ]     "modules.video_edit_v11",
  359 [code      ]     "modules.distribution_export_v11",
  360 [code      ]     "modules.hit_kpi_monitor_v11",
  361 [code      ]     "modules.expert_mode_v11",
  362 [code      ] ]
  363 [blank     ] 
  364 [blank     ] 
  365 [def       ] def register(app_ctx=None):
  366 [code      ]     ok = {}
  367 [loop      ]     for m in REGISTERED_MODULES_V11:
  368 [try_block ]         try:
  369 [code      ]             __import__(m)
  370 [code      ]             ok[m] = True
  371 [try_block ]         except Exception as e:
  372 [code      ]             ok[m] = str(e)
  373 [code      ]     _safe_print(f"[orch_v11] registered: {ok}")
  374 [return    ]     return ok
  375 [blank     ] 
  376 [blank     ] 
  377 [def       ] def _self_test():
  378 [import    ]     import tempfile
  379 [blank     ] 
  380 [stmt      ]     with tempfile.TemporaryDirectory() as tmp:
  381 [code      ]         ws = {
  382 [code      ]             "track_title": "Selftest",
  383 [code      ]             "artist_name": "ZS",
  384 [code      ]             "bpm": 140.0,
  385 [code      ]             "length_sec": 90,
  386 [code      ]             "tags": ["test"],
  387 [code      ]         }
  388 [code      ]         res = run_full_pipeline_v11(
  389 [code      ]             project_id="selftest_v11",
  390 [code      ]             wizard_state=ws,
  391 [code      ]             expert_config=None,
  392 [code      ]             progress_cb=None,
  393 [code      ]             project_root=tmp,
  394 [code      ]         )
  395 [return    ]         return os.path.exists(res["release_dir"]) and os.path.exists(
  396 [code      ]             res["manifest_path"]
  397 [code      ]         )
  398 [blank     ] 
  399 [blank     ] 
  400 [branch    ] if __name__ == "__main__":
  401 [code      ]     print("orchestrator_v11_patch self-test:", "OK" if _self_test() else "FAIL")
```