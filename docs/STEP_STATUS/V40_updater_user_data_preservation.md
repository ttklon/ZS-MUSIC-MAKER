# APP_L v40 — updater failure-closed user-data preservation

Before replacing the program directory, the updater moves paths listed in `USER_PRESERVED` into a staging stash. Previously, a failed move was silently ignored. The later replacement loop could then delete the source that had not been preserved while the update still proceeded.

`_stash_user_data()` now accumulates typed move failures and raises a clear `RuntimeError` before destructive replacement. `install_from_zip()` already handles replacement-stage failures by invoking rollback from its pre-install backup, so a preservation failure now reaches that recovery path rather than allowing an update that may delete user data.

The focused regression creates a protected `settings.json`, forces its move to raise `PermissionError`, verifies the explicit error, and confirms the source file remains unchanged. No update archive is installed, no user data is deleted, restored, uploaded or claimed as a real recovery artifact.

Acceptance: focused updater suite — **3 passed**. Full `pytest tests/ -q` — **330 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**; `git diff --check` successful. Fresh deep audit reports **77 SILENT_EXCEPT_PASS** (from 78) and **880 total heuristic records** across **257** Python files. Raw audit JSON remains ignored and was not committed.
