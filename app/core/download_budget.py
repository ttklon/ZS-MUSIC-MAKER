"""Fail-closed per-volume preflight. Estimates reserve space, not a reservation."""
from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

RESERVE_BYTES = 512 * 1024 * 1024


def existing_parent(path: Path) -> Path:
    path = path.absolute()
    while not path.exists():
        if path == path.parent:
            raise OSError('No existing volume for destination')
        path = path.parent
    return path


def space_plan(size: int | None, destination: Path, cache: Path | None = None,
               temporary: Path | None = None) -> dict:
    if type(size) is not int or size <= 0:
        return dict(allowed=False, reason='Unknown download size; supply a reviewed file manifest', volumes=[])
    cache = cache or Path(os.environ.get('HF_HOME', Path.home() / '.cache/huggingface'))
    temporary = temporary or Path(tempfile.gettempdir())
    volumes = {}
    try:
        for purpose, path in [('destination', destination), ('cache', cache), ('temporary', temporary)]:
            parent = existing_parent(path)
            device = str(parent.stat().st_dev)
            row = volumes.setdefault(device, dict(volume=device, required_bytes=RESERVE_BYTES,
                free_bytes=shutil.disk_usage(parent).free, allocations=[]))
            row['required_bytes'] += size
            row['allocations'].append(dict(purpose=purpose, path=str(path), bytes=size))
        allowed = all(v['free_bytes'] >= v['required_bytes'] for v in volumes.values())
        return dict(allowed=allowed, reason='' if allowed else 'Insufficient disk space before download',
                    volumes=list(volumes.values()), reservation=False)
    except OSError as exc:
        return dict(allowed=False, reason=f'Cannot inspect disk: {exc}', volumes=list(volumes.values()))
