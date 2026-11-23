# -*- coding: utf-8 -*-
"""Окружение RVC (`.venv-rvc`): без него клон голоса физически невозможен.

`rvc-python==0.1.5` требует `numpy<=1.23.5`, основной проект — `>=1.26`.
Поэтому у RVC отдельный интерпретатор, и он должен появляться сам, а не
инструкцией в INSTALL.md. Здесь проверяется: поиск, офлайн-отказ, установка
по команде и отчёт для readiness.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from modules.rvc_manager import venv


def test_missing_venv_is_reported_without_side_effects(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("ZSMM_RVC_PYTHON", raising=False)
    monkeypatch.setattr(venv, "VENV_DIR", tmp_path / "absent")

    report = venv.rvc_venv_report()

    assert report["installed"] is False and report["python"] is None
    assert not (tmp_path / "absent").exists(), "отчёт не должен создавать каталоги"


def test_explicit_python_wins_and_must_be_absolute(tmp_path, monkeypatch) -> None:
    real = Path(sys.executable)
    monkeypatch.setenv("ZSMM_RVC_PYTHON", str(real))
    assert venv.find_rvc_python() == str(real)

    monkeypatch.setenv("ZSMM_RVC_PYTHON", "python")
    assert venv.find_rvc_python() is None, "относительный путь не должен считаться готовым"


def test_offline_refuses_instead_of_downloading(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("ZSMM_RVC_PYTHON", raising=False)
    monkeypatch.setattr(venv, "VENV_DIR", tmp_path / "rvc")

    result = venv.ensure_rvc_venv(allow_download=False)

    assert result == {"ok": False, "python": None, "created": False, "reason": "network disabled"}
    assert not (tmp_path / "rvc").exists()


def test_existing_venv_is_not_reinstalled(tmp_path, monkeypatch) -> None:
    venv_dir = tmp_path / "rvc"
    interpreter = venv_dir / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    interpreter.parent.mkdir(parents=True)
    interpreter.write_text("#!/bin/sh\n", encoding="utf-8")
    monkeypatch.delenv("ZSMM_RVC_PYTHON", raising=False)

    result = venv.ensure_rvc_venv(allow_download=True, venv_dir=venv_dir)

    assert result["ok"] is True and result["created"] is False
    assert result["python"] == str(interpreter)


def test_install_failure_is_reported_not_raised(tmp_path, monkeypatch) -> None:
    """Сломанный pip — это причина в отчёте, а не падение bootstrap."""
    venv_dir = tmp_path / "rvc"
    monkeypatch.delenv("ZSMM_RVC_PYTHON", raising=False)
    monkeypatch.setattr(venv, "_base_python", lambda: ["python3"])

    calls: list[list[str]] = []

    def fake_run(cmd, timeout):
        calls.append(cmd)
        if "venv" in cmd:
            target = Path(cmd[-1])
            (target / "bin").mkdir(parents=True)
            (target / "bin" / "python").write_text("#!/bin/sh\n", encoding="utf-8")
            return 0, ""
        return 1, "ERROR: no matching distribution"

    monkeypatch.setattr(venv, "_run", fake_run)

    result = venv.ensure_rvc_venv(allow_download=True, venv_dir=venv_dir)

    assert result["ok"] is False and result["created"] is True
    assert "no matching distribution" in result["reason"]
    assert any("rvc-python==0.1.5" in " ".join(cmd) for cmd in calls)


def test_supported_python_only() -> None:
    """rvc-python 0.1.5 не собирается на 3.12+: базовый интерпретатор ограничен."""
    assert venv._SUPPORTED_VERSIONS == {"(3, 8)", "(3, 9)", "(3, 10)", "(3, 11)"}


@pytest.mark.parametrize("bad", ["../evil", "a/b", ""])
def test_find_rvc_python_rejects_bad_explicit_path(monkeypatch, bad) -> None:
    monkeypatch.setenv("ZSMM_RVC_PYTHON", bad)
    assert venv.find_rvc_python() is None
