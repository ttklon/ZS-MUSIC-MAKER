# -*- coding: utf-8 -*-
"""
updater/paths.py — где лежит программа, пользовательские данные и бэкапы.

Разделение program vs user data — требование P0.10: обновление программы
никогда не должно затрагивать `%LOCALAPPDATA%\ZS Music Maker`.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def program_dir() -> Path:
    env = os.environ.get("ZSMM_PROGRAM_DIR")
    if env:
        return Path(env)
    # v37 FIX: раньше на win32 всегда возвращался 'C:\Program Files\ZS Music Maker',
    # хотя репо ставится клонированием в ЛЮБУЮ папку. Это приводило к тому, что
    # backup/rollback/install работали с несуществующим каталогом.
    # Теперь: если текущий корень проекта (рядом с updater/) выглядит как установка
    # (есть main.py) — используем ЕГО; 'Program Files' остаётся только для случая,
    # когда updater вызван не из дерева проекта.
    root = Path(__file__).resolve().parents[1]
    if (root / "main.py").exists():
        return root
    if sys.platform == "win32":
        pf = os.environ.get("ProgramFiles", r"C:\Program Files")
        return Path(pf) / "ZS Music Maker"
    return root


def user_data_dir() -> Path:
    env = os.environ.get("ZSMM_USER_DIR")
    if env:
        return Path(env)
    if sys.platform == "win32":
        appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser(r"~\AppData\Local"))
        return Path(appdata) / "ZS Music Maker"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "ZS Music Maker"
    xdg = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
    return Path(xdg) / "zsmm"


def backup_dir() -> Path:
    d = program_dir() / "updater" / "backup"
    d.mkdir(parents=True, exist_ok=True)
    return d


def staging_dir() -> Path:
    d = program_dir() / "updater" / "backup" / "staging"
    d.mkdir(parents=True, exist_ok=True)
    return d


def online_enabled(allow_online: bool = False, settings_path: Path | None = None) -> bool:
    """Allow remote updater traffic only after an explicit user opt-in.

    Та же политика, что и у остального приложения: `app.core.net_policy`.
    """
    from app.core.net_policy import network_allowed

    path = Path(settings_path) if settings_path else program_dir() / "data" / "settings.json"
    return network_allowed(allow_online, path)
