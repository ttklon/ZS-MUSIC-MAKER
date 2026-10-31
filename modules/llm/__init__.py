# -*- coding: utf-8 -*-
"""
modules.llm — единая точка для LLM-провайдеров.

    secrets    шифрованное хранилище ключей
    providers  Ollama / OpenRouter / Grok / Gemini
    fallback   шаблонный текст и адаптер локальной модели
    router     LLMRouter: провайдеры по цепочке + честный fallback

Публичное API:
    LLMRouter().complete(prompt, system="", max_tokens=512, temperature=0.8)
        -> {ok, text, provider, model, tokens, fallback_used, provider_chain, error?}

Ключи никогда не попадают в лог; без ключей и сети роутер отдаёт
`provider="local_template"` с `fallback_used=True`, а не падает.
"""

from __future__ import annotations

import json

from modules.llm.fallback import complete_local_handle  # noqa: F401 - публичный реэкспорт
from modules.llm.fallback import local_fallback_lyrics  # noqa: F401 - публичный реэкспорт
from modules.llm.providers import ProviderResult  # noqa: F401 - публичный реэкспорт
from modules.llm.router import LLMRouter  # noqa: F401 - публичный реэкспорт
from modules.llm.secrets import get_keys_from_env  # noqa: F401 - публичный реэкспорт
from modules.llm.secrets import load_secrets  # noqa: F401 - публичный реэкспорт
from modules.llm.secrets import save_secrets  # noqa: F401 - публичный реэкспорт

__all__ = [
    "LLMRouter",
    "ProviderResult",
    "complete_local_handle",
    "get_keys_from_env",
    "load_secrets",
    "local_fallback_lyrics",
    "save_secrets",
]


def _cli():
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument(
        "--prompt", default="Напиши текст в жанре phonk про ночь и тачки, 16 строк"
    )
    p.add_argument(
        "--system", default="Ты — генератор текстов для программы ZS Music Maker."
    )
    p.add_argument("--theme", default="ночь")
    p.add_argument("--genre", default="phonk")
    p.add_argument("--language", default="ru")
    p.add_argument("--timeout", type=float, default=15.0)
    a = p.parse_args()
    router = LLMRouter(timeout=a.timeout)
    r = router.complete(
        a.prompt, a.system, theme=a.theme, genre=a.genre, language=a.language
    )
    print(
        json.dumps(
            {
                "provider": r.get("provider"),
                "model": r.get("model"),
                "fallback_used": r.get("fallback_used"),
                "chain": r.get("provider_chain"),
                "text_preview": r.get("text", "")[:300],
                "log": router.log,
            },
            ensure_ascii=False,
            indent=2,
        )
    )

