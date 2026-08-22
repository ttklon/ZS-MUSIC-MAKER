# PLAN_v39 — ШАГ 087: auto_backup before AI/God Mode

Created `app/core/auto_backup.py`. `create_snapshot()` copies eligible `data/` files and output session manifests into `data/backups/<UTC timestamp>_<label>/`, writes a `zsmm.backup.v1` manifest with per-file SHA-256 values, excludes runtime model/backups directories, and never exceeds **50 MB** of copied source content by default. `restore_snapshot()` verifies each checksum before copying and does not delete existing destination files. `purge_old_backups()` removes snapshots older than seven days.

`main.py` now calls `_preflight_backup()` before explicit `--ai`, `--ai --dry-run`, and `--god` execution. Snapshot errors are visible as warnings but do not silently claim a backup exists or prevent a user-requested pipeline from starting.

Acceptance created a temporary data/manifest snapshot, verified manifest contents/checksums, restored it, confirmed model runtime content is excluded, tested the size ceiling and retention purge, and exercised preflight reporting through a stubbed snapshot. Full `pytest tests/ -q` — **204 passed**; `compileall` successfully; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**.
