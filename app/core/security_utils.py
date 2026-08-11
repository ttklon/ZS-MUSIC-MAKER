# -*- coding: utf-8 -*-
"""
ZS Music Maker — security_utils.py (GOD MODE)
========================================================================
Безопасная работа с данными и сетью.
Заменяет уязвимые urllib и MD5 на SHA-256 и валидированные запросы.
"""

import hashlib
import requests
import os
from typing import Optional
from urllib.parse import urlparse

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
