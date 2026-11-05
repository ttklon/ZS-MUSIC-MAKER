# -*- coding: utf-8 -*-
"""
updater/archive.py — проверка пакета и резервные копии перед обновлением.

Оставляем последние три бэкапа: этого достаточно для отката и это не даёт
каталогу обновлений расти без границы.
"""

from __future__ import annotations

import hashlib
import os
import time
import zipfile
from pathlib import Path
from typing import Any

from updater.paths import backup_dir, program_dir


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_zip(zip_path: Path, expected_sha256: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"ok": False, "sha256": None, "size": 0, "checks": {}}
    p = Path(zip_path)
    if not p.exists():
        result["reason"] = "zip not found"
        return result
    result["size"] = p.stat().st_size
    if result["size"] < 1024:
        result["reason"] = "zip too small (<1KB)"
        return result
    if result["size"] > 5 * 1024**3:
        result["reason"] = "zip too large (>5GB)"
        return result
    sha = compute_sha256(p)
    result["sha256"] = sha
    result["checks"]["sha256_computed"] = True
    if expected_sha256:
        if sha.lower() != expected_sha256.lower():
            result["reason"] = "sha256 mismatch"
            return result
        result["checks"]["sha256_match"] = True

    try:
        with zipfile.ZipFile(str(p), "r") as z:
            names = set(z.namelist())
    except zipfile.BadZipFile:
        result["reason"] = "corrupted zip"
        return result

    # v37 FIX: раньше verify требовал TZ.txt/PROMPT.txt — этих файлов НЕТ
    # в репозитории, поэтому updater отвергал ЛЮБОЙ реальный дистрибутив.
    # Проверяем реальные маркеры проекта: main.py, version.json, modules/.
    has_main = any(n.endswith("main.py") and not n.startswith("docs/") for n in names)
    has_version = any(n.endswith("version.json") for n in names)
    has_modules = any(n.startswith("modules/") and n.endswith(".py") for n in names)
    result["checks"]["has_main_py"] = has_main
    result["checks"]["has_version_json"] = has_version
    result["checks"]["has_modules"] = has_modules
    if not (has_main and has_version and has_modules):
        result["reason"] = "zip missing required files: main.py/version.json/modules/"
        return result

    result["ok"] = True
    return result


def make_backup(reason: str = "pre_update") -> Path | None:
    src = program_dir()
    if not src.exists():
        return None
    ts = time.strftime("%Y%m%d_%H%M%S")
    dst = backup_dir() / f"backup_{ts}_{reason}.zip"
    with zipfile.ZipFile(str(dst), "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(src):
            if "updater/backup" in root.replace("\\", "/"):
                continue
            if "__pycache__" in root:
                continue
            for f in files:
                fp = Path(root) / f
                try:
                    z.write(str(fp), fp.relative_to(src))
                except Exception:
                    pass
    prune_old_backups(keep=3)
    return dst


def prune_old_backups(keep: int = 3) -> list[Path]:
    bd = backup_dir()
    backups = sorted(
        bd.glob("backup_*.zip"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    removed = []
    for old in backups[keep:]:
        try:
            old.unlink()
            removed.append(old)
        except Exception:
            pass
    return removed


def list_backups() -> list[dict[str, Any]]:
    bd = backup_dir()
    return [
        {"path": str(p), "size": p.stat().st_size, "mtime": p.stat().st_mtime}
        for p in sorted(
            bd.glob("backup_*.zip"), key=lambda x: x.stat().st_mtime, reverse=True
        )
    ]
