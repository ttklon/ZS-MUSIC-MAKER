from __future__ import annotations

import json
import os
import time
from pathlib import Path

from app.core.auto_backup import create_snapshot, purge_old_backups, restore_snapshot


def test_snapshot_is_bounded_verifiable_and_restorable(tmp_path: Path) -> None:
    data = tmp_path / "data"
    data.mkdir()
    (data / "settings.json").write_text('{"quality":"high"}', encoding="utf-8")
    (data / "ai_models").mkdir()
    (data / "ai_models" / "runtime.bin").write_bytes(b"model-not-backed-up")
    root = tmp_path / "project"
    manifest_source = root / "output" / "run" / "session_manifest.json"
    manifest_source.parent.mkdir(parents=True)
    manifest_source.write_text('{"schema":"v1"}', encoding="utf-8")
    backups = data / "backups"

    report = create_snapshot("ai", data_dir=data, backup_root=backups, root=root, max_bytes=1_024, now=1_700_000_000)
    manifest = json.loads(Path(report["manifest_path"]).read_text(encoding="utf-8"))
    restore_root = tmp_path / "restore"
    restored = restore_snapshot(Path(report["path"]), restore_root)

    assert report["ok"] is True
    assert report["total_bytes"] <= 1_024
    assert manifest["schema"] == "zsmm.backup.v1"
    assert {entry["path"] for entry in manifest["files"]} == {"data/settings.json", "manifests/run/session_manifest.json"}
    assert restored["ok"] is True
    assert (restore_root / "data" / "settings.json").read_text(encoding="utf-8") == '{"quality":"high"}'
    assert not (restore_root / "data" / "ai_models" / "runtime.bin").exists()


def test_snapshot_respects_size_ceiling_and_retention(tmp_path: Path) -> None:
    data = tmp_path / "data"
    data.mkdir()
    (data / "large.json").write_bytes(b"x" * 2_000)
    backups = data / "backups"
    old = backups / "old"
    old.mkdir(parents=True)
    old_time = time.time() - 9 * 24 * 3600
    os.utime(old, (old_time, old_time))

    report = create_snapshot("dry", data_dir=data, backup_root=backups, root=tmp_path, max_bytes=100)
    manifest = json.loads(Path(report["manifest_path"]).read_text(encoding="utf-8"))

    assert report["total_bytes"] == 0
    assert report["skipped"] == 1
    assert manifest["skipped"][0]["reason"] == "max_backup_bytes"
    assert "old" in report["purged"]
    assert purge_old_backups(backups) == []


def test_main_preflight_backup_reports_snapshot(monkeypatch, capsys) -> None:
    from app.cli import backup

    monkeypatch.setattr("app.core.auto_backup.create_snapshot", lambda mode: {"ok": True, "files": 2, "total_bytes": 3, "path": f"/tmp/{mode}"})

    report = backup.preflight_backup("ai_dry_run")

    assert report["ok"] is True
    assert "[backup] files=2 bytes=3 path=/tmp/ai_dry_run" in capsys.readouterr().out
