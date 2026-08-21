# -*- coding: utf-8 -*-
"""ZS Music Maker - app/ai/llm_service.py (v38): обёртка над llama-cpp."""
from __future__ import annotations
import json
from typing import Any, Optional


def complete(handle: Any, system: str, user: str, max_tokens: int = 1024,
             temperature: float = 0.85, top_p: float = 0.95,
             repeat_penalty: float = 1.1) -> str:
    if handle is None:
        return ""
    try:
        res = handle.create_chat_completion(
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            max_tokens=max_tokens, temperature=temperature, top_p=top_p,
            repeat_penalty=repeat_penalty)
        return res["choices"][0]["message"]["content"].strip()
    except Exception:
        try:
            prompt = f"<|system|>\n{system}\n<|user|>\n{user}\n<|assistant|>\n"
            res = handle(prompt, max_tokens=max_tokens, temperature=temperature,
                         top_p=top_p, repeat_penalty=repeat_penalty,
                         stop=["<|user|>", "<|system|>"])
            return res["choices"][0]["text"].strip()
        except Exception:
            return ""


def complete_json(handle: Any, system: str, user: str, max_tokens: int = 2048,
                  temperature: float = 0.4) -> Optional[dict]:
    txt = complete(handle, system, user, max_tokens=max_tokens, temperature=temperature)
    if not txt:
        return None
    s, e = txt.find("{"), txt.rfind("}")
    if s < 0 or e <= s:
        return None
    try:
        return json.loads(txt[s:e + 1])
    except Exception:
        try:
            return json.loads(txt[s:e + 1].replace("'", '"'))
        except Exception:
            return None
