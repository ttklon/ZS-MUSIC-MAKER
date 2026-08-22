from __future__ import annotations

from tools import readiness


def test_license_inventory_covers_base_and_optional_ai_requirements() -> None:
    rows = readiness.dependency_requirements()
    by_package = {row["package"].lower(): row for row in rows}

    assert "requests" in by_package
    assert "torch" in by_package
    assert "optional-ai" in by_package["torch"]["groups"]
    assert "base" in by_package["matchering"]["groups"]
    assert "optional-ai" in by_package["matchering"]["groups"]


def test_license_markdown_is_explicit_about_evidence_and_review(tmp_path) -> None:
    target = tmp_path / "LICENSES.md"
    written = readiness.write_license_report(target)
    content = target.read_text(encoding="utf-8")

    assert written == target
    assert "# Dependency licenses" in content
    assert "| Package | Requirement groups |" in content
    assert "GPL-compatibility checklist" in content
    assert "REVIEW REQUIRED" in content
    assert "not a license assertion" in content


def test_license_rows_never_guess_missing_distribution_metadata() -> None:
    row = readiness._license_from_metadata("zsmm-package-that-does-not-exist")

    assert row["version"] == "not installed"
    assert row["license"] == "UNKNOWN (distribution unavailable)"
    assert row["source"] == "not installed"
