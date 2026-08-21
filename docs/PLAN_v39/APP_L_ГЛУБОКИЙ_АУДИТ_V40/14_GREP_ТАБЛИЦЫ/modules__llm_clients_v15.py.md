# grep-таблицы `modules/llm_clients_v15.py`

## `import` — 14 совпадений
```
   19 | from __future__ import annotations
   21 | import base64
   22 | import json
   23 | import os
   24 | import time
   25 | from pathlib import Path
   26 | from typing import Any
   29 |     import requests
   36 |     from cryptography.fernet import Fernet
   37 |     from cryptography.hazmat.primitives import hashes
   38 |     from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
  340 |     import random
  387 |         import socket
  545 |     import argparse
```

## `print` — 1 совпадений
```
  563 |     print(
```

## `except` — 11 совпадений
```
   32 | except Exception:
   41 | except Exception:
   79 |     except Exception:
  159 |     except requests.exceptions.ConnectionError:
  163 |     except Exception as e:
  206 |     except Exception as e:
  247 |     except Exception as e:
  286 |         except Exception:
  296 |     except Exception as e:
  395 |         except Exception:
  406 |         except Exception:
```

## `try` — 10 совпадений
```
   28 | try:
   35 | try:
   74 |     try:
  136 |     try:
  182 |     try:
  223 |     try:
  264 |     try:
  284 |         try:
  389 |         try:
  397 |         try:
```

## `def` — 16 совпадений
```
   52 | def _derive_key(master_password: str, salt: bytes = b"zsmm-v15-salt") -> bytes:
   61 | def save_secrets(secrets: dict[str, str], master_password: str) -> bool:
   71 | def load_secrets(master_password: str) -> dict[str, str] | None:
   83 | def get_keys_from_env() -> dict[str, str]:
  105 |     def __init__(
  116 |     def to_dict(self):
  127 | def call_ollama(
  169 | def call_openrouter(
  212 | def call_grok(
  253 | def call_gemini(
  326 | def local_fallback_lyrics(
  366 |     def __init__(
  383 |     def _preflight(self) -> dict[str, bool]:
  411 |     def _try_provider(self, name: str, fn):
  425 |     def complete(
  544 | def _cli():
```

## `class` — 2 совпадений
```
  102 | class ProviderResult:
  363 | class LLMRouter:
```

## `raise` — 1 совпадений
```
   54 |         raise RuntimeError("cryptography not installed")
```

## `return` — 37 совпадений
```
   58 |     return base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
   63 |         return False
   68 |     return True
   73 |         return None
   78 |         return json.loads(data.decode())
   80 |         return None
   96 |     return keys
  117 |         return {
  135 |         return ProviderResult(False, provider="ollama", error="requests_missing")
  147 |             return ProviderResult(
  151 |         return ProviderResult(
  160 |         return ProviderResult(
  164 |         return ProviderResult(
  177 |         return ProviderResult(False, provider="openrouter", error="requests_missing")
  179 |         return ProviderResult(
  197 |             return ProviderResult(
  203 |         return ProviderResult(
  207 |         return ProviderResult(
  220 |         return ProviderResult(False, provider="grok", error="requests_missing")
  222 |         return ProviderResult(False, provider="grok", model=model, error="no_api_key")
  238 |             return ProviderResult(
  244 |         return ProviderResult(
  248 |         return ProviderResult(
  261 |         return ProviderResult(False, provider="gemini", error="requests_missing")
  263 |         return ProviderResult(False, provider="gemini", model=model, error="no_api_key")
  279 |             return ProviderResult(
  288 |         return ProviderResult(
  297 |         return ProviderResult(
  357 |     return "\n".join(lines[: n_lines + 8])
  385 |             return LLMRouter._preflight_cache
  409 |         return out
  423 |         return r
  457 |                     return d
  476 |                     return d
  498 |                     return d
  520 |                 return d
  529 |         return {
```

## `if` — 27 совпадений
```
   53 |     if not HAS_CRYPTO:
   62 |     if not HAS_CRYPTO:
   72 |     if not HAS_CRYPTO or not SECRETS_FILE.exists():
   94 |         if v:
  134 |     if not HAS_REQ:
  146 |         if r.status_code != 200:
  176 |     if not HAS_REQ:
  178 |     if not api_key:
  196 |         if r.status_code != 200:
  219 |     if not HAS_REQ:
  221 |     if not api_key:
  237 |         if r.status_code != 200:
  260 |     if not HAS_REQ:
  262 |     if not api_key:
  278 |         if r.status_code != 200:
  335 |         if language == "ru"
  384 |         if LLMRouter._preflight_cache is not None:
  440 |         if pre.get("internet"):
  442 |             if self.keys.get("openrouter"):
  453 |                 if r1.ok and r1.text.strip():
  464 |             if self.keys.get("grok"):
  472 |                 if r2.ok and r2.text.strip():
  483 |             if self.keys.get("gemini"):
  494 |                 if r3.ok and r3.text.strip():
  508 |         if pre.get("ollama"):
  516 |             if r4.ok and r4.text.strip():
  579 | if __name__ == "__main__":
```

## `for` — 5 совпадений
```
   86 |     for env_name, key_name in (
  343 |     for _ in range(4):
  347 |     for _ in range(4):
  351 |     for _ in range(4):
  355 |     for _ in range(4):
```

## `requests` — 5 совпадений
```
  137 |         r = requests.post(
  159 |     except requests.exceptions.ConnectionError:
  183 |         r = requests.post(
  224 |         r = requests.post(
  277 |         r = requests.post(url, json=body, timeout=timeout)
```
