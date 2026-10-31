# -*- coding: utf-8 -*-
"""
app/cli/env.py — корневой контекст CLI: версия/сборка, безопасный вывод,
настройка кодировки консоли Windows.

Единственный источник версии — `version.json` (в установленном колесе —
`app.version_info`). Здесь же решается вечная проблема Windows: консоль
по умолчанию cp866/cp1251 и ломает кириллицу.
"""

from __future__ import annotations

import io
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load_version_info() -> tuple[str, str]:
    # A source checkout uses version.json as its release source of truth.  The
    # wheel ships main.py as a module, where that root-level JSON file is not
    # present, so use the packaged dynamic version as a safe installed fallback.
    default_v = "17.0.0"
    default_b = "wheel-installed"
    try:
        from app.version_info import __version__

        default_v = str(__version__)
    except Exception:
        pass
    try:
        vp = ROOT / "version.json"
        if vp.exists():
            data = json.loads(vp.read_text(encoding="utf-8"))
            return (
                str(data.get("version", default_v)),
                str(data.get("build", default_b)),
            )
    except Exception:
        pass
    return default_v, default_b


class ProjectContext:
    """Версия/сборка/статус проекта — один объект на процесс."""

    def __init__(self) -> None:
        version, build = _load_version_info()
        self.version = version
        self.build = build
        self.status = "GOD MODE 3.0 (Autonomy & Stability)"


ctx = ProjectContext()
VERSION = ctx.version
BUILD = ctx.build


def setup_console_encoding() -> None:
    """UTF-8 не трогаем, cp866 — только как последний шанс для старых консолей."""
    try:
        os.environ.setdefault("PYTHONIOENCODING", "utf-8")
        enc = (getattr(sys.stdout, "encoding", "") or "").lower()
        if enc in ("utf-8", "utf8", "cp65001"):
            return
        try:
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
                sys.stderr.reconfigure(encoding="utf-8", errors="replace")
                return
        except Exception:
            pass
        for encoding in ("utf-8", "cp866"):
            try:
                sys.stdout = io.TextIOWrapper(
                    sys.stdout.buffer,
                    encoding=encoding,
                    errors="replace",
                    line_buffering=True,
                )
                sys.stderr = io.TextIOWrapper(
                    sys.stderr.buffer,
                    encoding=encoding,
                    errors="replace",
                    line_buffering=True,
                )
                return
            except Exception:
                continue
    except Exception:
        pass


def safe_print(msg: str) -> None:
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            sys.stdout.buffer.write((msg + "\n").encode("utf-8", "replace"))
        except Exception:
            pass


def header() -> None:
    safe_print("=" * 64)
    safe_print(f"ZS Music Maker v{ctx.version} — unified entrypoint")
    safe_print(f"Build: {ctx.build}")
    safe_print(f"Status: {ctx.status}")
    safe_print("=" * 64)
