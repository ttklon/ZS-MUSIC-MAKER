"""
ZS Music Maker — main.py (единая точка входа, консолидированная)
====================================================================

v22 changes:
  — generate-from-scratch: refs=[] теперь НЕ fallback (default genre-style);
  — structured synth_beat fallback (не 8с sine-каша);
  — formant vocal scaffold v22 (гласные/интонация/паузы);
  — жанровый пул fallback-лирикс;
  — lazy mkdir в 21 модуле (нет side-effect при импорте).

v17 fixes (сохранены):
  — VERSION / BUILD читаются из version.json;
  — консольная кодировка без инверсии;
  — CLI-режимы: --smoke, --dry-run, --dashboard, --self-diag,
                --e2e, --onboarding, --health, --readiness, --console,
                --version.
"""

from __future__ import annotations

import io
import json
import os
import sys
import traceback
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def _load_version_info():
    # A source checkout uses version.json as its release source of truth.  The
    # wheel ships main.py as a module, where that root-level JSON file is not
    # present, so use the packaged dynamic version as a safe installed fallback.
    default_v = "17.0.0"
    default_b = "wheel-installed"
    try:
        from app.version_info import __version__

        default_v = str(__version__)
    except Exception:
        pass
    try:
        vp = ROOT / "version.json"
        if vp.exists():
            data = json.loads(vp.read_text(encoding="utf-8"))
            return (
                str(data.get("version", default_v)),
                str(data.get("build", default_b)),
            )
    except Exception:
        pass
    return default_v, default_b


class ProjectContext:
    def __init__(self):
        v, b = _load_version_info()
        self.version = v
        self.build = b
        self.status = "GOD MODE 3.0 (Autonomy & Stability)"

ctx = ProjectContext()

# AUDIT-FIX P0: VERSION/BUILD использовались в _try_launch_gui_pyside (строка
# с setWindowTitle) и в _cli_version, но НИГДЕ не были определены как
# module-level имена — это давало NameError и краш `main.py --version` и
# запуска Desktop GUI. Определяем их из единственного источника правды
# (version.json), как и задумано в docstring v17.
VERSION = ctx.version
BUILD = ctx.build


def _setup_console_encoding() -> None:
    """
    v17 FIX: раньше логика была инвертирована — если stdout УЖЕ был UTF-8,
    его насильно оборачивали в cp866 и в Windows Terminal / PowerShell 7
    сыпались кракозябры. Теперь UTF-8 не трогаем, cp866 только как
    последний шанс.
    """
    try:
        os.environ.setdefault("PYTHONIOENCODING", "utf-8")
        enc = (getattr(sys.stdout, "encoding", "") or "").lower()
        if enc in ("utf-8", "utf8", "cp65001"):
            return
        try:
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
                sys.stderr.reconfigure(encoding="utf-8", errors="replace")
                return
        except Exception:
            pass
        try:
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer,
                encoding="utf-8",
                errors="replace",
                line_buffering=True,
            )
            sys.stderr = io.TextIOWrapper(
                sys.stderr.buffer,
                encoding="utf-8",
                errors="replace",
                line_buffering=True,
            )
        except Exception:
            try:
                sys.stdout = io.TextIOWrapper(
                    sys.stdout.buffer,
                    encoding="cp866",
                    errors="replace",
                    line_buffering=True,
                )
                sys.stderr = io.TextIOWrapper(
                    sys.stderr.buffer,
                    encoding="cp866",
                    errors="replace",
                    line_buffering=True,
                )
            except Exception:
                pass
    except Exception:
        pass


def _safe_print(msg: str) -> None:
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            sys.stdout.buffer.write((msg + "\n").encode("utf-8", "replace"))
        except Exception:
            pass


def _header() -> None:
    _safe_print("=" * 64)
    _safe_print(f"ZS Music Maker v{ctx.version} — main.py (unified)")
    _safe_print(f"Build: {ctx.build}")
    _safe_print(f"Status: {ctx.status}")
    _safe_print("=" * 64)


def _preflight_backup(mode: str) -> dict:
    """Create a bounded restore-capable snapshot before an explicit AI/God run."""
    try:
        from app.core.auto_backup import create_snapshot

        report = create_snapshot(mode)
        _safe_print(
            f"[backup] files={report['files']} bytes={report['total_bytes']} path={report['path']}"
        )
        return report
    except Exception as exc:
        # Backups protect work but must not silently make a requested render impossible.
        _safe_print(f"[backup] WARNING: preflight snapshot failed: {exc}")
        return {"ok": False, "reason": str(exc)}


def _health_snapshot() -> dict:
    try:
        from modules import health_v12

        rep = health_v12.collect()
        _safe_print(
            f"[main] health: {rep.verdict}  "
            f"ready={rep.percent_ready}%  "
            f"core_ok={rep.core_ok}"
        )
        return {"verdict": rep.verdict, "percent": rep.percent_ready}
    except Exception as e:
        _safe_print(f"[main] health_v12 not available: {e}")
        return {"verdict": "UNKNOWN", "percent": 0}


def _try_launch_gui_pyside() -> bool:
    try:
        from PySide6.QtWidgets import QApplication
    except Exception as e:
        _safe_print(f"[ERROR] PySide6 не найден. Для работы GUI установите: pip install PySide6. Ошибка: {e}")
        return False
    try:
        from app.gui import theme_v12
        from app.gui.wizard import Wizard
        from app.hw_probe import probe
        from app.logger import setup_logger
        from app.runtime_orchestrator import RuntimeOrchestrator
    except Exception as e:
        _safe_print(f"[ERROR] Не удалось загрузить модули GUI. Проверьте целостность папки app/gui. Ошибка: {e}")
        traceback.print_exc()
        return False
    app = QApplication.instance() or QApplication(sys.argv)
    try:
        theme_v12.apply(app)
    except Exception as exc:
        _safe_print(f"[main] GUI theme fallback after apply failure: {exc}")
    try:
        log = setup_logger("zsmm")
        hw = probe()
        orch = RuntimeOrchestrator(log=log)
        w = Wizard(orch=orch, hw=hw, log=log)
        w.setWindowTitle(f"ZS Music Maker v{VERSION} — Desktop Wizard")
        w.show()
        rc = app.exec()
        raise SystemExit(rc)
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        return False


def _try_launch_gui_gradio() -> bool:
    try:
        import gradio  # noqa: F401
    except Exception as e:
        _safe_print(f"[main] gradio недоступен: {e}")
        return False
    try:
        from app.core.orchestrator import build_gradio_ui

        demo = build_gradio_ui()
        demo.launch(
            server_name="127.0.0.1", server_port=7860, share=False, show_error=True
        )
        return True
    except Exception as e:
        _safe_print(f"[main] gradio UI failed: {e}")
        traceback.print_exc()
        return False


LEGACY_PATCH_MODULES = (
    "orchestrator_v12_patch",
    "orchestrator_v11_patch",
    "orchestrator_v10_patch",
    "orchestrator_v9_patch",
    "orchestrator_v8_patch",
)


def _print_legacy_report(enabled: bool) -> list[dict[str, object]]:
    """Print a deterministic compatibility report without importing patch code."""
    from app.core.orchestrator import legacy_compatibility_report

    report = legacy_compatibility_report(enabled)
    _safe_print(json.dumps({"legacy_enabled": enabled, "capabilities": report}, ensure_ascii=False, indent=2))
    return report


def _register_patches(enabled: bool = True) -> dict[str, object]:
    """Загрузить изолированный legacy-слой v8–v12 только по умолчанию.

    Новые пути должны опираться на единый core-оркестратор. Флаг
    ``--legacy-off`` оставляет старые патчи в репозитории для совместимости с
    Wizard, но не импортирует и не регистрирует их в текущем процессе.
    """
    report: dict[str, object] = {"enabled": enabled, "loaded": [], "skipped": []}
    if not enabled:
        report["skipped"] = list(LEGACY_PATCH_MODULES)
        _safe_print("[main] LEGACY patches disabled (--legacy-off).")
        return report

    for module_name in LEGACY_PATCH_MODULES:
        try:
            module = __import__(f"app.core.{module_name}", fromlist=[module_name])
            register = getattr(module, "register", None)
            if callable(register):
                register()
                report["loaded"].append(module_name)
            else:
                report["skipped"].append(module_name)
        except Exception as exc:
            report["skipped"].append(module_name)
            _safe_print(f"[main] LEGACY patch {module_name} unavailable: {exc}")
    return report


def _cli_smoke() -> int:
    """Runs the current smoke suite: v29 (God Mode E2E) → v26 (audio quality).

    v36 FIX: старая цепочка тянула smoke_v14/v15/v17/v21/v24/v25 — все они
    перенесены в docs/legacy/ ещё в v29 и по этим путям НЕ импортируются.
    Каждый вызов --smoke бесполезно печатал 6 строк «failed: No module named».
    Оставлены ТОЛЬКО реально работающие v29 → v26."""
    for name in ("tools.smoke_v29", "tools.smoke_v26"):
        try:
            mod = __import__(name, fromlist=["main"])
            return int(mod.main() or 0)
        except Exception as e:
            _safe_print(f"[main --smoke] {name} failed: {e}")

    _safe_print("[main --smoke] No valid smoke tests found.")
    return 2


def _cli_dry_run() -> int:
    try:
        from app.core.orchestrator import run_full_pipeline

        out = run_full_pipeline("cli", {}, dry_run=True)
        _safe_print(
            f"verdict={out.get('verdict')}  " f"duration={out.get('duration_sec')}s"
        )
        return 0 if str(out.get("verdict", "")).endswith("PASS") else 1
    except Exception as e:
        _safe_print(f"[main --dry-run] failed: {e}")
        return 2


def _cli_dashboard() -> int:
    try:
        from modules import kpi_dashboard_v12

        return int(kpi_dashboard_v12.main() or 0)
    except Exception as e:
        _safe_print(f"[main --dashboard] failed: {e}")
        return 2


def _cli_self_diag() -> int:
    try:
        from modules import self_diag_v13

        return int(self_diag_v13.main_entry() or 0)
    except Exception as e:
        _safe_print(f"[main --self-diag] failed: {e}")
        return 2


def _cli_e2e() -> int:
    try:
        from tools import real_e2e_v14

        return int(real_e2e_v14.main() or 0)
    except Exception as e:
        _safe_print(f"[main --e2e] tools/real_e2e_v14 failed: {e}")
        return 2


def _cli_onboarding() -> int:
    try:
        from modules import voice_onboarding

        rc = voice_onboarding.run_cli()
        return int(rc or 0)
    except Exception as e:
        _safe_print(f"[main --onboarding] failed: {e}")
        return 2


def _cli_health() -> int:
    snap = _health_snapshot()
    return 0 if snap.get("verdict") in ("GREEN", "YELLOW") else 1


def _cli_readiness() -> int:
    try:
        from tools import readiness

        pct, blocks = readiness.compute()
        _safe_print(
            json.dumps({"percent": pct, "blocks": blocks}, ensure_ascii=False, indent=2)
        )
        return 0
    except Exception as e:
        _safe_print(f"[main --readiness] failed: {e}")
        return 2


def _cli_version() -> int:
    try:
        from config.settings import get_settings
        cfg = get_settings()
        cfg_path = str(cfg.config_path)
    except Exception as _ce:  # noqa: BLE001 — конфиг опционален
        cfg_path = "unavailable"
    _safe_print(json.dumps({"version": VERSION, "build": BUILD, "config": cfg_path}, ensure_ascii=False))
    return 0


def _cli_god(args) -> int:
    try:
        from app.core.orchestrator_god import run_god_pipeline

        genre = getattr(args, "genre", "drift_phonk")
        theme = getattr(args, "theme", genre)

        # v34 FIX (SESSION_LOG v32.22): раньше несуществующий жанр падал
        # глубоко внутри пайплайна с непонятным KeyError. Теперь валидация
        # против StyleRegistry на входе + подсказка ближайших вариантов.
        try:
            from modules.genre_engine import StyleRegistry
            known = set(StyleRegistry().list_genres())
            if genre not in known:
                import difflib
                hint = difflib.get_close_matches(genre, sorted(known), n=3, cutoff=0.5)
                _safe_print(f"[main --god] unknown genre: {genre!r}")
                if hint:
                    _safe_print(f"  did you mean: {', '.join(hint)}?")
                _safe_print("  full list: python main.py --list-genres")
                return 2
        except ImportError:
            pass  # движок жанров недоступен — пусть пайплайн сам решит

        _safe_print(f"[main --god] Launching GOD MODE pipeline (genre={genre}, theme={theme})...")
        out = run_god_pipeline("god_cli", {"theme": theme, "genre": genre})
        _safe_print(
            f"GOD MODE COMPLETED: elapsed={out.get('elapsed_sec')}s master={out.get('master_path')}"
        )
        return 0
    except Exception as e:
        _safe_print(f"[main --god] failed: {e}")
        traceback.print_exc()
        return 2


def _cli_console() -> int:
    _safe_print("[main --console] запущен без GUI. Команды:")
    _safe_print("  smoke | e2e | diag | health | readiness | dry | version | exit")
    while True:
        try:
            cmd = input("zsmm> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return 0
        if cmd in ("exit", "quit", "q"):
            return 0
        elif cmd == "smoke":
            _cli_smoke()
        elif cmd == "e2e":
            _cli_e2e()
        elif cmd == "diag":
            _cli_self_diag()
        elif cmd == "health":
            _cli_health()
        elif cmd == "readiness":
            _cli_readiness()
        elif cmd == "dry":
            _cli_dry_run()
        elif cmd == "version":
            _cli_version()
        else:
            _safe_print(
                "unknown; try: smoke|e2e|diag|health|readiness|dry|version|exit"
            )


def main() -> int:
    _setup_console_encoding()
    _header()
    
    parser = argparse.ArgumentParser(description="ZS Music Maker — Professional AI Music Production Station")
    parser.add_argument("--god", action="store_true", help="Launch the ULTIMATE GOD MODE pipeline")
    parser.add_argument("--async-mode", action="store_true", help="Launch parallel async pipeline")
    parser.add_argument("--genre", type=str, default="drift_phonk", help="Target genre (100+ available)")
    parser.add_argument("--theme", type=str, default="drift_phonk", help="Target theme/mood")
    parser.add_argument("--list-genres", action="store_true", help="Show all 119+ available genres")
    parser.add_argument("--smoke", action="store_true", help="Run quality smoke tests")
    parser.add_argument("--self-diag", action="store_true", help="Run system self-diagnostics")
    parser.add_argument("--health", action="store_true", help="Check system health and GPU")
    parser.add_argument("--version", "-V", action="store_true", help="Show version info")
    parser.add_argument("--gradio", action="store_true", help="Launch Web UI (Gradio)")
    parser.add_argument("--desktop", action="store_true", help="Launch Desktop UI (PySide6)")
    # AUDIT-FIX P0: нижеперечисленные режимы имели реализации (_cli_*),
    # рекламировались в docstring модуля, но НЕ были подключены к argparse —
    # `main.py --dry-run` и др. падали с "unrecognized arguments".
    parser.add_argument("--dry-run", action="store_true", help="Run pipeline in dry-run (no heavy deps)")
    parser.add_argument("--dashboard", action="store_true", help="Show KPI dashboard")
    parser.add_argument("--e2e", action="store_true", help="Run real end-to-end test")
    parser.add_argument("--onboarding", action="store_true", help="Run voice onboarding CLI")
    parser.add_argument("--readiness", action="store_true", help="Compute readiness percent")
    parser.add_argument("--console", action="store_true", help="Force console REPL mode (no GUI)")
    parser.add_argument(
        "--legacy-off",
        action="store_true",
        help="Skip legacy v8-v12 patch registration for runtime pipelines",
    )
    parser.add_argument(
        "--legacy-report",
        action="store_true",
        help="Print the v8-v12 compatibility capability matrix and exit",
    )
    parser.add_argument("--ai", action="store_true", help="Launch AI GOD MODE 4.0 (sequential AI stack)")
    parser.add_argument("--ai-status", action="store_true", help="Show AI model registry & availability")
    parser.add_argument("--ai-pull", type=str, default="", help="Pull one AI model role (or 'all')")
    parser.add_argument("--dossier-artist", type=str, default="", help="Artist name/slug for dossier")
    parser.add_argument("--dossier-add", type=str, default="", help="Add local folder source")
    parser.add_argument("--dossier-build", action="store_true", help="Run full AI dossier build (heavy)")
    parser.add_argument("--score", type=str, default="", help="Score a mastered WAV and print hit-score breakdown")
    parser.add_argument("--update", action="store_true", help="Check Git update status without applying changes")

    args = parser.parse_args()

    if args.version:
        return _cli_version()

    # Report before early CLI exits such as --smoke.  This records exactly what
    # compatibility behavior is intentionally unavailable without loading it.
    if args.legacy_off:
        _print_legacy_report(enabled=False)
    if args.legacy_report:
        _print_legacy_report(enabled=not args.legacy_off)
        return 0
    
    if args.list_genres:
        from modules.genre_engine import StyleRegistry
        reg = StyleRegistry()
        print("\nAvailable Genres:")
        for g in sorted(reg.list_genres()):
            print(f"  - {g}")
        return 0

    if args.smoke:
        return _cli_smoke()
    
    if args.self_diag:
        return _cli_self_diag()
    
    if args.health:
        return _cli_health()

    # Legacy v8..v12 сохранён для обратной совместимости, но его загрузка
    # теперь управляется явно. Новый core-путь работает и без этих патчей.
    _register_patches(enabled=not args.legacy_off)

    if args.dry_run:
        if args.ai:
            _preflight_backup("ai_dry_run")
            from app.core.orchestrator_ai import run_ai_pipeline

            ws = {
                "genre": args.genre,
                "theme": args.theme,
                "artist_slug": args.dossier_artist or None,
            }
            out = run_ai_pipeline("ai_cli_dry_run", ws, dry_run=True, terminal_progress=True)
            print(json.dumps({"stages": out["report"]["stages"]}, ensure_ascii=False, indent=2))
            return 0
        return _cli_dry_run()

    if args.dashboard:
        return _cli_dashboard()

    if args.e2e:
        return _cli_e2e()

    if args.onboarding:
        return _cli_onboarding()

    if args.readiness:
        return _cli_readiness()

    if args.console:
        return _cli_console()

    if args.update:
        from updater.updater import check_git_update_status
        report = check_git_update_status(ROOT)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report.get("ok") else 2

    if args.score:
        from modules.hit_scorer import score_track
        report = score_track(args.score)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if not report.get("error") else 2

    if args.ai_status:
        from app.ai.registry import registry, MODEL_REGISTRY
        print("[AI] Hardware budget:", registry.hw)
        for k, v in MODEL_REGISTRY.items():
            avail = "OK" if registry.is_available(k) else "--"
            print(f"  {avail} {k:20s} {v['engine']:22s} VRAM~{v.get('vram_est_gb', 0)} GB - {v['role']}")
        return 0

    if args.ai_pull:
        from tools import pull_ai_models as pm
        if args.ai_pull.lower() == "all":
            from app.ai.registry import MODEL_REGISTRY
            for k in MODEL_REGISTRY:
                pm.pull(k)
        else:
            pm.pull(args.ai_pull)
        return 0

    if args.dossier_add and args.dossier_artist:
        from modules.artist_dossier import DossierManager
        from modules.artist_dossier.collectors import LocalFolderCollector, LyricVaultCollector
        mgr = DossierManager()
        src = args.dossier_add
        tracks = []
        if Path(src).is_dir():
            tracks = LocalFolderCollector(src).collect(args.dossier_artist)
        tracks += LyricVaultCollector(str(ROOT / "lyric_vault")).collect(args.dossier_artist)
        mgr.add_artist(args.dossier_artist, tracks=tracks)
        print(f"[dossier] artist={args.dossier_artist} tracks_added={len(tracks)}")
        return 0

    if args.dossier_build and args.dossier_artist:
        from modules.artist_dossier import DossierManager
        mgr = DossierManager()
        d = mgr.build_full_dossier(args.dossier_artist,
                                   progress_cb=lambda tid, st: print(f"  [{tid}] {st}"))
        print(json.dumps(d, ensure_ascii=False, indent=2)[:2000])
        return 0

    if args.ai:
        _preflight_backup("ai")
        from app.core.orchestrator_ai import run_ai_pipeline
        ws = {"genre": args.genre, "theme": args.theme,
              "artist_slug": args.dossier_artist or None}
        out = run_ai_pipeline("ai_cli", ws, dry_run=False, terminal_progress=True)
        print(json.dumps({"stages": out["report"]["stages"],
                          "artefacts": out["artefacts"]}, ensure_ascii=False, indent=2))
        return 0

    if args.god:
        _preflight_backup("god")
        return _cli_god(args)
    
    if args.async_mode:
        # v33 FIX (P1, SESSION_LOG v32.9): раньше --async-mode ВСЕГДА
        # возвращал 0, даже если пайплайн упал — exit code врал CI.
        import asyncio
        from app.core.orchestrator_async import AsyncOrchestrator
        try:
            orch = AsyncOrchestrator("async_cli", ROOT / "output" / "async_cli")
            result = asyncio.run(orch.run_pipeline({"genre": args.genre}))
        except Exception as e:
            print(f"[async-mode] PIPELINE FAILED: {e}")
            return 1
        # Оркестратор может вернуть dict со статусом или None —
        # считаем падением только явный status=failed/error.
        if isinstance(result, dict):
            status = str(result.get("status", "")).lower()
            if status in ("failed", "error"):
                print(f"[async-mode] pipeline status={status}")
                return 1
        return 0

    if args.gradio:
        if _try_launch_gui_gradio(): return 0
        return 2

    if args.desktop:
        if _try_launch_gui_pyside(): return 0
        return 2

    # Default behavior: try GUI, then console
    _health_snapshot()
    if _try_launch_gui_pyside(): return 0
    if _try_launch_gui_gradio(): return 0
    return _cli_console()


if __name__ == "__main__":
    raise SystemExit(main())
