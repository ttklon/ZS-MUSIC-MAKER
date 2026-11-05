# -*- coding: utf-8 -*-
"""
modules/llm/fallback.py — локальные фоллбеки LLM-слоя.

Шаблонный текст из punch-библиотеки (последний рубеж роутера) и адаптер
локальной llama-совместимой модели к общему устойчивому сервису.
"""

from __future__ import annotations

from typing import Any


PUNCHLINES_RU = [
    "Ночь, движ, тачка — вот моя жизнь",
    "Мы летим по трассе, город спит",
    "Клуб гудит, басы качают",
    "Танцпол горит, мы на волне",
    "Огни фар режут темноту",
    "Я не остановлюсь, пока не взорву",
    "Ставки высоки, но мы играем в свою игру",
    "Каждый удар кика — как выстрел в грудь",
    "Мы пишем историю каждой ночью",
    "Скорость — это свобода, ты чувствуешь",
]


PUNCHLINES_EN = [
    "Neon dreams and midnight lights",
    "Speeding through the empty streets",
    "Bass drops harder than my heart",
    "Dance floor's alive tonight",
    "We ride the wave until sunrise",
]


def local_fallback_lyrics(
    theme: str, genre: str, language: str = "ru", n_lines: int = 16
) -> str:
    """Собирает шаблонный текст из punch-lib + темы + жанра."""
    pool = PUNCHLINES_RU if language == "ru" else PUNCHLINES_EN
    lines: list[str] = []
    lines.append("[intro]")
    lines.append(
        f"{theme}, {genre}, время идёт"
        if language == "ru"
        else f"{theme}, {genre}, we're on"
    )
    lines.append("")
    lines.append("[verse 1]")
    import random

    r = random.Random(hash((theme, genre, language)) & 0xFFFF)
    for _ in range(4):
        lines.append(r.choice(pool))
    lines.append("")
    lines.append("[hook]")
    for _ in range(4):
        lines.append(r.choice(pool))
    lines.append("")
    lines.append("[verse 2]")
    for _ in range(4):
        lines.append(r.choice(pool))
    lines.append("")
    lines.append("[hook]")
    for _ in range(4):
        lines.append(r.choice(pool))
    return "\n".join(lines[: n_lines + 8])


def complete_local_handle(
    handle: Any,
    prompt: str,
    system: str = "",
    max_tokens: int = 512,
    temperature: float = 0.8,
    timeout_sec: float = 600.0,
) -> dict[str, Any]:
    """Delegate local llama-compatible completion to the shared resilient service.

    This adapter intentionally returns failure metadata rather than a template
    fallback: callers can decide whether a local model failure should fall
    through to the existing provider router or their domain-specific fallback.
    """
    from app.ai import llm_service

    report = llm_service.complete_with_report(
        handle,
        system,
        prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        timeout_sec=timeout_sec,
    )
    return {
        "ok": report.ok,
        "text": report.text,
        "provider": "local_llm_service",
        "model": "llama_compatible_handle",
        "tokens": len(report.text.split()),
        "fallback_used": False,
        "provider_chain": ["local_llm_service"],
        "error": report.error,
        "attempts": report.attempts,
        "circuit_open": report.circuit_open,
    }
