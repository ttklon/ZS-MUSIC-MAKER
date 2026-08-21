from __future__ import annotations

from tools.genre_validator import validate_preset_assets, validate_runtime_genres


def test_all_versioned_genre_presets_have_valid_schema() -> None:
    assert validate_preset_assets() == []


def test_all_runtime_genres_build_wizard_state() -> None:
    assert validate_runtime_genres() == []
