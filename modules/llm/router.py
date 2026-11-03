# -*- coding: utf-8 -*-
"""
modules/llm/router.py — маршрутизация запроса по провайдерам.

Порядок: OpenRouter → Grok → Gemini → Ollama → локальный шаблон.
Перед вызовами делается быстрый preflight (сеть/локальный демон), чтобы
отсутствие интернета не стоило десятков секунд простоя.
"""

from __future__ import annotations

import logging
import os

import time
from typing import Any

from modules.llm.fallback import local_fallback_lyrics
from modules.llm.providers import call_gemini, call_grok, call_ollama, call_openrouter
from modules.llm.secrets import get_keys_from_env


class LLMRouter:
    """Роутер по ТЗ 9.3: OpenRouter → Grok → Gemini → Ollama → local."""

    def __init__(
        self,
        keys: dict[str, str] | None = None,
        ollama_url: str = "http://127.0.0.1:11434",
        timeout: float = 60.0,
        ollama_model: str | None = None,
    ):
        self.keys = keys or get_keys_from_env()
        self.ollama_url = ollama_url
        self.timeout = timeout
        self.ollama_model = ollama_model
        self.log: list[dict[str, Any]] = []

    # v25 (P1): быстрый preflight (<1с). Раньше 4 провайдера по 8с таймауту
    # = до 32с мёртвого простоя, если сети нет / ключей нет. Теперь один
    # socket.connect() решает, стоит ли вообще звонить в облака / локальный
    # Ollama. Состояние не кэшируется: сервер можно запустить во время работы.
    def _preflight(self) -> dict[str, bool]:
        out = {"internet": False, "ollama": False}
        import socket

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.4)
            s.connect(("8.8.8.8", 53))
            s.close()
            out["internet"] = True
        except Exception:
            logging.getLogger(__name__).debug("ignored exception", exc_info=True)
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
            logging.getLogger(__name__).debug("ignored exception", exc_info=True)
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

        # 4. Ollama: choose among locally installed models, never download automatically.
        if pre.get("ollama"):
            selected = os.getenv("ZSMM_OLLAMA_MODEL", "").strip() or self.ollama_model
            selection = None
            if not selected:
                from modules.llm.ollama_adaptive import discover_ollama_model
                selection = discover_ollama_model(self.ollama_url)
                selected = selection.get("model")
            if selected:
                r4 = self._try_provider(
                    "ollama",
                    lambda: call_ollama(
                        prompt, system, model=selected, base_url=self.ollama_url,
                        timeout=float(os.getenv("ZSMM_OLLAMA_TIMEOUT", "600")),
                        max_tokens=max_tokens, temperature=temperature,
                    ),
                )
                chain.append("ollama")
                if r4.ok and r4.text.strip():
                    d = r4.to_dict()
                    d["provider_chain"] = chain
                    d["fallback_used"] = False
                    d["model_selection"] = selection or {"model": selected, "reason": "explicit or preselected"}
                    return d
                errs["ollama"] = r4.error
            else:
                chain.append("ollama_skipped_no_fitting_model")
                errs["ollama"] = (selection or {}).get("reason", "no fitting model")
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
