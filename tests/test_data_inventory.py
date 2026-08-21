# -*- coding: utf-8 -*-
"""Регрессии для versioned-каталога data и его статического аудита."""
from __future__ import annotations

from tools.audit_data_inventory import scan_data


def test_repository_data_inventory_is_clean() -> None:
    report = scan_data()

    assert report["files"]
    assert report["unknown"] == []
    assert report["invalid"] == []


def test_inventory_reports_unknown_and_invalid_assets(tmp_path) -> None:
    (tmp_path / "genre_presets").mkdir()
    (tmp_path / "genre_presets" / "valid.json").write_text("{}", encoding="utf-8")
    (tmp_path / "unmanaged.json").write_text("{broken", encoding="utf-8")

    report = scan_data(tmp_path)

    assert report["unknown"] == ["unmanaged.json"]
    assert report["invalid"][0]["path"] == "unmanaged.json"
    assert report["invalid"][0]["error"].startswith(
        "Expecting property name enclosed in double quotes"
    )
