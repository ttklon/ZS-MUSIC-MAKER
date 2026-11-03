"""Fail-closed and atomic JSON index storage for the user's voice recordings."""
from __future__ import annotations

import json
import os
import stat
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Iterator


class VoiceIndexError(RuntimeError):
    """An existing voice index cannot be safely read or updated."""


def _reject_nonfinite(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def read_index(path: Path, empty: Callable[[], Any], valid: Callable[[Any], bool]) -> Any:
    if path.is_symlink():
        raise VoiceIndexError(f"Voice index is a symbolic link; refusing to update: {path}")
    if not path.exists():
        return empty()
    try:
        with path.open("r", encoding="utf-8") as source:
            data = json.load(source, parse_constant=_reject_nonfinite)
        if not valid(data):
            raise ValueError("unexpected index structure")
        return data
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        raise VoiceIndexError(f"Voice index unreadable; original preserved: {path} ({type(exc).__name__})") from exc


def write_index(path: Path, data: Any) -> None:
    """Write a complete replacement in the same directory; never truncate the original."""
    if path.is_symlink():
        raise VoiceIndexError(f"Voice index is a symbolic link; refusing to update: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as target:
            json.dump(data, target, ensure_ascii=False, indent=2, allow_nan=False)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def lock_index(path: Path, timeout: float = 10) -> Iterator[None]:
    """Serialize read/modify/write across app processes; fail closed on timeout."""
    from filelock import FileLock, Timeout

    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = Path(str(path) + ".lock")
    try:
        info = lock_path.lstat()
    except FileNotFoundError:
        info = None
    if info is not None and (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size != 0):
        raise VoiceIndexError(f"Unsafe existing voice lock file; original preserved: {lock_path}")
    try:
        with FileLock(str(lock_path), timeout=timeout, preserve_lock_file=True, fallback_to_soft=False):
            yield
    except Timeout as exc:
        raise VoiceIndexError(f"Voice index is locked; original preserved: {path}") from exc
