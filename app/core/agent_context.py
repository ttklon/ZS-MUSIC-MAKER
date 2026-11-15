# -*- coding: utf-8 -*-
"""
app/core/agent_context.py — подключение ИИ-агентов к обычному прогону.

Вынесено из `orchestrator.py`, чтобы фасад пайплайна не превышал лимит
400 строк: здесь только связка «рецепт → контекст агентов», а не стадии.

Сеть — по политике (`app/core/net_policy.py`): офлайн-прогон не стучится
наружу, тренды берутся из встроенного словаря 2026.
"""

from __future__ import annotations

import logging
from typing import Any

_LOG = logging.getLogger(__name__)


def _attach_agent_context(recipe: dict[str, Any]) -> dict[str, Any]:
    """Подключить trend_scout + sample_hunter к текущему прогону.

    Не блокирует пайплайн: если агенты недоступны, причина остаётся в отчёте
    (`agent_context.blocked`), а трек всё равно собирается. Сеть — по политике
    (`network.online` / `--online`), как и у остальных сетевых шагов.
    """
    try:
        from app.core.agent_wiring import prepare_run_context
        from app.core.net_policy import network_allowed

        context = prepare_run_context(dict(recipe), allow_online=network_allowed())
    except Exception as exc:  # noqa: BLE001 — агенты не должны ронять прогон
        _LOG.debug("agent context failed: %s", exc)
        context = {"wired": False, "blocked": ["agents"], "reason": f"{type(exc).__name__}: {exc}"}
    if context.get("trend_notes") and not recipe.get("trend_notes"):
        recipe["trend_notes"] = context["trend_notes"]
    recipe["agent_context"] = context
    return context
