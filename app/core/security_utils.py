# -*- coding: utf-8 -*-
"""
ZS Music Maker — security_utils.py (GOD MODE)
========================================================================
Безопасная работа с данными и сетью.
Заменяет уязвимые urllib и MD5 на SHA-256 и валидированные запросы.
"""

import hashlib
import os
import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests

_SECRET_PATTERNS = (
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?:sk|api)[_-][A-Za-z0-9_-]{16,}", re.IGNORECASE),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{16,}", re.IGNORECASE),
)


def safe_identifier(value: str, *, fallback: str = "unknown", max_length: int = 96) -> str:
    """Сделать value безопасным single path component без `..` или separators."""
    raw = (value or "").strip()
    if not raw or raw in {".", ".."} or ".." in raw or "/" in raw or "\\" in raw:
        return fallback
    normalized = re.sub(r"[^A-Za-z0-9а-яА-ЯёЁ_-]+", "_", raw).strip("._-")
    return normalized[:max_length] or fallback


def safe_child_path(root: str | Path, identifier: str) -> Path:
    """Вернуть path под root либо отклонить traversal/absolute component."""
    base = Path(root).resolve()
    child = base / safe_identifier(identifier)
    if child.parent != base:
        raise ValueError("unsafe child path")
    return child


def redact_secrets(text: str) -> str:
    """Заменить распространённые access-token формы перед записью в log/UI."""
    redacted = str(text)
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def safe_hash(data: str) -> str:
    """Безопасное хеширование через SHA-256 (вместо MD5)."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def download_file(url: str, target_path: str, timeout: int = 30) -> bool:
    """
    Безопасная загрузка файла с валидацией схемы и таймаутом.
    Заменяет уязвимый urllib.request.urlretrieve.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")

    try:
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False

def get_json(url: str, timeout: int = 15) -> Optional[dict]:
    """Безопасное получение JSON через requests."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return None
        
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None
