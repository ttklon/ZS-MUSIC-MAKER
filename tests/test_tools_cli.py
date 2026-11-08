from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = (
    "ast_dead_imports.py",
    "audio_golden_metrics.py",
    "audit_data_inventory.py",
    "audit_honesty.py",
    "fallback_audit.py",
    "generate_audio_goldens.py",
    "genre_validator.py",
    "gitignore_guard.py",
    "pull_ai_models.py",
    "samples_audit.py",
    "e2e.py",
    "smoke_audio.py",
    "smoke_god.py",
)


@pytest.mark.parametrize("tool", TOOLS)
def test_tool_help_is_safe_and_successful(tool: str) -> None:
    """A maintenance tool must show help before it creates reports or runs audio work."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / tool), "--help"],
        cwd=ROOT,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    # На Windows консоль может отдать кириллицу в cp1251, и `text=True`
    # возвращает None вместо строки — это не пустой --help, а кодировка.
    assert "usage:" in _output(result).lower()


def _output(result: subprocess.CompletedProcess) -> str:
    """stdout инструмента строкой: None или байты после сбоя декодирования — не повод падать."""
    out = result.stdout
    if isinstance(out, bytes):
        out = out.decode("utf-8", "replace")
    return out or ""


def test_readiness_package_help_is_safe() -> None:
    """Пакет readiness запускается как модуль и печатает usage."""
    result = subprocess.run(
        [sys.executable, "-m", "tools.readiness", "--help"],
        cwd=ROOT,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert "usage:" in _output(result).lower()
