# -*- coding: utf-8 -*-
"""
modules/llm/secrets.py — хранилище API-ключей LLM-провайдеров.

Ключи шифруются `cryptography.fernet` мастер-паролем и лежат в
`data/secrets.enc`; ключи из окружения используются для CI и не логируются.
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    HAS_CRYPTO = True
except Exception:  # noqa: BLE001 - без cryptography остаётся только ENV
    HAS_CRYPTO = False

ROOT = Path(__file__).resolve().parents[1]

SECRETS_FILE = ROOT / "data" / "secrets.enc"


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
