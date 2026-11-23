# -*- coding: utf-8 -*-
"""
app/core/agent_wiring.py — «все ИИ-агенты автономно в каждой функции».

ТЗ требует не «есть модули агентов», а чтобы **каждый** прогон их вызывал:
`trend_scout` (что сейчас в тренде), `sample_hunter` (бесплатные сэмплы под
жанр), `sequential_runner` (одна тяжёлая модель в памяти). Раньше это было
только в `hit_factory.generator`, поэтому бит и вокал шли «сами по себе».

Модуль намеренно маленький и без побочных эффектов: `prepare_run_context`
собирает контекст, `wire_full_agents` проверяет импорты. Всё, что стоит
времени (сеть, скачивание), выполняется только при `allow_online=True`.
"""

from __future__ import annotations

import logging
from typing import Any

_LOG = logging.getLogger(__name__)


def wire_full_agents() -> bool:
    """Проверить, что три агента импортируются. Ничего не качает."""
    try:
        import agents.sample_hunter  # noqa: F401
        import agents.trend_scout  # noqa: F401
        from app.ai.sequential_runner import SequentialAIRunner  # noqa: F401

        return True
    except Exception as exc:  # noqa: BLE001 — отчёт вместо падения прогона
        _LOG.warning("full_agents wiring failed: %s", exc)
        return False


def trend_context(theme: str, allow_online: bool = False) -> dict[str, Any]:
    """Актуальные слова и панчи под тему. Сеть — только если разрешена."""
    try:
        from agents.trend_scout import scout

        data = scout(theme=theme or "лето тачки движ", offline_only=not allow_online)
        return {
            "ok": True,
            "hype_words": list(data.get("hype_words") or [])[:10],
            "punchlines": list(data.get("punchlines") or [])[:5],
            "offline": bool(data.get("offline", True)),
        }
    except Exception as exc:  # noqa: BLE001
        _LOG.debug("trend_scout failed: %s", exc)
        return {"ok": False, "reason": f"{type(exc).__name__}: {exc}"}


def sample_context(genre: str, allow_online: bool = False, limit: int = 3) -> dict[str, Any]:
    """Бесплатные сэмплы под жанр. Лицензионный фильтр — внутри `sample_hunter`."""
    try:
        from agents.sample_hunter import hunt

        data = hunt(query=genre or "drum loop", max_results=limit, allow_online=allow_online)
        results = data.get("results") if isinstance(data, dict) else None
        return {
            "ok": bool(results),
            "count": len(results or []),
            "offline": bool((data or {}).get("offline", True)),
            "reason": "" if results else "в локальном банке нет подходящих сэмплов",
        }
    except Exception as exc:  # noqa: BLE001
        _LOG.debug("sample_hunter failed: %s", exc)
        return {"ok": False, "count": 0, "reason": f"{type(exc).__name__}: {exc}"}


def prepare_run_context(wizard_state: dict[str, Any], allow_online: bool = False) -> dict[str, Any]:
    """Контекст агентов для прогона: тренды + сэмплы + готовность раннера.

    Вызывается пайплайном до стадий: текст получает `trend_notes`, бит —
    понимание, что банк сэмплов проверен. Возвращает словарь, который можно
    положить в `wizard_state` без побочных эффектов.
    """
    theme = str(wizard_state.get("theme") or "")
    genre = str(wizard_state.get("genre") or "")
    trends = trend_context(theme, allow_online)
    samples = sample_context(genre, allow_online)
    wired = wire_full_agents()
    notes = ", ".join(trends.get("hype_words") or [])
    existing = str(wizard_state.get("trend_notes") or "").strip()
    return {
        "wired": wired,
        "trend": trends,
        "samples": samples,
        "trend_notes": notes if notes and not existing else existing,
        "blocked": [
            stage for stage, item in (("trends", trends), ("samples", samples))
            if not item.get("ok")
        ],
    }
