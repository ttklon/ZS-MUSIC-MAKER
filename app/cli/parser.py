# -*- coding: utf-8 -*-
"""
app/cli/parser.py — описание аргументов командной строки.

Один парсер, один источник правды о флагах: каждый флаг, объявленный здесь,
обязан иметь обработчик в `app.cli.commands` — «мёртвых» флагов нет.
"""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="ZS Music Maker — Professional AI Music Production Station"
    )
    parser.add_argument("--god", action="store_true", help="Launch the ULTIMATE GOD MODE pipeline")
    parser.add_argument("--async-mode", action="store_true", help="Launch parallel async pipeline")
    parser.add_argument("--genre", type=str, default="drift_phonk", help="Target genre (100+ available)")
    parser.add_argument("--theme", type=str, default="drift_phonk", help="Target theme/mood")
    parser.add_argument("--list-genres", action="store_true", help="Show all available genres")
    parser.add_argument("--smoke", action="store_true", help="Run quality smoke tests")
    parser.add_argument("--self-diag", action="store_true", help="Run system self-diagnostics")
    parser.add_argument("--health", action="store_true", help="Check system health and GPU")
    parser.add_argument("--version", "-V", action="store_true", help="Show version info")
    parser.add_argument("--gradio", action="store_true", help="Launch Web UI (Gradio)")
    parser.add_argument("--desktop", action="store_true", help="Launch Desktop UI (PySide6)")
    parser.add_argument("--run", action="store_true", help="Run the full classic pipeline without GUI")
    parser.add_argument("--dry-run", action="store_true", help="Run pipeline in dry-run (no heavy deps)")
    parser.add_argument("--seed", type=int, default=None, help="Deterministic seed (same seed => identical beat/artefacts)")
    parser.add_argument("--resume", action="store_true", help="Disabled: legacy artifact reuse was not verified")
    parser.add_argument("--only", type=str, default="", help="Comma-separated stages to run (see --list-stages)")
    parser.add_argument("--dashboard", action="store_true", help="Show KPI dashboard")
    parser.add_argument("--e2e", action="store_true", help="Run real end-to-end test")
    parser.add_argument("--onboarding", action="store_true", help="Run voice onboarding CLI")
    parser.add_argument("--readiness", action="store_true", help="Compute readiness percent")
    parser.add_argument("--console", action="store_true", help="Force console REPL mode (no GUI)")
    parser.add_argument("--ai", action="store_true", help="Launch AI GOD MODE 4.0 (sequential AI stack)")
    parser.add_argument("--ai-status", action="store_true", help="Show AI model registry & availability")
    parser.add_argument("--ai-pull", type=str, default="", help="Pull one AI model role (or 'all')")
    parser.add_argument("--dossier-artist", type=str, default="", help="Artist name/slug for dossier")
    parser.add_argument("--dossier-add", type=str, default="", help="Add local folder source")
    parser.add_argument("--dossier-build", action="store_true", help="Run full AI dossier build (heavy)")
    parser.add_argument("--score", type=str, default="", help="Score a mastered WAV and print hit-score breakdown")
    parser.add_argument("--update", action="store_true", help="Check Git update status without applying changes")
    parser.add_argument("--list-stages", action="store_true", help="Show stage keys usable with --only")
    # --- HIT FACTORY (автономная фабрика хитов, бесплатно, нероншно) ---
    parser.add_argument("--hit-factory", action="store_true", help="Автономная фабрика хитов (бесплатно): генерит 1..N треков с эволюцией по hit_score")
    parser.add_argument("--hit-count", type=int, default=1, help="Сколько хитов генерить в батче (1..100)")
    parser.add_argument("--hit-genre", type=str, default="", help="Фиксированный жанр для фабрики (пусто = рандом хитовый)")
    parser.add_argument("--hit-theme", type=str, default="", help="Фиксированная тема (пусто = авто из трендов 2026)")
    parser.add_argument("--hit-seed", type=int, default=None, help="Базовый seed для детерминизма фабрики")
    parser.add_argument("--hit-duration", type=int, default=None, help="Длительность хита сек (65/90/120)")
    parser.add_argument("--hit-min-score", type=float, default=68.0, help="Порог hit_score для эволюции (68=solid, 82=chart_ready)")
    parser.add_argument("--hit-no-evolve", action="store_true", help="Выключить эволюцию (одна попытка на трек)")
    return parser
