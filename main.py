# -*- coding: utf-8 -*-
"""
ZS Music Maker — единая точка входа
===================================

Три способа работы, в порядке приоритета:

* Desktop Wizard (PySide6) — `python main.py`, `--desktop`;
* Web UI (Gradio) — `--gradio`;
* консольный REPL — `--console` или автоматический откат, если GUI нет.

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


def main() -> int:
    # Собранный PyInstaller-exe должен уметь порождать процессы (мастеринг
    # считает стенды параллельно): без freeze_support дочерний процесс
    # перезапускает exe целиком и уходит в рекурсию.
    multiprocessing.freeze_support()
    setup_console_encoding()
    header()
    args = build_parser().parse_args()

    # 1) Команды без побочных эффектов на проект.
    if args.version:
        return commands.run_version()
    if args.list_genres:
        return commands.run_list_genres()
    if args.list_stages:
        return pipeline_cmds.run_list_stages()
    if args.smoke:
        return commands.run_smoke()
    if args.self_diag:
        return commands.run_self_diag()
    if args.health:
        return commands.run_health()
    if args.readiness:
        return commands.run_readiness()
    if args.dashboard:
        return commands.run_dashboard()
    if args.e2e:
        return commands.run_e2e()
    if args.onboarding:
        return commands.run_onboarding()
    if args.update:
        return commands.run_update()

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
        return commands.run_console()
    if args.gradio or args.desktop:
        from app.cli import gui

        launched = gui.try_launch_gradio() if args.gradio else gui.try_launch_pyside()
        return 0 if launched else 2

    # 6) Поведение по умолчанию: Desktop → Web → консоль.
    from app.cli import gui
    from app.cli.probes import health_snapshot

    health_snapshot()
    if gui.try_launch_pyside():
        return 0
    if gui.try_launch_gradio():
        return 0
    return commands.run_console()


if __name__ == "__main__":
    raise SystemExit(main())
