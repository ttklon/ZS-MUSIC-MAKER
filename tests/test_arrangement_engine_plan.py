from __future__ import annotations

import modules.arrangement_engine as arrangement


def test_seeded_phonk_arrangement_preserves_patterns_sections_and_hook() -> None:
    style = {"bpm": 132, "key": "F", "mode": "minor", "genre_hint": "phonk / drift"}

    first = arrangement.build_arrangement(style, total_seconds=120, seed=41, variant=2)
    second = arrangement.build_arrangement(style, total_seconds=120, seed=41, variant=2)

    assert first["ok"] is True
    assert first["drums"]["kick"]["pattern_key"] == "phonk"
    assert first["drums"]["hihat"]["pattern_key"] == "phonk"
    assert first["sections"] == second["sections"]
    assert first["total_sec"] == second["total_sec"]
    assert all(section["end_sec"] >= section["start_sec"] for section in first["sections"])
    assert any("riser" in section["fx"] for section in first["sections"])
    hook = first["tiktok_hook"]
    assert 0 <= hook["start_sec"] <= hook["end_sec"] <= first["total_sec"]
    assert hook["end_sec"] - hook["start_sec"] <= 25.0
