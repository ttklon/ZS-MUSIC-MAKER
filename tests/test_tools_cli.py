from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = (
    "ab_compare.py",
    "ast_dead_imports.py",
    "audio_golden_metrics.py",
    "audit_data_inventory.py",
    "deep_audit_v40.py",
    "deep_audit_v40_expand.py",
    "deep_audit_v40_report.py",
    "fallback_audit.py",
    "generate_audio_goldens.py",
    "genre_validator.py",
    "lazy_dirs_patch.py",
    "p0_truth_test.py",
    "pull_ai_models.py",
    "readiness.py",
    "real_e2e_v14.py",
    "regress_v39.py",
    "smoke_v26.py",
    "smoke_v29.py",
    "validate_final_track.py",
)


@pytest.mark.parametrize("tool", TOOLS)
def test_tool_help_is_safe_and_successful(tool: str) -> None:
    """A maintenance tool must show help before it creates reports or runs audio work."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / tool), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert "usage:" in result.stdout.lower()
