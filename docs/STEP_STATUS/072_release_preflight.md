# PLAN_v39 — ШАГ 072: release checklist и preflight

A new read-only `tools/release_preflight.py` validates the release candidate before any tag or release action. It checks that `main` is selected, the worktree is clean, `VERSION` agrees exactly with canonical `version.json`, wheel metadata declares the same mirror, the console entrypoint is present and the source-implied tag is still available locally and on `origin`. The command does not fetch, tag, push, build, install or mutate the repository.

The canonical version already present in the repository is **39.9.0**, with an exact `VERSION` mirror. Therefore the only honest proposed release tag is **`v39.9.0`**. The earlier PLAN text naming `39.0.0-mega`/`v39.0.0` conflicts with the established source version and is not silently applied as a downgrade. Final clean-head preflight and tag verification are reserved for the final release action.

Acceptance: targeted preflight invariants — **2 passed**; full `pytest tests/ -q` — **235 passed**; `compileall` successful; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**. The separate final preflight run will attest clean `main` and tag availability after this step is committed and pushed.
