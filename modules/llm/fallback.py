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


def _seed_for(theme: str, genre: str, language: str) -> int:
    """Сид, одинаковый в любом процессе.

    `hash()` строк в Python рандомизирован между запусками (`PYTHONHASHSEED`),
    поэтому два прогона с одними и теми же параметрами давали разные тексты.
    sha256 от тех же строк даёт то же число всегда.
    """
    import hashlib

    key = f"{theme}\x00{genre}\x00{language}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(key).digest()[:8], "big")


def _pick_block(rng, pool: list[str], count: int) -> list[str]:
    """Строки блока без повторов.

    `random.choice` этого не гарантирует: в живом прогоне одна и та же строка
    шла дважды подряд («Клуб гудит, басы качают» ×2). Пул короткий, поэтому
    при нехватке строк блок получается короче — это честнее повтора.
    """
    return rng.sample(pool, k=min(count, len(pool)))


def local_fallback_lyrics(
    theme: str, genre: str, language: str = "ru", n_lines: int = 16
) -> str:
    """Собирает шаблонный текст из punch-lib + темы + жанра.

    Один и тот же вход даёт один и тот же текст: это fallback, но он обязан
    быть воспроизводимым, иначе `--seed` не держит обещание детерминизма.
    """
    import random

    pool = PUNCHLINES_RU if language == "ru" else PUNCHLINES_EN
    rng = random.Random(_seed_for(theme, genre, language))
    intro = (
        f"{theme}, {genre}, время идёт"
        if language == "ru"
        else f"{theme}, {genre}, we're on"
    )
    verse1 = _pick_block(rng, pool, 4)
    hook = _pick_block(rng, pool, 4)
    # Второй куплет не повторяет первый: пул короткий, и без этого «куплет 2»
    # дословно повторял строки из первого.
    rest = [line for line in pool if line not in verse1]
    verse2 = _pick_block(rng, rest, 4) if len(rest) >= 2 else _pick_block(rng, pool, 4)
    parts = ["[intro]", intro, "", "[verse 1]", *verse1, "", "[hook]", *hook, "", "[verse 2]", *verse2, "", "[hook]", *hook]
    return "\n".join(parts[: n_lines + 8])


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
