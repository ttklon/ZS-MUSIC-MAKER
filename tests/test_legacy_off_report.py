from __future__ import annotations

import sys

import main
from app.core.orchestrator import LEGACY_CAPABILITY_MANIFEST, legacy_compatibility_report


def test_legacy_compatibility_report_marks_only_versioned_capabilities_unavailable() -> None:
    disabled = legacy_compatibility_report(False)
    enabled = legacy_compatibility_report(True)

    assert [row["module"] for row in disabled] == [row[0] for row in LEGACY_CAPABILITY_MANIFEST]
    assert all(row["available"] is False for row in disabled)
    assert all(row["reason"] == "legacy patches disabled" for row in disabled)
    assert all(row["available"] is True for row in enabled)


def test_legacy_off_smoke_reports_before_dispatch_without_importing_patch_modules(
    monkeypatch, capsys
) -> None:
    patch_modules = tuple(f"app.core.{name}" for name in main.LEGACY_PATCH_MODULES)
    for name in patch_modules:
        sys.modules.pop(name, None)
    monkeypatch.setattr(main, "_cli_smoke", lambda: 0)
    monkeypatch.setattr(sys, "argv", ["main.py", "--legacy-off", "--smoke"])

    assert main.main() == 0

    captured = capsys.readouterr().out
    assert '"legacy_enabled": false' in captured
    assert "lyrics_v8" in captured
    assert "run_full_pipeline_v12" in captured
    assert not any(name in sys.modules for name in patch_modules)


def test_legacy_report_can_describe_enabled_mode_without_registering_modules(monkeypatch, capsys) -> None:
    patch_modules = tuple(f"app.core.{name}" for name in main.LEGACY_PATCH_MODULES)
    for name in patch_modules:
        sys.modules.pop(name, None)
    monkeypatch.setattr(sys, "argv", ["main.py", "--legacy-report"])

    assert main.main() == 0

    captured = capsys.readouterr().out
    assert '"legacy_enabled": true' in captured
    assert not any(name in sys.modules for name in patch_modules)
