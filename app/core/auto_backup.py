"""Bounded preflight snapshots for AI/God Mode runs."""

from __future__ import annotations

import hashlib
import json
import shutil
import time
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = ROOT / "data"
DEFAULT_BACKUP_ROOT = DEFAULT_DATA_DIR / "backups"
MAX_BACKUP_BYTES = 50_000_000
RETENTION_DAYS = 7
_EXCLUDED_DATA_PARTS = {"backups", "ai_models"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _data_candidates(data_dir: Path) -> Iterable[tuple[Path, Path]]:
    if not data_dir.exists():
        return []
    candidates: list[tuple[Path, Path]] = []
    for path in sorted(data_dir.rglob("*")):
        if not path.is_file() or any(part in _EXCLUDED_DATA_PARTS for part in path.relative_to(data_dir).parts):
            continue
        candidates.append((path, Path("data") / path.relative_to(data_dir)))
    return candidates


def _manifest_candidates(root: Path) -> Iterable[tuple[Path, Path]]:
    output_dir = root / "output"
    if not output_dir.exists():
        return []
    candidates: list[tuple[Path, Path]] = []
    for path in sorted(output_dir.rglob("*.json")):
        if "manifest" not in path.name.lower() or not path.is_file():
            continue
        candidates.append((path, Path("manifests") / path.relative_to(output_dir)))
    return candidates


def purge_old_backups(backup_root: Path = DEFAULT_BACKUP_ROOT, now: float | None = None) -> list[str]:
    """Remove timestamped snapshots older than retention and return removed names."""
    if not backup_root.exists():
        return []
    cutoff = (time.time() if now is None else now) - RETENTION_DAYS * 24 * 3600
    removed: list[str] = []
    for child in backup_root.iterdir():
        if not child.is_dir() or child.stat().st_mtime >= cutoff:
            continue
        shutil.rmtree(child, ignore_errors=True)
        removed.append(child.name)
    return sorted(removed)


def create_snapshot(
    label: str,
    data_dir: Path = DEFAULT_DATA_DIR,
    backup_root: Path = DEFAULT_BACKUP_ROOT,
    root: Path = ROOT,
    max_bytes: int = MAX_BACKUP_BYTES,
    now: float | None = None,
) -> dict:
    """Copy a bounded data/manifest snapshot and return verifiable metadata."""
    timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(time.time() if now is None else now))
    safe_label = "".join(char for char in str(label) if char.isalnum() or char in "_-" )[:32] or "run"
    target = backup_root / f"{timestamp}_{safe_label}"
    suffix = 1
    while target.exists():
        target = backup_root / f"{timestamp}_{safe_label}_{suffix}"
        suffix += 1
    target.mkdir(parents=True, exist_ok=False)
    selected: list[dict] = []
    skipped: list[dict] = []
    total = 0
    for source, relative in [*_data_candidates(data_dir), *_manifest_candidates(root)]:
        size = source.stat().st_size
        if total + size > max_bytes:
            skipped.append({"path": str(relative), "size": size, "reason": "max_backup_bytes"})
            continue
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        total += size
        selected.append({"path": str(relative), "size": size, "sha256": _sha256(destination)})
    manifest = {
        "schema": "zsmm.backup.v1",
        "label": safe_label,
        "created_at": timestamp,
        "max_bytes": max_bytes,
        "total_bytes": total,
        "files": selected,
        "skipped": skipped,
    }
    (target / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    removed = purge_old_backups(backup_root, now=now)
    return {
        "ok": True,
        "path": str(target),
        "manifest_path": str(target / "manifest.json"),
        "total_bytes": total,
        "files": len(selected),
        "skipped": len(skipped),
        "purged": removed,
    }


def restore_snapshot(snapshot_dir: Path, destination_root: Path) -> dict:
    """Restore listed snapshot files after checksum verification; never deletes target files."""
    manifest_path = Path(snapshot_dir) / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        restored: list[str] = []
        for entry in manifest.get("files", []):
            relative = Path(entry["path"])
            source = Path(snapshot_dir) / relative
            if not source.is_file() or _sha256(source) != entry["sha256"]:
                return {"ok": False, "reason": f"checksum mismatch: {relative}", "restored": restored}
            target = Path(destination_root) / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            restored.append(str(relative))
        return {"ok": True, "restored": restored}
    except Exception as exc:
        return {"ok": False, "reason": f"restore failed: {exc}", "restored": []}
