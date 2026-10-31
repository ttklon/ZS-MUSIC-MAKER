# -*- coding: utf-8 -*-
"""
app/cli/pipeline.py — команды запуска пайплайнов и досье из CLI.

Здесь живёт всё, что реально запускает тяжёлые стадии: классический DAG
(`--run`, `--dry-run`, `--seed/--resume/--only`), AI-пайплайн, God Mode,
async-оркестратор и сборка досье артиста.
"""

from __future__ import annotations

import json
import traceback

from app.cli.env import ROOT, safe_print


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
