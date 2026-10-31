from __future__ import annotations

from tools import readiness


def test_tracked_python_modules_match_versioned_production_tree() -> None:
    paths = readiness.tracked_python_modules()

    assert paths == sorted(paths)
    assert "main.py" in paths
    assert "tools/readiness/__init__.py" in paths
    assert all(path.endswith(".py") for path in paths)
    assert not [path for path in paths if path.startswith("tests/")]
    assert all(
        "/" not in path or path.split("/", 1)[0] in readiness.INVENTORY_ROOTS
        for path in paths
    )


def test_module_inventory_has_auditable_status_for_every_tracked_module() -> None:
    rows = readiness.module_inventory()

    assert len(rows) == len(readiness.tracked_python_modules())
    assert {row["path"] for row in rows} == set(readiness.tracked_python_modules())
    assert all(row["syntax_ok"] for row in rows)
    assert {row["status"] for row in rows} <= {"REAL_PASS", "REAL_FAIL", "PLANNED"}


def test_inventory_markdown_has_one_row_per_tracked_module() -> None:
    table = readiness.inventory_markdown()

    assert table.startswith("| Versioned module | Status |")
    assert table.count("\n") == len(readiness.tracked_python_modules()) + 1
    assert "| tools/readiness/__init__.py |" in table


def test_readiness_includes_inventory_summary_without_changing_compute_shape() -> None:
    percent, details = readiness.compute()

    summary = details["module_inventory"]
    assert isinstance(percent, float)
    assert set(summary) == {"tracked_modules", "REAL_PASS", "REAL_FAIL", "PLANNED"}
    assert summary["tracked_modules"] == len(readiness.tracked_python_modules())
    assert sum(summary[key] for key in ("REAL_PASS", "REAL_FAIL", "PLANNED")) == summary["tracked_modules"]
    assert "caps_triggered" in details
