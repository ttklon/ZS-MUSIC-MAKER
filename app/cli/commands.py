# -*- coding: utf-8 -*-
"""
app/cli/commands.py — обработчики всех неинтерактивных режимов CLI.

Каждая функция возвращает POSIX exit code: 0 — успех, 1 — провал проверки,
2 — ошибка окружения. Логика тяжёлых подсистем здесь не дублируется: команды
только собирают аргументы и вызывают канонические entrypoint-функции.
"""

from __future__ import annotations

import json
import traceback
from pathlib import Path

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
    for name in ("tools.smoke_god", "tools.smoke_audio"):
        try:
            mod = __import__(name, fromlist=["main"])
            return int(mod.main() or 0)
        except Exception as e:
            safe_print(f"[main --smoke] {name} failed: {e}")
    safe_print("[main --smoke] No valid smoke tests found.")
    return 2


def run_dry_run() -> int:
    try:
        from app.core.orchestrator import run_full_pipeline

        out = run_full_pipeline("cli", {}, dry_run=True)
        safe_print(f"verdict={out.get('verdict')}  duration={out.get('duration_sec')}s")
        return 0 if str(out.get("verdict", "")).endswith("PASS") else 1
    except Exception as e:
        safe_print(f"[main --dry-run] failed: {e}")
        return 2


def parse_only(raw: str) -> set[str] | None:
    """`--only beat,lyrics` → {'beat', 'lyrics'}; пусто → None (все стадии)."""
    keys = {part.strip() for part in (raw or "").split(",") if part.strip()}
    return keys or None


def run_list_stages() -> int:
    from app.core.pipeline_runtime import STAGE_KEYS

    safe_print("Stages usable with --only:")
    for key in STAGE_KEYS:
        safe_print(f"  - {key}")
    return 0


def run_pipeline(args) -> int:
    """Полный классический прогон без GUI — с seed/resume/only."""
    try:
        from app.core.orchestrator import run_full_pipeline

        only = parse_only(args.only)
        wizard_state: dict = {"genre": args.genre, "theme": args.theme}
        if args.dossier_artist:
            wizard_state["artist"] = args.dossier_artist
        if args.seed is not None:
            wizard_state["seed"] = args.seed
        project_id = f"cli_{args.genre}"
        out = run_full_pipeline(
            project_id,
            wizard_state,
            dry_run=args.dry_run,
            only=only,
            resume=args.resume,
        )
    except ValueError as exc:
        safe_print(f"[main --run] {exc}")
        return 2
    except Exception as e:
        safe_print(f"[main --run] failed: {e}")
        return 2
    safe_print(
        json.dumps(
            {
                "verdict": out.get("verdict"),
                "percent": out.get("percent"),
                "master": out.get("master_path"),
                "seed": out.get("seed"),
                "only": out.get("only"),
                "resume": out.get("resume"),
                "duration_sec": out.get("duration_sec"),
                "status_summary": out.get("status_summary"),
                "warnings": out.get("warnings"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if str(out.get("verdict", "")).endswith("PASS") else 1


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

        safe_print(f"[AI] Hardware budget: {registry.hw}")
        for key, meta in MODEL_REGISTRY.items():
            avail = "OK" if registry.is_available(key) else "--"
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

            for role in MODEL_REGISTRY:
                pm.pull(role)
        else:
            pm.pull(target)
        return 0
    except Exception as e:
        safe_print(f"[main --ai-pull] failed: {e}")
        return 2


def run_dossier_add(artist: str, source_dir: str) -> int:
    try:
        from modules.artist_dossier import DossierManager
        from modules.artist_dossier.collectors import (
            LocalFolderCollector,
            LyricVaultCollector,
        )

        tracks = []
        if Path(source_dir).is_dir():
            tracks = LocalFolderCollector(source_dir).collect(artist)
        tracks += LyricVaultCollector(str(ROOT / "lyric_vault")).collect(artist)
        DossierManager().add_artist(artist, tracks=tracks)
        safe_print(f"[dossier] artist={artist} tracks_added={len(tracks)}")
        return 0
    except Exception as e:
        safe_print(f"[main --dossier-add] failed: {e}")
        return 2


def run_dossier_build(artist: str) -> int:
    try:
        from modules.artist_dossier import DossierManager

        dossier = DossierManager().build_full_dossier(
            artist, progress_cb=lambda track_id, stage: safe_print(f"  [{track_id}] {stage}")
        )
        safe_print(json.dumps(dossier, ensure_ascii=False, indent=2)[:2000])
        return 0
    except Exception as e:
        safe_print(f"[main --dossier-build] failed: {e}")
        return 2


def _run_ai_pipeline(
    args, *, dry_run: bool, run_id: str, backup_mode: str | None = None
) -> int:
    from app.cli.backup import preflight_backup

    if backup_mode:
        preflight_backup(backup_mode)
    try:
        from app.core.orchestrator_ai import run_ai_pipeline

        workspace = {
            "genre": args.genre,
            "theme": args.theme,
            "artist_slug": args.dossier_artist or None,
        }
        out = run_ai_pipeline(run_id, workspace, dry_run=dry_run, terminal_progress=True)
        payload = {"stages": out["report"]["stages"]}
        if not dry_run:
            payload["artefacts"] = out["artefacts"]
        safe_print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        safe_print(f"[main] AI pipeline failed: {e}")
        return 2


def run_ai(args) -> int:
    return _run_ai_pipeline(args, dry_run=False, run_id="ai_cli", backup_mode="ai")


def run_ai_dry_run(args) -> int:
    return _run_ai_pipeline(
        args, dry_run=True, run_id="ai_cli_dry_run", backup_mode="ai_dry_run"
    )


def run_god(args) -> int:
    genre = getattr(args, "genre", "drift_phonk")
    theme = getattr(args, "theme", genre)

    # Неизвестный жанр раньше падал глубоко в пайплайне непонятным KeyError.
    try:
        from modules.genre_engine import StyleRegistry

        known = set(StyleRegistry().list_genres())
        if genre not in known:
            import difflib

            safe_print(f"[main --god] unknown genre: {genre!r}")
            hint = difflib.get_close_matches(genre, sorted(known), n=3, cutoff=0.5)
            if hint:
                safe_print(f"  did you mean: {', '.join(hint)}?")
            safe_print("  full list: python main.py --list-genres")
            return 2
    except ImportError:
        pass  # движок жанров недоступен — пусть пайплайн сам решит

    from app.cli.backup import preflight_backup

    preflight_backup("god")
    try:
        from app.core.orchestrator_god import run_god_pipeline

        safe_print(
            f"[main --god] Launching GOD MODE pipeline (genre={genre}, theme={theme})..."
        )
        out = run_god_pipeline("god_cli", {"theme": theme, "genre": genre})
        safe_print(
            f"GOD MODE COMPLETED: elapsed={out.get('elapsed_sec')}s "
            f"master={out.get('master_path')}"
        )
        return 0
    except Exception as e:
        safe_print(f"[main --god] failed: {e}")
        traceback.print_exc()
        return 2


def run_async(args) -> int:
    import asyncio

    try:
        from app.core.orchestrator_async import AsyncOrchestrator

        orch = AsyncOrchestrator("async_cli", ROOT / "output" / "async_cli")
        result = asyncio.run(orch.run_pipeline({"genre": args.genre}))
    except Exception as e:
        safe_print(f"[async-mode] PIPELINE FAILED: {e}")
        return 1
    # Статус failed/error — единственное честное основание вернуть код ошибки.
    if isinstance(result, dict) and str(result.get("status", "")).lower() in (
        "failed",
        "error",
    ):
        safe_print(f"[async-mode] pipeline status={result.get('status')}")
        return 1
    return 0


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
