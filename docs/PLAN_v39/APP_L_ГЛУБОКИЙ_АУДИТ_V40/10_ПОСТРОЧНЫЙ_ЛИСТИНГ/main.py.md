# ПОСТРОЧНЫЙ ЛИСТИНГ: `main.py`

**Всего строк:** 585

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 215 | 36.8 |
| blank | 92 | 15.7 |
| return | 58 | 9.9 |
| try_block | 55 | 9.4 |
| branch | 47 | 8.0 |
| import | 37 | 6.3 |
| docstring | 32 | 5.5 |
| def | 21 | 3.6 |
| comment | 18 | 3.1 |
| loop | 6 | 1.0 |
| raise | 3 | 0.5 |
| class | 1 | 0.2 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker — main.py (единая точка входа, консолидированная)
    3 [docstring ] ====================================================================
    4 [blank     ] 
    5 [docstring ] v22 changes:
    6 [docstring ]   — generate-from-scratch: refs=[] теперь НЕ fallback (default genre-style);
    7 [docstring ]   — structured synth_beat fallback (не 8с sine-каша);
    8 [docstring ]   — formant vocal scaffold v22 (гласные/интонация/паузы);
    9 [docstring ]   — жанровый пул fallback-лирикс;
   10 [docstring ]   — lazy mkdir в 21 модуле (нет side-effect при импорте).
   11 [blank     ] 
   12 [docstring ] v17 fixes (сохранены):
   13 [docstring ]   — VERSION / BUILD читаются из version.json;
   14 [docstring ]   — консольная кодировка без инверсии;
   15 [docstring ]   — CLI-режимы: --smoke, --dry-run, --dashboard, --self-diag,
   16 [docstring ]                 --e2e, --onboarding, --health, --readiness, --console,
   17 [docstring ]                 --version.
   18 [docstring ] """
   19 [blank     ] 
   20 [import    ] from __future__ import annotations
   21 [blank     ] 
   22 [import    ] import io
   23 [import    ] import json
   24 [import    ] import os
   25 [import    ] import sys
   26 [import    ] import traceback
   27 [import    ] import argparse
   28 [import    ] from pathlib import Path
   29 [blank     ] 
   30 [code      ] ROOT = Path(__file__).resolve().parent
   31 [code      ] sys.path.insert(0, str(ROOT))
   32 [blank     ] 
   33 [blank     ] 
   34 [def       ] def _load_version_info():
   35 [code      ]     default_v = "17.0.0"
   36 [code      ]     default_b = "v17-consolidated"
   37 [try_block ]     try:
   38 [code      ]         vp = ROOT / "version.json"
   39 [branch    ]         if vp.exists():
   40 [code      ]             data = json.loads(vp.read_text(encoding="utf-8"))
   41 [return    ]             return (
   42 [code      ]                 str(data.get("version", default_v)),
   43 [code      ]                 str(data.get("build", default_b)),
   44 [code      ]             )
   45 [try_block ]     except Exception:
   46 [code      ]         pass
   47 [return    ]     return default_v, default_b
   48 [blank     ] 
   49 [blank     ] 
   50 [class     ] class ProjectContext:
   51 [def       ]     def __init__(self):
   52 [code      ]         v, b = _load_version_info()
   53 [code      ]         self.version = v
   54 [code      ]         self.build = b
   55 [code      ]         self.status = "GOD MODE 3.0 (Autonomy & Stability)"
   56 [blank     ] 
   57 [code      ] ctx = ProjectContext()
   58 [blank     ] 
   59 [comment   ] # AUDIT-FIX P0: VERSION/BUILD использовались в _try_launch_gui_pyside (строка
   60 [comment   ] # с setWindowTitle) и в _cli_version, но НИГДЕ не были определены как
   61 [comment   ] # module-level имена — это давало NameError и краш `main.py --version` и
   62 [comment   ] # запуска Desktop GUI. Определяем их из единственного источника правды
   63 [comment   ] # (version.json), как и задумано в docstring v17.
   64 [code      ] VERSION = ctx.version
   65 [code      ] BUILD = ctx.build
   66 [blank     ] 
   67 [blank     ] 
   68 [def       ] def _setup_console_encoding() -> None:
   69 [docstring ]     """
   70 [docstring ]     v17 FIX: раньше логика была инвертирована — если stdout УЖЕ был UTF-8,
   71 [docstring ]     его насильно оборачивали в cp866 и в Windows Terminal / PowerShell 7
   72 [docstring ]     сыпались кракозябры. Теперь UTF-8 не трогаем, cp866 только как
   73 [docstring ]     последний шанс.
   74 [docstring ]     """
   75 [try_block ]     try:
   76 [code      ]         os.environ.setdefault("PYTHONIOENCODING", "utf-8")
   77 [code      ]         enc = (getattr(sys.stdout, "encoding", "") or "").lower()
   78 [branch    ]         if enc in ("utf-8", "utf8", "cp65001"):
   79 [return    ]             return
   80 [try_block ]         try:
   81 [branch    ]             if hasattr(sys.stdout, "reconfigure"):
   82 [code      ]                 sys.stdout.reconfigure(encoding="utf-8", errors="replace")
   83 [code      ]                 sys.stderr.reconfigure(encoding="utf-8", errors="replace")
   84 [return    ]                 return
   85 [try_block ]         except Exception:
   86 [code      ]             pass
   87 [try_block ]         try:
   88 [code      ]             sys.stdout = io.TextIOWrapper(
   89 [code      ]                 sys.stdout.buffer,
   90 [code      ]                 encoding="utf-8",
   91 [code      ]                 errors="replace",
   92 [code      ]                 line_buffering=True,
   93 [code      ]             )
   94 [code      ]             sys.stderr = io.TextIOWrapper(
   95 [code      ]                 sys.stderr.buffer,
   96 [code      ]                 encoding="utf-8",
   97 [code      ]                 errors="replace",
   98 [code      ]                 line_buffering=True,
   99 [code      ]             )
  100 [try_block ]         except Exception:
  101 [try_block ]             try:
  102 [code      ]                 sys.stdout = io.TextIOWrapper(
  103 [code      ]                     sys.stdout.buffer,
  104 [code      ]                     encoding="cp866",
  105 [code      ]                     errors="replace",
  106 [code      ]                     line_buffering=True,
  107 [code      ]                 )
  108 [code      ]                 sys.stderr = io.TextIOWrapper(
  109 [code      ]                     sys.stderr.buffer,
  110 [code      ]                     encoding="cp866",
  111 [code      ]                     errors="replace",
  112 [code      ]                     line_buffering=True,
  113 [code      ]                 )
  114 [try_block ]             except Exception:
  115 [code      ]                 pass
  116 [try_block ]     except Exception:
  117 [code      ]         pass
  118 [blank     ] 
  119 [blank     ] 
  120 [def       ] def _safe_print(msg: str) -> None:
  121 [try_block ]     try:
  122 [code      ]         print(msg)
  123 [try_block ]     except UnicodeEncodeError:
  124 [try_block ]         try:
  125 [code      ]             sys.stdout.buffer.write((msg + "\n").encode("utf-8", "replace"))
  126 [try_block ]         except Exception:
  127 [code      ]             pass
  128 [blank     ] 
  129 [blank     ] 
  130 [def       ] def _header() -> None:
  131 [code      ]     _safe_print("=" * 64)
  132 [code      ]     _safe_print(f"ZS Music Maker v{ctx.version} — main.py (unified)")
  133 [code      ]     _safe_print(f"Build: {ctx.build}")
  134 [code      ]     _safe_print(f"Status: {ctx.status}")
  135 [code      ]     _safe_print("=" * 64)
  136 [blank     ] 
  137 [blank     ] 
  138 [def       ] def _health_snapshot() -> dict:
  139 [try_block ]     try:
  140 [import    ]         from modules import health_v12
  141 [blank     ] 
  142 [code      ]         rep = health_v12.collect()
  143 [code      ]         _safe_print(
  144 [code      ]             f"[main] health: {rep.verdict}  "
  145 [code      ]             f"ready={rep.percent_ready}%  "
  146 [code      ]             f"core_ok={rep.core_ok}"
  147 [code      ]         )
  148 [return    ]         return {"verdict": rep.verdict, "percent": rep.percent_ready}
  149 [try_block ]     except Exception as e:
  150 [code      ]         _safe_print(f"[main] health_v12 not available: {e}")
  151 [return    ]         return {"verdict": "UNKNOWN", "percent": 0}
  152 [blank     ] 
  153 [blank     ] 
  154 [def       ] def _try_launch_gui_pyside() -> bool:
  155 [try_block ]     try:
  156 [import    ]         from PySide6.QtWidgets import QApplication
  157 [try_block ]     except Exception as e:
  158 [code      ]         _safe_print(f"[ERROR] PySide6 не найден. Для работы GUI установите: pip install PySide6. Ошибка: {e}")
  159 [return    ]         return False
  160 [try_block ]     try:
  161 [import    ]         from app.gui import theme_v12
  162 [import    ]         from app.gui.wizard import Wizard
  163 [import    ]         from app.hw_probe import probe
  164 [import    ]         from app.logger import setup_logger
  165 [import    ]         from app.runtime_orchestrator import RuntimeOrchestrator
  166 [try_block ]     except Exception as e:
  167 [code      ]         _safe_print(f"[ERROR] Не удалось загрузить модули GUI. Проверьте целостность папки app/gui. Ошибка: {e}")
  168 [code      ]         traceback.print_exc()
  169 [return    ]         return False
  170 [code      ]     app = QApplication.instance() or QApplication(sys.argv)
  171 [try_block ]     try:
  172 [code      ]         theme_v12.apply(app)
  173 [try_block ]     except Exception:
  174 [code      ]         pass
  175 [try_block ]     try:
  176 [code      ]         log = setup_logger("zsmm")
  177 [code      ]         hw = probe()
  178 [code      ]         orch = RuntimeOrchestrator(log=log)
  179 [code      ]         w = Wizard(orch=orch, hw=hw, log=log)
  180 [code      ]         w.setWindowTitle(f"ZS Music Maker v{VERSION} — Desktop Wizard")
  181 [code      ]         w.show()
  182 [code      ]         rc = app.exec()
  183 [raise     ]         raise SystemExit(rc)
  184 [try_block ]     except SystemExit:
  185 [raise     ]         raise
  186 [try_block ]     except Exception:
  187 [code      ]         traceback.print_exc()
  188 [return    ]         return False
  189 [blank     ] 
  190 [blank     ] 
  191 [def       ] def _try_launch_gui_gradio() -> bool:
  192 [try_block ]     try:
  193 [import    ]         import gradio  # noqa: F401
  194 [try_block ]     except Exception as e:
  195 [code      ]         _safe_print(f"[main] gradio недоступен: {e}")
  196 [return    ]         return False
  197 [try_block ]     try:
  198 [import    ]         from app.core.orchestrator import build_gradio_ui
  199 [blank     ] 
  200 [code      ]         demo = build_gradio_ui()
  201 [code      ]         demo.launch(
  202 [code      ]             server_name="127.0.0.1", server_port=7860, share=False, show_error=True
  203 [code      ]         )
  204 [return    ]         return True
  205 [try_block ]     except Exception as e:
  206 [code      ]         _safe_print(f"[main] gradio UI failed: {e}")
  207 [code      ]         traceback.print_exc()
  208 [return    ]         return False
  209 [blank     ] 
  210 [blank     ] 
  211 [code      ] LEGACY_PATCH_MODULES = (
  212 [code      ]     "orchestrator_v12_patch",
  213 [code      ]     "orchestrator_v11_patch",
  214 [code      ]     "orchestrator_v10_patch",
  215 [code      ]     "orchestrator_v9_patch",
  216 [code      ]     "orchestrator_v8_patch",
  217 [code      ] )
  218 [blank     ] 
  219 [blank     ] 
  220 [def       ] def _register_patches(enabled: bool = True) -> dict[str, object]:
  221 [docstring ]     """Загрузить изолированный legacy-слой v8–v12 только по умолчанию.
  222 [blank     ] 
  223 [docstring ]     Новые пути должны опираться на единый core-оркестратор. Флаг
  224 [docstring ]     ``--legacy-off`` оставляет старые патчи в репозитории для совместимости с
  225 [docstring ]     Wizard, но не импортирует и не регистрирует их в текущем процессе.
  226 [docstring ]     """
  227 [code      ]     report: dict[str, object] = {"enabled": enabled, "loaded": [], "skipped": []}
  228 [branch    ]     if not enabled:
  229 [code      ]         report["skipped"] = list(LEGACY_PATCH_MODULES)
  230 [code      ]         _safe_print("[main] LEGACY patches disabled (--legacy-off).")
  231 [return    ]         return report
  232 [blank     ] 
  233 [loop      ]     for module_name in LEGACY_PATCH_MODULES:
  234 [try_block ]         try:
  235 [code      ]             module = __import__(f"app.core.{module_name}", fromlist=[module_name])
  236 [code      ]             register = getattr(module, "register", None)
  237 [branch    ]             if callable(register):
  238 [code      ]                 register()
  239 [code      ]                 report["loaded"].append(module_name)
  240 [branch    ]             else:
  241 [code      ]                 report["skipped"].append(module_name)
  242 [try_block ]         except Exception as exc:
  243 [code      ]             report["skipped"].append(module_name)
  244 [code      ]             _safe_print(f"[main] LEGACY patch {module_name} unavailable: {exc}")
  245 [return    ]     return report
  246 [blank     ] 
  247 [blank     ] 
  248 [def       ] def _cli_smoke() -> int:
  249 [docstring ]     """Runs the current smoke suite: v29 (God Mode E2E) → v26 (audio quality).
  250 [blank     ] 
  251 [docstring ]     v36 FIX: старая цепочка тянула smoke_v14/v15/v17/v21/v24/v25 — все они
  252 [docstring ]     перенесены в docs/legacy/ ещё в v29 и по этим путям НЕ импортируются.
  253 [docstring ]     Каждый вызов --smoke бесполезно печатал 6 строк «failed: No module named».
  254 [docstring ]     Оставлены ТОЛЬКО реально работающие v29 → v26."""
  255 [loop      ]     for name in ("tools.smoke_v29", "tools.smoke_v26"):
  256 [try_block ]         try:
  257 [code      ]             mod = __import__(name, fromlist=["main"])
  258 [return    ]             return int(mod.main() or 0)
  259 [try_block ]         except Exception as e:
  260 [code      ]             _safe_print(f"[main --smoke] {name} failed: {e}")
  261 [blank     ] 
  262 [code      ]     _safe_print("[main --smoke] No valid smoke tests found.")
  263 [return    ]     return 2
  264 [blank     ] 
  265 [blank     ] 
  266 [def       ] def _cli_dry_run() -> int:
  267 [try_block ]     try:
  268 [import    ]         from app.core.orchestrator import run_full_pipeline
  269 [blank     ] 
  270 [code      ]         out = run_full_pipeline("cli", {}, dry_run=True)
  271 [code      ]         _safe_print(
  272 [code      ]             f"verdict={out.get('verdict')}  " f"duration={out.get('duration_sec')}s"
  273 [code      ]         )
  274 [return    ]         return 0 if str(out.get("verdict", "")).endswith("PASS") else 1
  275 [try_block ]     except Exception as e:
  276 [code      ]         _safe_print(f"[main --dry-run] failed: {e}")
  277 [return    ]         return 2
  278 [blank     ] 
  279 [blank     ] 
  280 [def       ] def _cli_dashboard() -> int:
  281 [try_block ]     try:
  282 [import    ]         from modules import kpi_dashboard_v12
  283 [blank     ] 
  284 [return    ]         return int(kpi_dashboard_v12.main() or 0)
  285 [try_block ]     except Exception as e:
  286 [code      ]         _safe_print(f"[main --dashboard] failed: {e}")
  287 [return    ]         return 2
  288 [blank     ] 
  289 [blank     ] 
  290 [def       ] def _cli_self_diag() -> int:
  291 [try_block ]     try:
  292 [import    ]         from modules import self_diag_v13
  293 [blank     ] 
  294 [return    ]         return int(self_diag_v13.main_entry() or 0)
  295 [try_block ]     except Exception as e:
  296 [code      ]         _safe_print(f"[main --self-diag] failed: {e}")
  297 [return    ]         return 2
  298 [blank     ] 
  299 [blank     ] 
  300 [def       ] def _cli_e2e() -> int:
  301 [try_block ]     try:
  302 [import    ]         from tools import real_e2e_v14
  303 [blank     ] 
  304 [return    ]         return int(real_e2e_v14.main() or 0)
  305 [try_block ]     except Exception as e:
  306 [code      ]         _safe_print(f"[main --e2e] tools/real_e2e_v14 failed: {e}")
  307 [return    ]         return 2
  308 [blank     ] 
  309 [blank     ] 
  310 [def       ] def _cli_onboarding() -> int:
  311 [try_block ]     try:
  312 [import    ]         from modules import voice_onboarding
  313 [blank     ] 
  314 [code      ]         rc = voice_onboarding.run_cli()
  315 [return    ]         return int(rc or 0)
  316 [try_block ]     except Exception as e:
  317 [code      ]         _safe_print(f"[main --onboarding] failed: {e}")
  318 [return    ]         return 2
  319 [blank     ] 
  320 [blank     ] 
  321 [def       ] def _cli_health() -> int:
  322 [code      ]     snap = _health_snapshot()
  323 [return    ]     return 0 if snap.get("verdict") in ("GREEN", "YELLOW") else 1
  324 [blank     ] 
  325 [blank     ] 
  326 [def       ] def _cli_readiness() -> int:
  327 [try_block ]     try:
  328 [import    ]         from tools import readiness
  329 [blank     ] 
  330 [code      ]         pct, blocks = readiness.compute()
  331 [code      ]         _safe_print(
  332 [code      ]             json.dumps({"percent": pct, "blocks": blocks}, ensure_ascii=False, indent=2)
  333 [code      ]         )
  334 [return    ]         return 0
  335 [try_block ]     except Exception as e:
  336 [code      ]         _safe_print(f"[main --readiness] failed: {e}")
  337 [return    ]         return 2
  338 [blank     ] 
  339 [blank     ] 
  340 [def       ] def _cli_version() -> int:
  341 [try_block ]     try:
  342 [import    ]         from config.settings import get_settings
  343 [code      ]         cfg = get_settings()
  344 [code      ]         cfg_path = str(cfg.config_path)
  345 [try_block ]     except Exception as _ce:  # noqa: BLE001 — конфиг опционален
  346 [code      ]         cfg_path = "unavailable"
  347 [code      ]     _safe_print(json.dumps({"version": VERSION, "build": BUILD, "config": cfg_path}, ensure_ascii=False))
  348 [return    ]     return 0
  349 [blank     ] 
  350 [blank     ] 
  351 [def       ] def _cli_god(args) -> int:
  352 [try_block ]     try:
  353 [import    ]         from app.core.orchestrator_god import run_god_pipeline
  354 [blank     ] 
  355 [code      ]         genre = getattr(args, "genre", "drift_phonk")
  356 [code      ]         theme = getattr(args, "theme", genre)
  357 [blank     ] 
  358 [comment   ]         # v34 FIX (SESSION_LOG v32.22): раньше несуществующий жанр падал
  359 [comment   ]         # глубоко внутри пайплайна с непонятным KeyError. Теперь валидация
  360 [comment   ]         # против StyleRegistry на входе + подсказка ближайших вариантов.
  361 [try_block ]         try:
  362 [import    ]             from modules.genre_engine import StyleRegistry
  363 [code      ]             known = set(StyleRegistry().list_genres())
  364 [branch    ]             if genre not in known:
  365 [import    ]                 import difflib
  366 [code      ]                 hint = difflib.get_close_matches(genre, sorted(known), n=3, cutoff=0.5)
  367 [code      ]                 _safe_print(f"[main --god] unknown genre: {genre!r}")
  368 [branch    ]                 if hint:
  369 [code      ]                     _safe_print(f"  did you mean: {', '.join(hint)}?")
  370 [code      ]                 _safe_print("  full list: python main.py --list-genres")
  371 [return    ]                 return 2
  372 [try_block ]         except ImportError:
  373 [code      ]             pass  # движок жанров недоступен — пусть пайплайн сам решит
  374 [blank     ] 
  375 [code      ]         _safe_print(f"[main --god] Launching GOD MODE pipeline (genre={genre}, theme={theme})...")
  376 [code      ]         out = run_god_pipeline("god_cli", {"theme": theme, "genre": genre})
  377 [code      ]         _safe_print(
  378 [code      ]             f"GOD MODE COMPLETED: elapsed={out.get('elapsed_sec')}s master={out.get('master_path')}"
  379 [code      ]         )
  380 [return    ]         return 0
  381 [try_block ]     except Exception as e:
  382 [code      ]         _safe_print(f"[main --god] failed: {e}")
  383 [code      ]         traceback.print_exc()
  384 [return    ]         return 2
  385 [blank     ] 
  386 [blank     ] 
  387 [def       ] def _cli_console() -> int:
  388 [code      ]     _safe_print("[main --console] запущен без GUI. Команды:")
  389 [code      ]     _safe_print("  smoke | e2e | diag | health | readiness | dry | version | exit")
  390 [loop      ]     while True:
  391 [try_block ]         try:
  392 [code      ]             cmd = input("zsmm> ").strip().lower()
  393 [try_block ]         except (EOFError, KeyboardInterrupt):
  394 [return    ]             return 0
  395 [branch    ]         if cmd in ("exit", "quit", "q"):
  396 [return    ]             return 0
  397 [branch    ]         elif cmd == "smoke":
  398 [code      ]             _cli_smoke()
  399 [branch    ]         elif cmd == "e2e":
  400 [code      ]             _cli_e2e()
  401 [branch    ]         elif cmd == "diag":
  402 [code      ]             _cli_self_diag()
  403 [branch    ]         elif cmd == "health":
  404 [code      ]             _cli_health()
  405 [branch    ]         elif cmd == "readiness":
  406 [code      ]             _cli_readiness()
  407 [branch    ]         elif cmd == "dry":
  408 [code      ]             _cli_dry_run()
  409 [branch    ]         elif cmd == "version":
  410 [code      ]             _cli_version()
  411 [branch    ]         else:
  412 [code      ]             _safe_print(
  413 [code      ]                 "unknown; try: smoke|e2e|diag|health|readiness|dry|version|exit"
  414 [code      ]             )
  415 [blank     ] 
  416 [blank     ] 
  417 [def       ] def main() -> int:
  418 [code      ]     _setup_console_encoding()
  419 [code      ]     _header()
  420 [blank     ]     
  421 [code      ]     parser = argparse.ArgumentParser(description="ZS Music Maker — Professional AI Music Production Station")
  422 [code      ]     parser.add_argument("--god", action="store_true", help="Launch the ULTIMATE GOD MODE pipeline")
  423 [code      ]     parser.add_argument("--async-mode", action="store_true", help="Launch parallel async pipeline")
  424 [code      ]     parser.add_argument("--genre", type=str, default="drift_phonk", help="Target genre (100+ available)")
  425 [code      ]     parser.add_argument("--theme", type=str, default="drift_phonk", help="Target theme/mood")
  426 [code      ]     parser.add_argument("--list-genres", action="store_true", help="Show all 119+ available genres")
  427 [code      ]     parser.add_argument("--smoke", action="store_true", help="Run quality smoke tests")
  428 [code      ]     parser.add_argument("--self-diag", action="store_true", help="Run system self-diagnostics")
  429 [code      ]     parser.add_argument("--health", action="store_true", help="Check system health and GPU")
  430 [code      ]     parser.add_argument("--version", "-V", action="store_true", help="Show version info")
  431 [code      ]     parser.add_argument("--gradio", action="store_true", help="Launch Web UI (Gradio)")
  432 [code      ]     parser.add_argument("--desktop", action="store_true", help="Launch Desktop UI (PySide6)")
  433 [comment   ]     # AUDIT-FIX P0: нижеперечисленные режимы имели реализации (_cli_*),
  434 [comment   ]     # рекламировались в docstring модуля, но НЕ были подключены к argparse —
  435 [comment   ]     # `main.py --dry-run` и др. падали с "unrecognized arguments".
  436 [code      ]     parser.add_argument("--dry-run", action="store_true", help="Run pipeline in dry-run (no heavy deps)")
  437 [code      ]     parser.add_argument("--dashboard", action="store_true", help="Show KPI dashboard")
  438 [code      ]     parser.add_argument("--e2e", action="store_true", help="Run real end-to-end test")
  439 [code      ]     parser.add_argument("--onboarding", action="store_true", help="Run voice onboarding CLI")
  440 [code      ]     parser.add_argument("--readiness", action="store_true", help="Compute readiness percent")
  441 [code      ]     parser.add_argument("--console", action="store_true", help="Force console REPL mode (no GUI)")
  442 [code      ]     parser.add_argument(
  443 [code      ]         "--legacy-off",
  444 [code      ]         action="store_true",
  445 [code      ]         help="Skip legacy v8-v12 patch registration for runtime pipelines",
  446 [code      ]     )
  447 [code      ]     parser.add_argument("--ai", action="store_true", help="Launch AI GOD MODE 4.0 (sequential AI stack)")
  448 [code      ]     parser.add_argument("--ai-status", action="store_true", help="Show AI model registry & availability")
  449 [code      ]     parser.add_argument("--ai-pull", type=str, default="", help="Pull one AI model role (or 'all')")
  450 [code      ]     parser.add_argument("--dossier-artist", type=str, default="", help="Artist name/slug for dossier")
  451 [code      ]     parser.add_argument("--dossier-add", type=str, default="", help="Add local folder source")
  452 [code      ]     parser.add_argument("--dossier-build", action="store_true", help="Run full AI dossier build (heavy)")
  453 [blank     ] 
  454 [code      ]     args = parser.parse_args()
  455 [blank     ] 
  456 [branch    ]     if args.version:
  457 [return    ]         return _cli_version()
  458 [blank     ]     
  459 [branch    ]     if args.list_genres:
  460 [import    ]         from modules.genre_engine import StyleRegistry
  461 [code      ]         reg = StyleRegistry()
  462 [code      ]         print("\nAvailable Genres:")
  463 [loop      ]         for g in sorted(reg.list_genres()):
  464 [code      ]             print(f"  - {g}")
  465 [return    ]         return 0
  466 [blank     ] 
  467 [branch    ]     if args.smoke:
  468 [return    ]         return _cli_smoke()
  469 [blank     ]     
  470 [branch    ]     if args.self_diag:
  471 [return    ]         return _cli_self_diag()
  472 [blank     ]     
  473 [branch    ]     if args.health:
  474 [return    ]         return _cli_health()
  475 [blank     ] 
  476 [comment   ]     # Legacy v8..v12 сохранён для обратной совместимости, но его загрузка
  477 [comment   ]     # теперь управляется явно. Новый core-путь работает и без этих патчей.
  478 [code      ]     _register_patches(enabled=not args.legacy_off)
  479 [blank     ] 
  480 [branch    ]     if args.dry_run:
  481 [return    ]         return _cli_dry_run()
  482 [blank     ] 
  483 [branch    ]     if args.dashboard:
  484 [return    ]         return _cli_dashboard()
  485 [blank     ] 
  486 [branch    ]     if args.e2e:
  487 [return    ]         return _cli_e2e()
  488 [blank     ] 
  489 [branch    ]     if args.onboarding:
  490 [return    ]         return _cli_onboarding()
  491 [blank     ] 
  492 [branch    ]     if args.readiness:
  493 [return    ]         return _cli_readiness()
  494 [blank     ] 
  495 [branch    ]     if args.console:
  496 [return    ]         return _cli_console()
  497 [blank     ] 
  498 [branch    ]     if args.ai_status:
  499 [import    ]         from app.ai.registry import registry, MODEL_REGISTRY
  500 [code      ]         print("[AI] Hardware budget:", registry.hw)
  501 [loop      ]         for k, v in MODEL_REGISTRY.items():
  502 [code      ]             avail = "OK" if registry.is_available(k) else "--"
  503 [code      ]             print(f"  {avail} {k:20s} {v['engine']:22s} VRAM~{v.get('vram_est_gb', 0)} GB - {v['role']}")
  504 [return    ]         return 0
  505 [blank     ] 
  506 [branch    ]     if args.ai_pull:
  507 [import    ]         from tools import pull_ai_models as pm
  508 [branch    ]         if args.ai_pull.lower() == "all":
  509 [import    ]             from app.ai.registry import MODEL_REGISTRY
  510 [loop      ]             for k in MODEL_REGISTRY:
  511 [code      ]                 pm.pull(k)
  512 [branch    ]         else:
  513 [code      ]             pm.pull(args.ai_pull)
  514 [return    ]         return 0
  515 [blank     ] 
  516 [branch    ]     if args.dossier_add and args.dossier_artist:
  517 [import    ]         from modules.artist_dossier import DossierManager
  518 [import    ]         from modules.artist_dossier.collectors import LocalFolderCollector, LyricVaultCollector
  519 [code      ]         mgr = DossierManager()
  520 [code      ]         src = args.dossier_add
  521 [code      ]         tracks = []
  522 [branch    ]         if Path(src).is_dir():
  523 [code      ]             tracks = LocalFolderCollector(src).collect(args.dossier_artist)
  524 [code      ]         tracks += LyricVaultCollector(str(ROOT / "lyric_vault")).collect(args.dossier_artist)
  525 [code      ]         mgr.add_artist(args.dossier_artist, tracks=tracks)
  526 [code      ]         print(f"[dossier] artist={args.dossier_artist} tracks_added={len(tracks)}")
  527 [return    ]         return 0
  528 [blank     ] 
  529 [branch    ]     if args.dossier_build and args.dossier_artist:
  530 [import    ]         from modules.artist_dossier import DossierManager
  531 [code      ]         mgr = DossierManager()
  532 [code      ]         d = mgr.build_full_dossier(args.dossier_artist,
  533 [code      ]                                    progress_cb=lambda tid, st: print(f"  [{tid}] {st}"))
  534 [code      ]         print(json.dumps(d, ensure_ascii=False, indent=2)[:2000])
  535 [return    ]         return 0
  536 [blank     ] 
  537 [branch    ]     if args.ai:
  538 [import    ]         from app.core.orchestrator_ai import run_ai_pipeline
  539 [code      ]         ws = {"genre": args.genre, "theme": args.theme,
  540 [code      ]               "artist_slug": args.dossier_artist or None}
  541 [code      ]         out = run_ai_pipeline("ai_cli", ws, dry_run=False)
  542 [code      ]         print(json.dumps({"stages": out["report"]["stages"],
  543 [code      ]                           "artefacts": out["artefacts"]}, ensure_ascii=False, indent=2))
  544 [return    ]         return 0
  545 [blank     ] 
  546 [branch    ]     if args.god:
  547 [return    ]         return _cli_god(args)
  548 [blank     ]     
  549 [branch    ]     if args.async_mode:
  550 [comment   ]         # v33 FIX (P1, SESSION_LOG v32.9): раньше --async-mode ВСЕГДА
  551 [comment   ]         # возвращал 0, даже если пайплайн упал — exit code врал CI.
  552 [import    ]         import asyncio
  553 [import    ]         from app.core.orchestrator_async import AsyncOrchestrator
  554 [try_block ]         try:
  555 [code      ]             orch = AsyncOrchestrator("async_cli", ROOT / "output" / "async_cli")
  556 [code      ]             result = asyncio.run(orch.run_pipeline({"genre": args.genre}))
  557 [try_block ]         except Exception as e:
  558 [code      ]             print(f"[async-mode] PIPELINE FAILED: {e}")
  559 [return    ]             return 1
  560 [comment   ]         # Оркестратор может вернуть dict со статусом или None —
  561 [comment   ]         # считаем падением только явный status=failed/error.
  562 [branch    ]         if isinstance(result, dict):
  563 [code      ]             status = str(result.get("status", "")).lower()
  564 [branch    ]             if status in ("failed", "error"):
  565 [code      ]                 print(f"[async-mode] pipeline status={status}")
  566 [return    ]                 return 1
  567 [return    ]         return 0
  568 [blank     ] 
  569 [branch    ]     if args.gradio:
  570 [branch    ]         if _try_launch_gui_gradio(): return 0
  571 [return    ]         return 2
  572 [blank     ] 
  573 [branch    ]     if args.desktop:
  574 [branch    ]         if _try_launch_gui_pyside(): return 0
  575 [return    ]         return 2
  576 [blank     ] 
  577 [comment   ]     # Default behavior: try GUI, then console
  578 [code      ]     _health_snapshot()
  579 [branch    ]     if _try_launch_gui_pyside(): return 0
  580 [branch    ]     if _try_launch_gui_gradio(): return 0
  581 [return    ]     return _cli_console()
  582 [blank     ] 
  583 [blank     ] 
  584 [branch    ] if __name__ == "__main__":
  585 [raise     ]     raise SystemExit(main())
```