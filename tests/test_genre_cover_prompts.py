from __future__ import annotations

import json
from pathlib import Path

from modules.cover_art_ai import cover_direction_for_genre
from tools.genre_validator import COVER_TEMPLATE_FIELDS, validate_preset_assets

ROOT = Path(__file__).resolve().parents[1]
PRESETS_DIR = ROOT / "data" / "genre_presets"


def test_all_fifty_presets_have_renderable_cover_prompt_templates() -> None:
    presets = sorted(PRESETS_DIR.glob("*.json"))

    assert len(presets) == 50
    assert validate_preset_assets() == []
    for path in presets:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert all(field in payload["prompt_cover"] for field in COVER_TEMPLATE_FIELDS)
        assert payload["cover_instruments"]


def test_cover_direction_uses_preset_mood_key_and_instruments() -> None:
    direction = cover_direction_for_genre("brazilian_phonk", "latin, dark", key="Am")

    assert "brazilian_phonk" in direction
    assert "latin, dark" in direction
    assert "Am tonal palette" in direction
    assert "cowbell" in direction


def test_cover_direction_uses_safe_generic_fallback_for_unknown_genre() -> None:
    direction = cover_direction_for_genre("unknown_genre", "bright", key="C major")

    assert "unknown_genre" in direction
    assert "C major tonal palette" in direction
    assert "rhythmic drums" in direction
