# -*- coding: utf-8 -*-
"""
modules/llm/providers.py — HTTP-провайдеры LLM.

Ollama (локально), OpenRouter, Grok (xAI), Gemini. Каждый вызов возвращает
`ProviderResult` с честным `ok`/`error`, без исключений наружу.
"""

from __future__ import annotations

import logging

try:
    import requests

    HAS_REQ = True
except Exception:  # noqa: BLE001 - без requests работают только локальные роли
    HAS_REQ = False


class ProviderResult:
    __slots__ = ("error", "model", "ok", "provider", "raw", "text", "tokens")

    def __init__(
        self, ok, text="", model="", tokens=0, provider="", error=None, raw=None
    ):
        self.ok = ok
        self.text = text
        self.model = model
        self.tokens = tokens
        self.provider = provider
        self.error = error
        self.raw = raw

    def to_dict(self):
        return {
            "ok": self.ok,
            "text": self.text,
            "model": self.model,
            "tokens": self.tokens,
            "provider": self.provider,
            "error": self.error,
        }


def call_ollama(
    prompt: str,
    system: str = "",
    model: str = "llama3.2:3b",
    base_url: str = "http://127.0.0.1:11434",
    timeout: float = 60.0,
    max_tokens: int = 512,
    temperature: float = 0.8,
) -> ProviderResult:
    if not HAS_REQ:
        return ProviderResult(False, provider="ollama", error="requests_missing")
    try:
        r = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": model,
                "prompt": (system + "\n\n" + prompt).strip(),
                "stream": False,
                "keep_alive": 0,
                "options": {"num_ctx": 4096, "num_predict": max_tokens, "temperature": temperature},
            },
            timeout=timeout,
        )
        if r.status_code != 200:
            return ProviderResult(
                False, provider="ollama", model=model, error=f"http_{r.status_code}"
            )
        j = r.json()
        return ProviderResult(
            True,
            text=j.get("response", ""),
            model=model,
            tokens=j.get("eval_count", 0),
            provider="ollama",
            raw=j,
        )
    except requests.exceptions.ConnectionError:
        return ProviderResult(
            False, provider="ollama", model=model, error="connection_refused"
        )
    except Exception as e:
        return ProviderResult(
            False, provider="ollama", model=model, error=type(e).__name__
        )


def call_openrouter(
    prompt: str,
    system: str = "",
    api_key: str = "",
    model: str = "meta-llama/llama-3.1-70b-instruct:free",
    timeout: float = 60.0,
) -> ProviderResult:
    if not HAS_REQ:
        return ProviderResult(False, provider="openrouter", error="requests_missing")
    if not api_key:
        return ProviderResult(
            False, provider="openrouter", model=model, error="no_api_key"
        )
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": ([{"role": "system", "content": system}] if system else [])
                + [{"role": "user", "content": prompt}],
            },
            timeout=timeout,
        )
        if r.status_code != 200:
            return ProviderResult(
                False, provider="openrouter", model=model, error=f"http_{r.status_code}"
            )
        j = r.json()
        text = j["choices"][0]["message"]["content"]
        tokens = j.get("usage", {}).get("total_tokens", 0)
        return ProviderResult(
            True, text=text, model=model, tokens=tokens, provider="openrouter", raw=j
        )
    except Exception as e:
        return ProviderResult(
            False, provider="openrouter", model=model, error=type(e).__name__
        )


def call_grok(
    prompt: str,
    system: str = "",
    api_key: str = "",
    model: str = "grok-2-latest",
    timeout: float = 60.0,
) -> ProviderResult:
    if not HAS_REQ:
        return ProviderResult(False, provider="grok", error="requests_missing")
    if not api_key:
        return ProviderResult(False, provider="grok", model=model, error="no_api_key")
    try:
        r = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": ([{"role": "system", "content": system}] if system else [])
                + [{"role": "user", "content": prompt}],
            },
            timeout=timeout,
        )
        if r.status_code != 200:
            return ProviderResult(
                False, provider="grok", model=model, error=f"http_{r.status_code}"
            )
        j = r.json()
        text = j["choices"][0]["message"]["content"]
        tokens = j.get("usage", {}).get("total_tokens", 0)
        return ProviderResult(
            True, text=text, model=model, tokens=tokens, provider="grok", raw=j
        )
    except Exception as e:
        return ProviderResult(
            False, provider="grok", model=model, error=type(e).__name__
        )


def call_gemini(
    prompt: str,
    system: str = "",
    api_key: str = "",
    model: str = "gemini-1.5-flash",
    timeout: float = 60.0,
) -> ProviderResult:
    if not HAS_REQ:
        return ProviderResult(False, provider="gemini", error="requests_missing")
    if not api_key:
        return ProviderResult(False, provider="gemini", model=model, error="no_api_key")
    try:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={api_key}"
        )
        body = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": (system + "\n\n" + prompt).strip()}],
                }
            ]
        }
        r = requests.post(url, json=body, timeout=timeout)
        if r.status_code != 200:
            return ProviderResult(
                False, provider="gemini", model=model, error=f"http_{r.status_code}"
            )
        j = r.json()
        text = ""
        try:
            text = j["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            logging.getLogger(__name__).debug("ignored exception", exc_info=True)
        return ProviderResult(
            True,
            text=text,
            model=model,
            tokens=len(text.split()),
            provider="gemini",
            raw=j,
        )
    except Exception as e:
        return ProviderResult(
            False, provider="gemini", model=model, error=type(e).__name__
        )
