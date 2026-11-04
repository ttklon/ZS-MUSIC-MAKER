"""Explicit, non-file recipe changes allowed for an opened-project rebuild.

The original manifest is verified and its files copied before these overrides
are applied. Changing lyrics does not modify a pre-recorded vocal.
"""
from __future__ import annotations

import copy
from typing import Any

TEXT_LIMITS = {"theme": 5000, "artist": 1000, "user_extra_prompt": 10000,
               "reference_lyrics": 100000, "trend_notes": 100000}
INTEGER_LIMITS = {"vocal_offset_ms": (-5000, 5000), "n_verses": (1, 4)}
EDITABLE_FIELDS = frozenset({*TEXT_LIMITS, *INTEGER_LIMITS, "bpm_override", "user_lyrics_lines", "export_stems"})


def validate_project_overrides(overrides: dict[str, Any] | None) -> dict[str, Any]:
    """Reject unknown keys and invalid values; never silently coerce or clamp."""
    if overrides is None:
        return {}
    if not isinstance(overrides, dict) or any(not isinstance(key, str) or key not in EDITABLE_FIELDS for key in overrides):
        raise ValueError("unsupported project edit; file paths and other settings cannot be replaced here")
    for key, value in overrides.items():
        if key in TEXT_LIMITS:
            if not isinstance(value, str) or len(value) > TEXT_LIMITS[key] or (key in ("theme", "artist") and not value.strip()):
                raise ValueError(f"invalid project edit: {key}; text limit {TEXT_LIMITS[key]} characters, theme/artist cannot be blank")
        elif key in INTEGER_LIMITS:
            low, high = INTEGER_LIMITS[key]
            if type(value) is not int or not low <= value <= high:
                raise ValueError(f"invalid project edit: {key}; expected integer {low}..{high}")
        elif key == "bpm_override":
            if value is not None and (type(value) is not int or not 1 <= value <= 220):
                raise ValueError("invalid project edit: bpm_override; expected integer 1..220 or auto")
        elif key == "export_stems":
            if type(value) is not bool:
                raise ValueError("invalid project edit: export_stems")
        elif key == "user_lyrics_lines":
            if (not isinstance(value, list) or len(value) > 2000
                    or any(not isinstance(line, str) or len(line) > 10000 for line in value)
                    or sum(len(line) for line in value) > 100000):
                raise ValueError("invalid project edit: user_lyrics_lines; maximum 2000 lines, 10000 characters per line and 100000 total")
    return copy.deepcopy(overrides)


def apply_project_overrides(recipe: dict[str, Any], overrides: dict[str, Any] | None) -> dict[str, Any]:
    result = copy.deepcopy(recipe)
    changes = validate_project_overrides(overrides)
    result.update(changes)
    if "artist" in changes and "artist_name" in result:
        result["artist_name"] = changes["artist"]
    return result
