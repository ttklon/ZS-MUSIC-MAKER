"""Explicit replacement inputs for a new render of an opened project.

Selections are hashed and stat-checked at queue time, then copied, decoded and
checked again in the worker. This detects ordinary changes, not hostile TOCTOU
attacks. Archive metadata is not proof of who sang or of synchronization.
"""
from __future__ import annotations

import copy
import re
import shutil
import stat
from pathlib import Path

from app.core.input_integrity import _file_info

INPUT_KEYS = frozenset({"references", "beat_input_path", "own_vocal_wav"})
AUDIO_SUFFIXES = frozenset({".wav", ".flac", ".ogg"})
MAX_FILE_BYTES = 4 * 1024 * 1024 * 1024


def _identity(path: Path) -> tuple:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_FILE_BYTES:
        raise ValueError(f"replacement must be a regular audio file under 4 GiB: {path}")
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


class InputPreparationCancelled(Exception):
    """The user cancelled before any rebuild job was queued."""


def _selected(path: str, checkpoint=None) -> dict:
    if not isinstance(path, str) or not path or len(path) > 4096:
        raise ValueError("invalid replacement path")
    file = Path(path)
    if not file.is_absolute() or file.suffix.lower() not in AUDIO_SUFFIXES:
        raise ValueError("replacement requires an absolute WAV, FLAC or OGG path")
    identity = _identity(file)
    resolved = str(file.resolve(strict=True))
    size, digest = _file_info(file, checkpoint=checkpoint) if checkpoint is not None else _file_info(file)
    if _identity(file) != identity or str(file.resolve(strict=True)) != resolved:
        raise ValueError("selected input changed while queueing")
    return {"path": str(file), "resolved": resolved, "identity": identity, "size": size, "sha256": digest}


def prepare_replacements(replacements: dict | None, cancelled=None) -> dict:
    """Capture identities and hashes; optionally stop between file reads."""
    def checkpoint():
        if cancelled is not None and cancelled():
            raise InputPreparationCancelled("input preparation cancelled")
    checkpoint()
    if replacements is None:
        return {}
    if not isinstance(replacements, dict) or any(k not in INPUT_KEYS | {"ack_unverified_pairing"} for k in replacements):
        raise ValueError("unsupported input replacement")
    ack = replacements.get("ack_unverified_pairing", False)
    if type(ack) is not bool:
        raise ValueError("invalid unverified-pairing confirmation")
    prepared = {"ack_unverified_pairing": ack}
    for key in INPUT_KEYS:
        checkpoint()
        if key not in replacements:
            continue
        value = replacements[key]
        if key == "references":
            if not isinstance(value, list) or len(value) > 50:
                raise ValueError("choose at most 50 reference files")
            prepared[key] = [_selected(item, checkpoint=checkpoint) for item in value]
        else:
            prepared[key] = _selected(value, checkpoint=checkpoint)
    checkpoint()
    if len(prepared) == 1:
        if ack:
            raise ValueError("pairing confirmation requires a replacement")
        return {}
    return prepared


def _copy_selection(selection: dict, temp: Path, final: Path, number: int, field: str) -> tuple[str, str]:
    path = Path(selection["path"])
    if _identity(path) != selection["identity"] or str(path.resolve(strict=True)) != selection["resolved"]:
        raise ValueError(f"selected input changed since queueing: {field}")
    size, digest = _file_info(path)
    if (size, digest) != (selection["size"], selection["sha256"]):
        raise ValueError(f"selected input changed since queueing: {field}")
    name = f"replacement-{number:04d}{path.suffix.lower()}"
    copied = temp / name
    shutil.copyfile(path, copied)
    if _file_info(copied) != (size, digest) or _file_info(path) != (size, digest):
        raise ValueError(f"replacement changed or copy failed integrity check: {field}")
    if _identity(path) != selection["identity"] or str(path.resolve(strict=True)) != selection["resolved"]:
        raise ValueError(f"selected input changed while copying: {field}")
    from app.core.user_vocal import inspect_user_vocal
    try:
        audio = inspect_user_vocal(str(copied))
    except (OSError, RuntimeError, ValueError) as exc:
        raise ValueError(f"invalid replacement audio ({field}): {exc}") from exc
    if field == "beat_input_path" and (audio["duration_sec"] < 0.25 or audio["peak"] > 1.0001):
        raise ValueError("replacement backing must be at least 0.25 seconds and not exceed full scale")
    return str(final / name), digest


def _archive_binding(path: str) -> str:
    from modules.voice_convert import recording_backing
    binding = recording_backing(path)
    expected = binding.get("sha256") or ""
    recorded_path = binding.get("path") or ""
    if not expected and not recorded_path:
        return ""
    if not recorded_path or not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("recording archive has incomplete or invalid backing metadata")
    return expected


def apply_replacement_inputs(recipe: dict, original: dict, entries: list[dict], selection: dict,
                             temp: Path, final: Path) -> tuple[dict, dict]:
    """Copy replacements, preserve or validate backing binding, and return provenance."""
    result = copy.deepcopy(recipe)
    changed = [key for key in ("references", "beat_input_path", "own_vocal_wav") if key in selection]
    if not changed:
        return result, {}
    copied, hashes = {}, {}
    number = 0
    for key in changed:
        items = selection[key] if key == "references" else [selection[key]]
        paths, digests = [], []
        for item in items:
            path, digest = _copy_selection(item, temp, final, number, key)
            number += 1
            paths.append(path)
            digests.append(digest)
        copied[key] = paths if key == "references" else paths[0]
        hashes[key] = digests if key == "references" else digests[0]
    result.update(copied)
    if "beat_input_path" in changed:
        result["beat_engine"] = "user_audio"
    expected = str(original.get("recorded_backing_sha256") or "")
    label = "PRESERVED" if expected else "UNVERIFIED"
    if "own_vocal_wav" in changed:
        old_key = "own_vocal_wav" if original.get("own_vocal_wav") else "vocal_wav"
        old = next((e for e in entries if e["field"] == old_key), None)
        if expected and old and old["sha256"] == hashes["own_vocal_wav"]:
            label = "PRESERVED"
        else:
            expected = _archive_binding(selection["own_vocal_wav"]["path"])
            label = "ARCHIVE_BACKING_MATCH" if expected else "UNVERIFIED"
        result["recorded_backing_sha256"] = expected
        result.pop("vocal_wav", None)
        if str(result.get("voice_mode") or "pro").strip().lower() == "off":
            result["voice_mode"] = "pro"
    pair_changed = bool({"beat_input_path", "own_vocal_wav"} & set(changed))
    active_vocal = ((result.get("own_vocal_wav") or result.get("vocal_wav"))
                    and str(result.get("voice_mode") or "pro").strip().lower() != "off")
    if expected and pair_changed:
        backing = result.get("beat_input_path")
        if (not re.fullmatch(r"[0-9a-f]{64}", expected) or result.get("beat_engine") != "user_audio" or not backing):
            raise ValueError("recorded vocal requires its bound backing")
        # The files are still in the temporary directory at this point.
        local_backing = temp / Path(backing).name
        if _file_info(local_backing)[1] != expected:
            raise ValueError("selected backing does not match the recording's saved SHA-256")
    elif pair_changed and active_vocal and not selection.get("ack_unverified_pairing"):
        raise ValueError("voice/backing pairing is unverified; explicit confirmation is required")
    details = {"replaced_fields": changed}
    if pair_changed and active_vocal:
        details["vocal_binding"] = label
    return result, details
