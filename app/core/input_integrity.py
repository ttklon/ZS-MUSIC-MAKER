"""Record and freeze explicit recipe inputs for a cautious full rebuild.

Checksums detect accidental changes, not malicious report edits or concurrent
replacement attacks. External AI weights, programs and services are not covered.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import shutil
import tempfile
from pathlib import Path

from app.core.project_snapshot import snapshot_recipe
from app.core.revision import _sha256

FILE_FIELDS = ("beat_input_path", "own_vocal_wav", "vocal_wav", "rvc_model_path", "rvc_index_path")


def _recipe_digest(recipe: dict) -> str:
    state = snapshot_recipe(recipe)["recipe"]
    data = json.dumps(state, ensure_ascii=False, sort_keys=True, allow_nan=False, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _locations(recipe: dict) -> list[tuple[str, int | None, str]]:
    locations = []
    refs = recipe.get("references")
    if refs is not None:
        if not isinstance(refs, list) or any(not isinstance(p, str) or not p for p in refs):
            raise ValueError("reference paths must be non-empty strings in a list")
        locations.extend(("references", i, p) for i, p in enumerate(refs))
    for field in FILE_FIELDS:
        value = recipe.get(field)
        if value is not None and value != "":
            if not isinstance(value, str):
                raise ValueError(f"invalid input path: {field}")
            locations.append((field, None, value))
    return locations


def _file_info(path: Path) -> tuple[int, str]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"input is missing, a symlink, or not a regular file: {path}")
    before = path.stat()
    digest = _sha256(path)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
        raise ValueError(f"input changed during hashing: {path}")
    return after.st_size, digest


def capture_inputs(recipe: dict) -> dict:
    digest = _recipe_digest(recipe)
    entries = []
    for field, index, raw in _locations(recipe):
        path = Path(raw)
        size, sha = _file_info(path)
        entries.append({"field": field, "index": index, "raw_path": raw,
                        "absolute_path": str(path.resolve(strict=True)), "bytes": size, "sha256": sha})
    return {"version": 1, "recipe_sha256": digest, "files": entries}


def begin_input_capture(recipe: dict, enabled: bool) -> tuple[dict | None, str | None]:
    if not enabled:
        return None, None
    try:
        return capture_inputs(recipe), None
    except (OSError, ValueError, TypeError, RecursionError) as exc:
        return None, f"input integrity unavailable: {type(exc).__name__}: {exc}"


def finish_input_capture(report: dict, recipe: dict, capture: tuple[dict | None, str | None], warnings: list[str]) -> None:
    initial, error = capture
    if error:
        warnings.append(error + "; full rebuild after reopening unavailable")
        return
    if initial is None:
        return
    try:
        if capture_inputs(recipe) != initial:
            raise ValueError("inputs or recipe changed during render")
        report["input_integrity"] = initial
    except (OSError, ValueError, TypeError, RecursionError) as exc:
        warnings.append(f"input integrity unavailable: {type(exc).__name__}: {exc}; full rebuild after reopening unavailable")


def _validated_entries(recipe: dict, manifest: object) -> list[dict]:
    if not isinstance(manifest, dict) or type(manifest.get("version")) is not int or manifest["version"] != 1:
        raise ValueError("project has no supported input integrity manifest")
    if manifest.get("recipe_sha256") != _recipe_digest(recipe):
        raise ValueError("saved recipe does not match input manifest")
    entries, locations = manifest.get("files"), _locations(recipe)
    if not isinstance(entries, list) or len(entries) != len(locations):
        raise ValueError("input manifest does not cover the recipe")
    for entry, (field, index, raw) in zip(entries, locations):
        if not isinstance(entry, dict) or (entry.get("field"), entry.get("index"), entry.get("raw_path")) != (field, index, raw):
            raise ValueError("input manifest does not match the recipe")
        path, size, sha = entry.get("absolute_path"), entry.get("bytes"), entry.get("sha256")
        if not isinstance(path, str) or not Path(path).is_absolute():
            raise ValueError("invalid input manifest path")
        if type(size) is not int or size < 0 or not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{64}", sha):
            raise ValueError("invalid input manifest checksum or size")
    return entries


def _source_path(entry: dict, source: Path, report: dict) -> Path:
    path = Path(entry["absolute_path"])
    old_root = report.get("project_root")
    if isinstance(old_root, str) and Path(old_root).is_absolute():
        try:
            relative = path.relative_to(Path(old_root))
        except ValueError:
            relative = None
        if relative is not None:
            candidate = source / relative
            if not candidate.resolve().is_relative_to(source.resolve()):
                raise ValueError("project input escaped the selected directory")
            return candidate
    return path


def freeze_inputs(recipe: dict, report: dict, source: Path, destination: Path) -> dict:
    """Copy and hash every recorded input into a new project; never mutate sources."""
    source, destination = Path(source).resolve(strict=True), Path(destination).resolve(strict=True)
    if source == destination or source.is_relative_to(destination) or destination.is_relative_to(source):
        raise ValueError("full rebuild must use a separate project directory")
    entries = _validated_entries(recipe, report.get("input_integrity"))
    result = copy.deepcopy(recipe)
    final = destination / "input_files"
    if final.exists() or final.is_symlink():
        raise FileExistsError("input destination already exists")
    with tempfile.TemporaryDirectory(prefix=".inputs-", dir=destination) as temporary:
        temp = Path(temporary)
        cached: dict[tuple[str, int, str], str] = {}
        for entry in entries:
            path = _source_path(entry, source, report)
            key = (str(path), entry["bytes"], entry["sha256"])
            name = cached.get(key)
            if name is None:
                if _file_info(path) != (entry["bytes"], entry["sha256"]):
                    raise ValueError(f"input failed integrity check: {entry['field']}")
                suffix = path.suffix.lower()
                if not re.fullmatch(r"\.[a-z0-9]{1,12}", suffix):
                    suffix = ".bin"
                name = f"input-{len(cached):04d}{suffix}"
                copied = temp / name
                shutil.copyfile(path, copied)
                if _file_info(copied) != (entry["bytes"], entry["sha256"]):
                    raise ValueError(f"copied input failed integrity check: {entry['field']}")
                cached[key] = name
            target = str((final / name).resolve())
            if entry["index"] is None:
                result[entry["field"]] = target
            else:
                result[entry["field"]][entry["index"]] = target
        temp.rename(final)
    return result
