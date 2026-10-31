"""
ZS Music Maker v15 — modules/llm.py
==============================================================
Единая точка для LLM-провайдеров: Ollama (локально) → OpenRouter →
Grok (xAI) → Gemini → LOCAL_FALLBACK (шаблоны + punch-lib).

TZ раздел 9 (LLM модуль) и раздел 13 (fallback).

Ключи шифруются `cryptography.fernet` мастер-паролем; хранятся в
`data/secrets.enc`. Ключи никогда не попадают в лог.

Публичное API:
    LLMRouter().complete(prompt: str, system: str = "",
                         max_tokens=512, temperature=0.8) -> dict
        Возвращает {ok, text, provider, model, tokens, fallback_used,
                    provider_chain: [...], error?}
"""

from __future__ import annotations

import base64
import json
import os
import time
from pathlib import Path
from typing import Any

try:
    import requests

    HAS_REQ = True
except Exception:
    HAS_REQ = False

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    HAS_CRYPTO = True
except Exception:
    HAS_CRYPTO = False


ROOT = Path(__file__).resolve().parents[1]
SECRETS_FILE = ROOT / "data" / "secrets.enc"
# v22: ленивое создание (не при импорте)

# ------------------------------------------------------------ secret store


def _derive_key(master_password: str, salt: bytes = b"zsmm-v15-salt") -> bytes:
    if not HAS_CRYPTO:
        raise RuntimeError("cryptography not installed")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(), length=32, salt=salt, iterations=200_000
    )
    return base64.urlsafe_b64encode(kdf.derive(master_password.encode()))


def save_secrets(secrets: dict[str, str], master_password: str) -> bool:
    if not HAS_CRYPTO:
        return False
    key = _derive_key(master_password)
    f = Fernet(key)
    data = f.encrypt(json.dumps(secrets, ensure_ascii=False).encode())
    SECRETS_FILE.write_bytes(data)
    return True


def load_secrets(master_password: str) -> dict[str, str] | None:
    if not HAS_CRYPTO or not SECRETS_FILE.exists():
        return None
    try:
        key = _derive_key(master_password)
        f = Fernet(key)
        data = f.decrypt(SECRETS_FILE.read_bytes())
        return json.loads(data.decode())
    except Exception:
        return None


def get_keys_from_env() -> dict[str, str]:
    """Собирает ключи из ENV (для CI / автотестов, не для UI)."""
    keys = {}
    for env_name, key_name in (
        ("OPENROUTER_API_KEY", "openrouter"),
        ("XAI_API_KEY", "grok"),
        ("GROK_API_KEY", "grok"),
        ("GEMINI_API_KEY", "gemini"),
        ("GOOGLE_API_KEY", "gemini"),
    ):
        v = os.environ.get(env_name)
        if v:
            keys[key_name] = v
    return keys


# ----------------------------------------------------------- providers


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
            pass
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


# --------------------------------------------------------- local fallback

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


# -------------------------------------------------------------- Shared local adapter


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


# -------------------------------------------------------------- Router


class LLMRouter:
    """Роутер по ТЗ 9.3: OpenRouter → Grok → Gemini → Ollama → local."""

    def __init__(
        self,
        keys: dict[str, str] | None = None,
        ollama_url: str = "http://127.0.0.1:11434",
        timeout: float = 60.0,
    ):
        self.keys = keys or get_keys_from_env()
        self.ollama_url = ollama_url
        self.timeout = timeout
        self.log: list[dict[str, Any]] = []

    # v25 (P1): быстрый preflight (<1с). Раньше 4 провайдера по 8с таймауту
    # = до 32с мёртвого простоя, если сети нет / ключей нет. Теперь один
    # socket.connect() решает, стоит ли вообще звонить в облака / локальный
    # Ollama. Кэшируется на уровне класса.
    _preflight_cache: dict[str, bool] | None = None

    def _preflight(self) -> dict[str, bool]:
        if LLMRouter._preflight_cache is not None:
            return LLMRouter._preflight_cache
        out = {"internet": False, "ollama": False}
        import socket

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.4)
            s.connect(("8.8.8.8", 53))
            s.close()
            out["internet"] = True
        except Exception:
            pass
        try:
            parts = self.ollama_url.split("://", 1)[-1].split(":")
            host = parts[0]
            port = int(parts[1].split("/")[0]) if len(parts) > 1 else 11434
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.4)
            s.connect((host, port))
            s.close()
            out["ollama"] = True
        except Exception:
            pass
        LLMRouter._preflight_cache = out
        return out

    def _try_provider(self, name: str, fn):
        t0 = time.time()
        r = fn()
        dt = round(time.time() - t0, 3)
        entry = {
            "provider": name,
            "ok": r.ok,
            "error": r.error,
            "model": r.model,
            "duration_sec": dt,
        }
        self.log.append(entry)
        return r

    def complete(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 512,
        temperature: float = 0.8,
        theme: str = "",
        genre: str = "phonk",
        language: str = "ru",
    ) -> dict[str, Any]:
        chain = []
        # v25 (P1): preflight — не звоним куда не надо
        pre = self._preflight()
        errs = {"openrouter": None, "grok": None, "gemini": None, "ollama": None}

        if pre.get("internet"):
            # 1. OpenRouter (только если есть ключ)
            if self.keys.get("openrouter"):
                r1 = self._try_provider(
                    "openrouter",
                    lambda: call_openrouter(
                        prompt,
                        system,
                        self.keys.get("openrouter", ""),
                        timeout=self.timeout,
                    ),
                )
                chain.append("openrouter")
                if r1.ok and r1.text.strip():
                    d = r1.to_dict()
                    d["provider_chain"] = chain
                    d["fallback_used"] = False
                    return d
                errs["openrouter"] = r1.error
            else:
                chain.append("openrouter_skipped_no_key")
                errs["openrouter"] = "no_api_key"

            # 2. Grok
            if self.keys.get("grok"):
                r2 = self._try_provider(
                    "grok",
                    lambda: call_grok(
                        prompt, system, self.keys.get("grok", ""), timeout=self.timeout
                    ),
                )
                chain.append("grok")
                if r2.ok and r2.text.strip():
                    d = r2.to_dict()
                    d["provider_chain"] = chain
                    d["fallback_used"] = False
                    return d
                errs["grok"] = r2.error
            else:
                chain.append("grok_skipped_no_key")
                errs["grok"] = "no_api_key"

            # 3. Gemini
            if self.keys.get("gemini"):
                r3 = self._try_provider(
                    "gemini",
                    lambda: call_gemini(
                        prompt,
                        system,
                        self.keys.get("gemini", ""),
                        timeout=self.timeout,
                    ),
                )
                chain.append("gemini")
                if r3.ok and r3.text.strip():
                    d = r3.to_dict()
                    d["provider_chain"] = chain
                    d["fallback_used"] = False
                    return d
                errs["gemini"] = r3.error
            else:
                chain.append("gemini_skipped_no_key")
                errs["gemini"] = "no_api_key"
        else:
            chain.append("cloud_skipped_no_internet")
            errs["openrouter"] = errs["grok"] = errs["gemini"] = "no_internet"

        # 4. Ollama (локально) — только если порт живёт
        if pre.get("ollama"):
            r4 = self._try_provider(
                "ollama",
                lambda: call_ollama(
                    prompt, system, base_url=self.ollama_url, timeout=self.timeout
                ),
            )
            chain.append("ollama")
            if r4.ok and r4.text.strip():
                d = r4.to_dict()
                d["provider_chain"] = chain
                d["fallback_used"] = False
                return d
            errs["ollama"] = r4.error
        else:
            chain.append("ollama_skipped_no_local_daemon")
            errs["ollama"] = "no_local_daemon"

        # 5. LOCAL FALLBACK (template)
        text = local_fallback_lyrics(theme or "движение", genre, language)
        chain.append("local_template")
        return {
            "ok": True,
            "text": text,
            "provider": "local_template",
            "model": "punch_lib_v1",
            "tokens": len(text.split()),
            "provider_chain": chain,
            "fallback_used": True,
            "error": errs,
        }


# -------------------------------------------------------------- CLI


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


if __name__ == "__main__":
    _cli()
