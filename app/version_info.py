"""
ZS Music Maker — app/version_info.py
====================================

Single runtime version source. Source checkouts read canonical ``version.json``;
installed wheels read their distribution metadata because root-level source JSON
is intentionally not installed beside the package.
"""
from __future__ import annotations

import json
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def _source_version() -> str | None:
    version_file = Path(__file__).resolve().parents[1] / "version.json"
    try:
        return str(json.loads(version_file.read_text(encoding="utf-8"))["version"])
    except (OSError, ValueError, KeyError, TypeError):
        return None


def _installed_version() -> str:
    try:
        return version("zs-music-maker")
    except PackageNotFoundError:
        return "0+unknown"


__version__: str = _source_version() or _installed_version()
