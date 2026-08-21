# grep-таблицы `main.py`

## `import` — 37 совпадений
```
   20 | from __future__ import annotations
   22 | import io
   23 | import json
   24 | import os
   25 | import sys
   26 | import traceback
   27 | import argparse
   28 | from pathlib import Path
  140 |         from modules import health_v12
  156 |         from PySide6.QtWidgets import QApplication
  161 |         from app.gui import theme_v12
  162 |         from app.gui.wizard import Wizard
  163 |         from app.hw_probe import probe
  164 |         from app.logger import setup_logger
  165 |         from app.runtime_orchestrator import RuntimeOrchestrator
  193 |         import gradio  # noqa: F401
  198 |         from app.core.orchestrator import build_gradio_ui
  268 |         from app.core.orchestrator import run_full_pipeline
  282 |         from modules import kpi_dashboard_v12
  292 |         from modules import self_diag_v13
  302 |         from tools import real_e2e_v14
  312 |         from modules import voice_onboarding
  328 |         from tools import readiness
  342 |         from config.settings import get_settings
  353 |         from app.core.orchestrator_god import run_god_pipeline
  362 |             from modules.genre_engine import StyleRegistry
  365 |                 import difflib
  460 |         from modules.genre_engine import StyleRegistry
  499 |         from app.ai.registry import registry, MODEL_REGISTRY
  507 |         from tools import pull_ai_models as pm
  509 |             from app.ai.registry import MODEL_REGISTRY
  517 |         from modules.artist_dossier import DossierManager
  518 |         from modules.artist_dossier.collectors import LocalFolderCollector, LyricVaultCollector
  530 |         from modules.artist_dossier import DossierManager
  538 |         from app.core.orchestrator_ai import run_ai_pipeline
  552 |         import asyncio
  553 |         from app.core.orchestrator_async import AsyncOrchestrator
```

## `print` — 11 совпадений
```
  122 |         print(msg)
  462 |         print("\nAvailable Genres:")
  464 |             print(f"  - {g}")
  500 |         print("[AI] Hardware budget:", registry.hw)
  503 |             print(f"  {avail} {k:20s} {v['engine']:22s} VRAM~{v.get('vram_est_gb', 0)} GB - {v['role']}")
  526 |         print(f"[dossier] artist={args.dossier_artist} tracks_added={len(tracks)}")
  533 |                                    progress_cb=lambda tid, st: print(f"  [{tid}] {st}"))
  534 |         print(json.dumps(d, ensure_ascii=False, indent=2)[:2000])
  542 |         print(json.dumps({"stages": out["report"]["stages"],
  558 |             print(f"[async-mode] PIPELINE FAILED: {e}")
  565 |                 print(f"[async-mode] pipeline status={status}")
```

## `except` — 28 совпадений
```
   45 |     except Exception:
   85 |         except Exception:
  100 |         except Exception:
  114 |             except Exception:
  116 |     except Exception:
  123 |     except UnicodeEncodeError:
  126 |         except Exception:
  149 |     except Exception as e:
  157 |     except Exception as e:
  166 |     except Exception as e:
  173 |     except Exception:
  184 |     except SystemExit:
  186 |     except Exception:
  194 |     except Exception as e:
  205 |     except Exception as e:
  242 |         except Exception as exc:
  259 |         except Exception as e:
  275 |     except Exception as e:
  285 |     except Exception as e:
  295 |     except Exception as e:
  305 |     except Exception as e:
  316 |     except Exception as e:
  335 |     except Exception as e:
  345 |     except Exception as _ce:  # noqa: BLE001 — конфиг опционален
  372 |         except ImportError:
  381 |     except Exception as e:
  393 |         except (EOFError, KeyboardInterrupt):
  557 |         except Exception as e:
```

## `try` — 27 совпадений
```
   37 |     try:
   75 |     try:
   80 |         try:
   87 |         try:
  101 |             try:
  121 |     try:
  124 |         try:
  139 |     try:
  155 |     try:
  160 |     try:
  171 |     try:
  175 |     try:
  192 |     try:
  197 |     try:
  234 |         try:
  256 |         try:
  267 |     try:
  281 |     try:
  291 |     try:
  301 |     try:
  311 |     try:
  327 |     try:
  341 |     try:
  352 |     try:
  361 |         try:
  391 |         try:
  554 |         try:
```

## `def` — 21 совпадений
```
   34 | def _load_version_info():
   51 |     def __init__(self):
   68 | def _setup_console_encoding() -> None:
  120 | def _safe_print(msg: str) -> None:
  130 | def _header() -> None:
  138 | def _health_snapshot() -> dict:
  154 | def _try_launch_gui_pyside() -> bool:
  191 | def _try_launch_gui_gradio() -> bool:
  220 | def _register_patches(enabled: bool = True) -> dict[str, object]:
  248 | def _cli_smoke() -> int:
  266 | def _cli_dry_run() -> int:
  280 | def _cli_dashboard() -> int:
  290 | def _cli_self_diag() -> int:
  300 | def _cli_e2e() -> int:
  310 | def _cli_onboarding() -> int:
  321 | def _cli_health() -> int:
  326 | def _cli_readiness() -> int:
  340 | def _cli_version() -> int:
  351 | def _cli_god(args) -> int:
  387 | def _cli_console() -> int:
  417 | def main() -> int:
```

## `class` — 1 совпадений
```
   50 | class ProjectContext:
```

## `raise` — 3 совпадений
```
  183 |         raise SystemExit(rc)
  185 |         raise
  585 |     raise SystemExit(main())
```

## `return` — 58 совпадений
```
   41 |             return (
   47 |     return default_v, default_b
   79 |             return
   84 |                 return
  148 |         return {"verdict": rep.verdict, "percent": rep.percent_ready}
  151 |         return {"verdict": "UNKNOWN", "percent": 0}
  159 |         return False
  169 |         return False
  188 |         return False
  196 |         return False
  204 |         return True
  208 |         return False
  231 |         return report
  245 |     return report
  258 |             return int(mod.main() or 0)
  263 |     return 2
  274 |         return 0 if str(out.get("verdict", "")).endswith("PASS") else 1
  277 |         return 2
  284 |         return int(kpi_dashboard_v12.main() or 0)
  287 |         return 2
  294 |         return int(self_diag_v13.main_entry() or 0)
  297 |         return 2
  304 |         return int(real_e2e_v14.main() or 0)
  307 |         return 2
  315 |         return int(rc or 0)
  318 |         return 2
  323 |     return 0 if snap.get("verdict") in ("GREEN", "YELLOW") else 1
  334 |         return 0
  337 |         return 2
  348 |     return 0
  371 |                 return 2
  380 |         return 0
  384 |         return 2
  394 |             return 0
  396 |             return 0
  457 |         return _cli_version()
  465 |         return 0
  468 |         return _cli_smoke()
  471 |         return _cli_self_diag()
  474 |         return _cli_health()
  481 |         return _cli_dry_run()
  484 |         return _cli_dashboard()
  487 |         return _cli_e2e()
  490 |         return _cli_onboarding()
  493 |         return _cli_readiness()
  496 |         return _cli_console()
  504 |         return 0
  514 |         return 0
  527 |         return 0
  535 |         return 0
  544 |         return 0
  547 |         return _cli_god(args)
  559 |             return 1
  566 |                 return 1
  567 |         return 0
  571 |         return 2
  575 |         return 2
  581 |     return _cli_console()
```

## `if` — 37 совпадений
```
   39 |         if vp.exists():
   78 |         if enc in ("utf-8", "utf8", "cp65001"):
   81 |             if hasattr(sys.stdout, "reconfigure"):
  228 |     if not enabled:
  237 |             if callable(register):
  364 |             if genre not in known:
  368 |                 if hint:
  395 |         if cmd in ("exit", "quit", "q"):
  456 |     if args.version:
  459 |     if args.list_genres:
  467 |     if args.smoke:
  470 |     if args.self_diag:
  473 |     if args.health:
  480 |     if args.dry_run:
  483 |     if args.dashboard:
  486 |     if args.e2e:
  489 |     if args.onboarding:
  492 |     if args.readiness:
  495 |     if args.console:
  498 |     if args.ai_status:
  506 |     if args.ai_pull:
  508 |         if args.ai_pull.lower() == "all":
  516 |     if args.dossier_add and args.dossier_artist:
  522 |         if Path(src).is_dir():
  529 |     if args.dossier_build and args.dossier_artist:
  537 |     if args.ai:
  546 |     if args.god:
  549 |     if args.async_mode:
  562 |         if isinstance(result, dict):
  564 |             if status in ("failed", "error"):
  569 |     if args.gradio:
  570 |         if _try_launch_gui_gradio(): return 0
  573 |     if args.desktop:
  574 |         if _try_launch_gui_pyside(): return 0
  579 |     if _try_launch_gui_pyside(): return 0
  580 |     if _try_launch_gui_gradio(): return 0
  584 | if __name__ == "__main__":
```

## `for` — 5 совпадений
```
  233 |     for module_name in LEGACY_PATCH_MODULES:
  255 |     for name in ("tools.smoke_v29", "tools.smoke_v26"):
  463 |         for g in sorted(reg.list_genres()):
  501 |         for k, v in MODEL_REGISTRY.items():
  510 |             for k in MODEL_REGISTRY:
```

## `while` — 1 совпадений
```
  390 |     while True:
```

## `exec` — 1 совпадений
```
  182 |         rc = app.exec()
```
