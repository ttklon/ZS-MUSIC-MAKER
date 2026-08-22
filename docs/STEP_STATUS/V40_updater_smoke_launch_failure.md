# APP_L v40 — updater smoke-process launch failure

The updater replaces the application only after archive verification and backup. Its post-install smoke test already rolled back for a nonzero exit code or timeout, but an exception while *starting* the smoke process was silently ignored and could be followed by a successful installation result.

`install_from_zip()` now treats an unexpected smoke-process launch exception as a `smoke_test` failure. It returns a typed error message, preserves the backup path and exposes rollback status, matching the existing nonzero-exit and timeout failure contract. This prevents a failed smoke launch from being reported as accepted installation.

Focused regression uses a synthetic archive and mocks only the installation boundaries; it forces `subprocess.run` to raise `OSError` and asserts an explicit failed result with requested rollback. It does not install a release, download an update, run a smoke process or claim a restored application artifact.

Acceptance: focused updater suite — **2 passed**. Full `pytest tests/ -q` — **324 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**; `git diff --check` successful. Fresh deep audit reports **82 SILENT_EXCEPT_PASS** (from 83) and **878 total heuristic records** across **254** Python files. The `LONG_FUNCTION` category is now **25** because the explicit failure return legitimately lengthened this production function; raw audit JSON remains ignored and was not committed.
