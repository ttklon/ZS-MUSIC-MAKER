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
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def _load_version_info():
    default_v = "17.0.0"
    default_b = "v17-consolidated"
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


VERSION, BUILD = _load_version_info()


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
    _safe_print(f"ZS Music Maker v{VERSION} — main.py (unified)")
    _safe_print(f"Build: {BUILD}")
    _safe_print("=" * 64)


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
        _safe_print(f"[main] PySide6 недоступен: {e}")
        return False
    try:
        from app.gui import theme_v12
        from app.gui.wizard import Wizard
        from app.hw_probe import probe
        from app.logger import setup_logger
        from app.runtime_orchestrator import RuntimeOrchestrator
    except Exception as e:
        _safe_print(f"[main] desktop wizard недоступен: {e}")
        traceback.print_exc()
        return False
    app = QApplication.instance() or QApplication(sys.argv)
    try:
        theme_v12.apply(app)
    except Exception:
        pass
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


def _register_patches() -> None:
    for m in (
        "orchestrator_v12_patch",
        "orchestrator_v11_patch",
        "orchestrator_v10_patch",
        "orchestrator_v9_patch",
        "orchestrator_v8_patch",
    ):
        try:
            mod = __import__(f"app.core.{m}", fromlist=[m])
            if hasattr(mod, "register"):
                mod.register()
        except Exception:
            pass


def _cli_smoke() -> int:
    for name in (
        "tools.smoke_v21",
        "tools.smoke_v17",
        "tools.smoke_v15",
        "tools.smoke_v14",
    ):
        try:
            mod = __import__(name, fromlist=["main"])
            return int(mod.main() or 0)
        except Exception as e:
            _safe_print(f"[main --smoke] {name} failed: {e}")
    try:
        import legacy.smoke.smoke_v13 as sm

        return int(sm.main() or 0)
    except Exception as e2:
        _safe_print(f"[main --smoke] legacy smoke_v13 failed: {e2}")
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
    _safe_print(json.dumps({"version": VERSION, "build": BUILD}, ensure_ascii=False))
    return 0


def _cli_god() -> int:
    try:
        from app.core.orchestrator_god import run_god_pipeline

        # Парсинг аргументов
        genre = "drift_phonk"
        theme = "drift_phonk"
        for i, arg in enumerate(sys.argv):
            if arg == "--genre" and i + 1 < len(sys.argv):
                genre = sys.argv[i + 1]
            if arg == "--theme" and i + 1 < len(sys.argv):
                theme = sys.argv[i + 1]

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
    # v26: Патчи больше не нужны, используем единое ядро
    # _register_patches()

    args = set(sys.argv[1:])
    if "--smoke" in args:
        return _cli_smoke()
    if "--dry-run" in args:
        return _cli_dry_run()
    if "--dashboard" in args:
        return _cli_dashboard()
    if "--self-diag" in args:
        return _cli_self_diag()
    if "--e2e" in args:
        return _cli_e2e()
    if "--onboarding" in args:
        return _cli_onboarding()
    if "--health" in args:
        return _cli_health()
    if "--readiness" in args:
        return _cli_readiness()
    if "--console" in args:
        return _cli_console()
    if "--god" in args:
        # v26: Используем новое PipelineCore для God Mode
        from app.core.pipeline_core import ZSPipeline
        from app.core.orchestrator_god import run_god_pipeline
        return _cli_god()
    if "--async" in args:
        import asyncio
        from app.core.orchestrator_async import AsyncOrchestrator

        orch = AsyncOrchestrator("async_cli", ROOT / "output" / "async_cli")
        asyncio.run(orch.run_pipeline({"genre": "phonk", "bpm_override": 135}))
        return 0
    if "--version" in args or "-V" in args:
        return _cli_version()
    if "--gradio" in args:
        if _try_launch_gui_gradio():
            return 0
        _safe_print("[main] gradio requested, but unavailable.")
        return 2
    if "--desktop" in args:
        if _try_launch_gui_pyside():
            return 0
        _safe_print("[main] desktop requested, but unavailable.")
        return 2

    _health_snapshot()
    if _try_launch_gui_pyside():
        return 0
    if _try_launch_gui_gradio():
        return 0
    _safe_print("[main] GUI недоступен, переключаемся в console-режим.")
    return _cli_console()


if __name__ == "__main__":
    raise SystemExit(main())
