"""Versioned, bounded desktop recipe snapshots and strict report loading.

Snapshots contain private creative text and local paths. They are not a secure
archive, and restoring them does not verify or copy the referenced source files.
"""
from __future__ import annotations

import json
from pathlib import Path

MAX_REPORT_BYTES = 16 * 1024 * 1024
MAX_SNAPSHOT_BYTES = 1024 * 1024
# Unknown top-level inputs are rejected; known fields can still contain private data.
RECIPE_KEYS = frozenset({
    "project_id", "references", "theme", "beat_engine", "beat_input_path",
    "recorded_backing_sha256", "genre", "artist", "artist_name", "preset",
    "bpm_override", "aggression", "duration_sec", "user_lyrics_lines",
    "reference_lyrics", "transcribe_references", "trend_notes", "voice_mode",
    "stands", "n_verses", "quality_mode", "user_extra_prompt", "seed",
    "own_vocal_wav", "vocal_wav", "use_rvc", "rvc_model_path", "rvc_index_path",
    "rvc_pitch_shift", "vocal_offset_ms", "use_vocal_fx", "tune", "export_stems",
    "bilingual", "only", "variant",
})


def snapshot_recipe(state: dict) -> dict:
    """Return an exact JSON round trip or fail rather than silently lose inputs."""
    if not isinstance(state, dict) or any(not isinstance(k, str) or k not in RECIPE_KEYS for k in state):
        raise ValueError("recipe contains unsupported fields; project snapshot unavailable")
    try:
        data = json.dumps(state, ensure_ascii=False, allow_nan=False).encode("utf-8")
        if len(data) > MAX_SNAPSHOT_BYTES:
            raise ValueError("recipe snapshot exceeds size limit")
        restored = json.loads(data)
    except (TypeError, ValueError, OverflowError, RecursionError) as exc:
        raise ValueError(f"recipe is not safely serializable: {exc}") from exc
    if restored != state:
        raise ValueError("recipe would change in JSON; project snapshot unavailable")
    return {"version": 1, "recipe": restored}


def restore_recipe(report: dict) -> dict:
    snapshot = report.get("desktop_recipe_snapshot")
    if not isinstance(snapshot, dict) or type(snapshot.get("version")) is not int or snapshot["version"] != 1:
        raise ValueError("project has no supported complete recipe snapshot; a new full render is required")
    state = snapshot.get("recipe")
    return snapshot_recipe(state)["recipe"]


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError(f"invalid JSON constant: {value}")


def read_project_report(project: Path) -> tuple[dict, bytes]:
    path = Path(project) / "report.json"
    if path.is_symlink() or not path.is_file():
        raise ValueError("project report is missing or is a symlink")
    with path.open("rb") as stream:
        raw = stream.read(MAX_REPORT_BYTES + 1)
    if len(raw) > MAX_REPORT_BYTES:
        raise ValueError("source report exceeds size limit")
    try:
        report = json.loads(raw, object_pairs_hook=_unique_pairs, parse_constant=_invalid_constant)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ValueError(f"invalid project report: {exc}") from exc
    if not isinstance(report, dict):
        raise ValueError("project report must be an object")
    return report, raw
