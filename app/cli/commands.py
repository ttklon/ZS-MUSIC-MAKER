# -*- coding: utf-8 -*-
"""
app/cli/commands.py — обработчики всех неинтерактивных режимов CLI.

Каждая функция возвращает POSIX exit code: 0 — успех, 1 — провал проверки,
2 — ошибка окружения. Логика тяжёлых подсистем здесь не дублируется: команды
только собирают аргументы и вызывают канонические entrypoint-функции.
"""

from __future__ import annotations

import json

from app.cli.env import BUILD, ROOT, VERSION, safe_print
from app.cli.probes import health_snapshot


def run_version() -> int:
    try:
        from config.settings import get_settings

        cfg_path = str(get_settings().config_path)
    except Exception:  # noqa: BLE001 — конфиг опционален
        cfg_path = "unavailable"
    safe_print(
        json.dumps(
            {"version": VERSION, "build": BUILD, "config": cfg_path},
            ensure_ascii=False,
        )
    )
    return 0


def run_list_genres() -> int:
    try:
        from modules.genre_engine import StyleRegistry
    except Exception as e:
        safe_print(f"[main --list-genres] failed: {e}")
        return 2
    safe_print("\nAvailable Genres:")
    for genre in sorted(StyleRegistry().list_genres()):
        safe_print(f"  - {genre}")
    return 0


def run_smoke() -> int:
    """Smoke-набор: God Mode E2E → качество аудио."""
    codes = []
    for name in ("tools.smoke_god", "tools.smoke_audio"):
        try:
            mod = __import__(name, fromlist=["main"])
            codes.append(int(mod.main() or 0))
        except Exception as e:
            safe_print(f"[main --smoke] {name} failed: {e}")
            codes.append(2)
    return max(codes)


def run_dry_run() -> int:
    try:
        from app.core.orchestrator import run_full_pipeline

        out = run_full_pipeline("cli", {}, dry_run=True)
        safe_print(f"verdict={out.get('verdict')}  duration={out.get('duration_sec')}s")
        return 0 if str(out.get("verdict", "")).endswith("PASS") else 1
    except Exception as e:
        safe_print(f"[main --dry-run] failed: {e}")
        return 2


def run_dashboard() -> int:
    try:
        from modules import kpi_dashboard

        return int(kpi_dashboard.main() or 0)
    except Exception as e:
        safe_print(f"[main --dashboard] failed: {e}")
        return 2


def run_self_diag() -> int:
    try:
        from modules import self_diag

        return int(self_diag.main_entry() or 0)
    except Exception as e:
        safe_print(f"[main --self-diag] failed: {e}")
        return 2


def run_e2e() -> int:
    try:
        from tools import e2e

        return int(e2e.main() or 0)
    except Exception as e:
        safe_print(f"[main --e2e] tools/e2e failed: {e}")
        return 2


def run_onboarding() -> int:
    try:
        from modules import voice_onboarding

        return int(voice_onboarding.run_cli() or 0)
    except Exception as e:
        safe_print(f"[main --onboarding] failed: {e}")
        return 2


def run_health() -> int:
    snap = health_snapshot()
    return 0 if snap.get("verdict") in ("GREEN", "YELLOW") else 1


def run_readiness() -> int:
    try:
        from tools import readiness

        pct, blocks = readiness.compute()
        safe_print(
            json.dumps({"percent": pct, "blocks": blocks}, ensure_ascii=False, indent=2)
        )
        return 0
    except Exception as e:
        safe_print(f"[main --readiness] failed: {e}")
        return 2


def run_update() -> int:
    try:
        from updater.updater import check_git_update_status

        report = check_git_update_status(ROOT)
    except Exception as e:
        safe_print(f"[main --update] failed: {e}")
        return 2
    safe_print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("ok") else 2


def run_score(master_wav: str) -> int:
    try:
        from modules.hit_scorer import score_track

        report = score_track(master_wav)
    except Exception as e:
        safe_print(f"[main --score] failed: {e}")
        return 2
    safe_print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not report.get("error") else 2


def run_ai_status() -> int:
    try:
        from app.ai.registry import MODEL_REGISTRY, registry
        from app.core.hw_autodetect import detect, human_summary

        safe_print("[AI] Current hardware profile:")
        safe_print(human_summary(detect()))
        safe_print(f"[AI] Hardware budget: {registry.hw}")
        safe_print("[AI] Presence checks only; dependencies for non-GGUF roles do not prove weights or inference.")
        for key, meta in MODEL_REGISTRY.items():
            available = registry.is_available(key)
            avail = ("FILES" if key == "vocal_rvc" else "YES") if available else "--"
            safe_print(
                f"  {avail} {key:20s} {meta['engine']:22s} "
                f"VRAM~{meta.get('vram_est_gb', 0)} GB - {meta['role']}"
            )
        return 0
    except Exception as e:
        safe_print(f"[main --ai-status] failed: {e}")
        return 2


def run_ai_pull(target: str) -> int:
    try:
        from tools import pull_ai_models as pm

        if target.lower() == "all":
            from app.ai.registry import MODEL_REGISTRY

            results = [pm.pull(role) for role in MODEL_REGISTRY]
            return 0 if all(results) else 2
        return 0 if pm.pull(target) else 2
    except Exception as e:
        safe_print(f"[main --ai-pull] failed: {e}")
        return 2


def run_console() -> int:
    """Консольный REPL — запасной путь, когда GUI невозможен."""
    safe_print("[main --console] запущен без GUI. Команды:")
    safe_print("  smoke | e2e | diag | health | readiness | dry | version | exit")
    dispatch = {
        "smoke": run_smoke,
        "e2e": run_e2e,
        "diag": run_self_diag,
        "health": run_health,
        "readiness": run_readiness,
        "dry": run_dry_run,
        "version": run_version,
    }
    while True:
        try:
            cmd = input("zsmm> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return 0
        if cmd in ("exit", "quit", "q"):
            return 0
        handler = dispatch.get(cmd)
        if handler is None:
            safe_print("unknown; try: smoke|e2e|diag|health|readiness|dry|version|exit")
            continue
        handler()
