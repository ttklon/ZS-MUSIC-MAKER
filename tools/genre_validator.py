# -*- coding: utf-8 -*-
"""Проверка versioned JSON пресетов и runtime genre profiles."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRESETS_DIR = ROOT / "data" / "genre_presets"
sys.path.insert(0, str(ROOT))

from modules.genre_engine import GenreFactory, StyleRegistry

PRESET_REQUIRED = {
    "genre": str,
    "bpm_range": list,
    "typical_keys": list,
    "structure_templates": list,
    "mood_tags": list,
    "vocal_style": str,
    "mastering_profile_default": str,
    "prompt_cover": str,
    "cover_instruments": str,
}

COVER_TEMPLATE_FIELDS = {"{genre}", "{mood}", "{key}", "{instruments}"}


def validate_preset_assets(presets_dir: Path = PRESETS_DIR) -> list[str]:
    """Проверить 50 versioned preset JSON по реальной data schema."""
    errors: list[str] = []
    files = sorted(presets_dir.glob("*.json"))
    for path in files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{path.name}: invalid JSON: {exc}")
            continue
        for field, field_type in PRESET_REQUIRED.items():
            if field not in payload:
                errors.append(f"{path.name}: missing {field}")
            elif not isinstance(payload[field], field_type) or not payload[field]:
                errors.append(f"{path.name}: invalid {field}")
        template = payload.get("prompt_cover", "")
        if isinstance(template, str) and template:
            missing_fields = sorted(field for field in COVER_TEMPLATE_FIELDS if field not in template)
            if missing_fields:
                errors.append(f"{path.name}: prompt_cover missing placeholders {missing_fields}")
        bpm = payload.get("bpm_range", [])
        if isinstance(bpm, list) and len(bpm) == 2:
            if not all(isinstance(value, (int, float)) for value in bpm) or not (20 <= bpm[0] <= bpm[1] <= 300):
                errors.append(f"{path.name}: invalid bpm_range={bpm!r}")
        else:
            errors.append(f"{path.name}: bpm_range must contain [min, max]")
    if len(files) != 50:
        errors.append(f"expected exactly 50 JSON presets, found {len(files)}")
    return errors


def validate_runtime_genres() -> list[str]:
    """Проверить runtime factory profiles, включая non-JSON built-ins."""
    registry = StyleRegistry()
    factory = GenreFactory(registry)
    errors: list[str] = []
    for genre in registry.list_genres():
        try:
            state = factory.create_wizard_state(genre)
            for field in ("bpm_override", "key_override", "energy", "tags"):
                if field not in state:
                    errors.append(f"runtime {genre}: missing {field}")
            if not 20 <= state["bpm_override"] <= 300:
                errors.append(f"runtime {genre}: invalid BPM {state['bpm_override']}")
        except Exception as exc:
            errors.append(f"runtime {genre}: {exc}")
    return errors


def validate_all() -> bool:
    asset_errors = validate_preset_assets()
    runtime_errors = validate_runtime_genres()
    runtime_count = len(StyleRegistry().list_genres())
    print(f"Preset assets: {len(list(PRESETS_DIR.glob('*.json')))}/50")
    print(f"Runtime genres: {runtime_count}")
    errors = asset_errors + runtime_errors
    if errors:
        print(f"FAIL: {len(errors)} issue(s)")
        for error in errors:
            print(f"  - {error}")
        return False
    print("PASS: 50/50 preset assets and all runtime genres are valid")
    return True


if __name__ == "__main__":
    from cli_contract import help_or_error

    if help_or_error(__doc__ or "ZS Music Maker tool"):
        raise SystemExit(0)
    raise SystemExit(0 if validate_all() else 1)
