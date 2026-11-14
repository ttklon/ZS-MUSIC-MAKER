"""Isolate Numba's on-disk JIT cache for independently launched processes.

Call before importing Numba. This is a mitigation for observed cross-process
cache corruption, not a guarantee against native crashes or other concurrent
processes that do not use this entrypoint.
"""
from __future__ import annotations

import logging
import os
import sys
import tempfile
from contextlib import contextmanager
from typing import Iterator

_MARKER = "ZSMM_NUMBA_CACHE_ISOLATED"
_BASE = "ZSMM_NUMBA_CACHE_BASE"


def _base(environ: dict) -> str | None:
    # A child launched by another isolated process must use a sibling directory,
    # not a child of the parent's temporary directory, which may be cleaned first.
    if environ.get(_MARKER) == "1":
        return environ.get(_BASE) or None
    return environ.get("NUMBA_CACHE_DIR") or None


def _make_temporary(base: str | None) -> tempfile.TemporaryDirectory:
    """Каталог под кэш; если указанная база исчезла — системный, а не отказ.

    `NUMBA_CACHE_DIR` может указывать на удалённый каталог (устаревшая
    переменная окружения, вычищенный tmp). Раньше это означало `RuntimeError`
    на старте приложения; изоляция кэша не стоит того, чтобы не дать программе
    запуститься, поэтому откат логируется и берётся системный tmp.
    """
    try:
        return tempfile.TemporaryDirectory(
            prefix="zsmm-numba-", dir=base, ignore_cleanup_errors=True
        )
    except OSError:
        if base is None:
            raise
        logging.getLogger(__name__).warning(
            "Numba cache base %r is not usable; using the system temporary directory", base
        )
        return tempfile.TemporaryDirectory(
            prefix="zsmm-numba-", dir=None, ignore_cleanup_errors=True
        )


@contextmanager
def isolated_numba_cache() -> Iterator[str]:
    """Set a fresh cache for this process and clean only that directory on exit.

    Environments embedding the app must invoke this before importing Numba.
    Abnormal termination may leave an OS temporary directory behind.
    """
    if "numba" in sys.modules:
        raise RuntimeError("cannot isolate Numba cache after Numba was imported")
    previous = {key: os.environ.get(key) for key in ("NUMBA_CACHE_DIR", _MARKER, _BASE)}
    base = _base(os.environ)
    if base is not None:
        base = os.path.abspath(base)
    try:
        temporary = _make_temporary(base)
    except OSError as exc:
        raise RuntimeError(
            "cannot create private Numba cache; check NUMBA_CACHE_DIR or the system temporary directory"
        ) from exc
    with temporary as directory:
        assigned = {"NUMBA_CACHE_DIR": directory, _MARKER: "1", _BASE: base or ""}
        os.environ.update(assigned)
        try:
            yield directory
        finally:
            for key, value in previous.items():
                # Do not overwrite unrelated changes made by the caller.
                if os.environ.get(key) == assigned[key]:
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value
