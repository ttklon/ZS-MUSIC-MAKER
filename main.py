# -*- coding: utf-8 -*-
"""
ZS Music Maker — единая точка входа
===================================

Основной пользовательский продукт — установленный Electron.
Python без флагов показывает инструкцию; PySide/Gradio/console доступны только
по явному выбору как legacy, не как автоматически выбранная основная студия.

Все неинтерактивные режимы (`--god`, `--ai`, `--smoke`, `--score`,
`--readiness`, `--update`, …) обслуживает пакет `app.cli`:
`parser` описывает флаги, `commands` — обработчики, `gui` — запуск UI,
`env` — версия и кодировка консоли, `backup` — preflight-снимок.

`main.py` намеренно тонкий: здесь только маршрутизация флагов и запуск GUI.
"""

from __future__ import annotations

import multiprocessing
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from app.cli import commands  # noqa: E402  (ROOT должен попасть в sys.path раньше)
from app.cli import dossier as dossier_cmds  # noqa: E402
from app.cli import pipeline as pipeline_cmds  # noqa: E402
from app.cli.env import ctx, header, setup_console_encoding  # noqa: E402
from app.cli.parser import build_parser  # noqa: E402

# Обратная совместимость для внешних скриптов и тестов, которые обращаются
# к `main.VERSION` / `main.BUILD` / `main.ctx`.
VERSION = ctx.version
BUILD = ctx.build


def _run_info_command(args) -> int | None:
    """Информация и явно запрошенная подготовка; чтение не вызывает докачку.

    Вынесено из `main()`, чтобы она осталась маршрутизатором, а не таблицей
    флагов: правило проекта — функция ≤ 60 строк.
    """
    dispatch = (
        (args.version, commands.run_version),
        (args.list_genres, commands.run_list_genres),
        (args.list_stages, pipeline_cmds.run_list_stages),
        (args.smoke, commands.run_smoke),
        (args.self_diag, commands.run_self_diag),
        (args.health, commands.run_health),
        (args.readiness, commands.run_readiness),
        (args.dashboard, commands.run_dashboard),
        (args.e2e, commands.run_e2e),
        (args.onboarding, commands.run_onboarding),
        (args.update, lambda: commands.run_update(allow_online=bool(getattr(args, "online", False)))),
    )
    for enabled, handler in dispatch:
        if enabled:
            return handler()
    if args.entrypoints:
        from app.cli.probes import entrypoint_snapshot
        return entrypoint_snapshot()
    if args.resource_policy:
        from app.cli.probes import resource_policy_snapshot
        return resource_policy_snapshot()
    if args.ollama_status:
        return commands.run_ollama_status()

    if args.ollama_setup:
        return commands.run_ollama_setup()

    if args.rvc_setup:
        return commands.run_rvc_setup()
    if args.rvc_train:
        return commands.run_rvc_train(args.rvc_voice, args.rvc_epochs)
    if args.rvc_fork:
        return commands.run_rvc_fork(args.rvc_fork)
    if args.bootstrap or args.auto_bootstrap:
        return commands.run_bootstrap(allow_online=bool(getattr(args, "online", False)))
    return None


def main() -> int:
    # Собранный PyInstaller-exe должен уметь порождать процессы (мастеринг
    # считает стенды параллельно): без freeze_support дочерний процесс
    # перезапускает exe целиком и уходит в рекурсию.
    multiprocessing.freeze_support()
    setup_console_encoding()
    header()
    args = build_parser().parse_args()

    # Preparation is explicit; read-only/help/default entrypoints never bootstrap.
    # 1) Команды без побочных эффектов на проект.
    early = _run_info_command(args)
    if early is not None:
        return early

    # 2) Пробы и оценка готового мастера.
    if args.score:
        return commands.run_score(args.score)
    if args.ai_status:
        return commands.run_ai_status()
    if args.ai_pull:
        return commands.run_ai_pull(args.ai_pull)

    # 3) Досье артиста.
    if args.dossier_add and args.dossier_artist:
        return dossier_cmds.run_dossier_add(args.dossier_artist, args.dossier_add)
    if args.dossier_build and args.dossier_artist:
        return dossier_cmds.run_dossier_build(args.dossier_artist)

    # 4a) HIT FACTORY — автономная фабрика хитов (приоритет выше классики)
    if getattr(args, "agent_hit", False):
        from app.cli.agent_task import run_agent_hit

        return run_agent_hit(args)
    if getattr(args, 'hit_factory', False):
        from app.cli.hitfactory import run_hit_factory
        return run_hit_factory(args)

    # 4) Пайплайны. `--seed/--resume/--only` относятся к классическому DAG.
    classic = (args.run or args.dry_run or args.resume or args.only or args.seed is not None)
    if classic and (args.ai or args.god or args.async_mode):
        from app.cli.env import safe_print

        safe_print(
            "[main] --seed/--resume/--only apply to the classic pipeline (--run); "
            "ignored for --ai/--god/--async-mode"
        )
    if args.ai and args.dry_run:
        return pipeline_cmds.run_ai_dry_run(args)
    if args.ai:
        return pipeline_cmds.run_ai(args)
    if args.god:
        return pipeline_cmds.run_god(args)
    if args.async_mode:
        return pipeline_cmds.run_async(args)
    if classic:
        return pipeline_cmds.run_pipeline(args)

    # 5) Интерфейсы.
    if args.console:
        from app.core.entrypoints import LEGACY_NOTICE
        from app.cli.env import safe_print
        safe_print(LEGACY_NOTICE)
        return commands.run_console()
    if args.gradio or args.desktop:
        from app.cli import gui
        from app.core.entrypoints import LEGACY_NOTICE
        from app.cli.env import safe_print
        safe_print(LEGACY_NOTICE)

        launched = gui.try_launch_gradio() if args.gradio else gui.try_launch_pyside()
        return 0 if launched else 2

    # No silent legacy GUI/network fallback from the Python entrypoint.
    from app.core.entrypoints import default_instructions
    from app.cli.env import safe_print

    safe_print(default_instructions())
    return 2


def cli_entry() -> int:
    """CLI entrypoint used by the script and installed console command."""
    from app.core.numba_cache import isolated_numba_cache

    with isolated_numba_cache():
        return main()


if __name__ == "__main__":
    raise SystemExit(cli_entry())
