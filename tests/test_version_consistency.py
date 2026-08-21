# -*- coding: utf-8 -*-
"""ZS Music Maker — единый источник версии (ШАГ 009)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _version_from_pyproject() -> str | None:
    try:
        import tomllib
    except ImportError:
        return None
    try:
        data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    except Exception:
        return None
    return data.get("project", {}).get("version")


def _version_from_app() -> str:
    from app.version_info import __version__

    return __version__


def test_version_json_matches_app_version_info():
    vj = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))["version"]
    assert vj == _version_from_app()


def test_pyproject_static_version_if_present_matches():
    vj = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))["version"]
    pv = _version_from_pyproject()
    if pv is not None:
        assert vj == pv


def test_cli_version_exit_zero():
    r = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "--version"],
        capture_output=True, text=True, timeout=180,
    )
    assert r.returncode == 0
    assert "version" in (r.stdout + r.stderr).lower()


def test_cli_version_shows_config_path():
    r = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "--version"],
        capture_output=True, text=True, timeout=180,
    )
    assert r.returncode == 0
    assert "config" in (r.stdout + r.stderr)


def test_build_id_mentions_version():
    data = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))
    build = data.get("build", "")
    assert build.startswith("v" + data["version"].split(".")[0])
