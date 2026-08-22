# APP_L v40 — ШАГИ 0005–0008: portable temporary paths

Confirmed fixed POSIX paths were confined to manual/self-test flows, but could fail on Windows. `release_pack_v9` now derives its non-existent CLI example master path from `tempfile.gettempdir()`. `video_edit_v11._self_test()` creates an LRC fixture in `TemporaryDirectory`, closes it before parsing and removes it automatically. The dotenv regression now constructs its configured beats directory from pytest `tmp_path`.

The audit entry 0007 for `tests/test_ai_layer.py` was rechecked against current source and is stale: the cited position contains a Demucs validation assertion and no `/tmp/unused.txt` literal. No unrelated test code was changed merely to satisfy an outdated line reference.

| Planned items | Resolution |
|---|---|
| 0005 | Fixed portable manual CLI example path |
| 0006 | Fixed portable video self-test fixture |
| 0007 | Stale finding; no current POSIX literal at cited source |
| 0008 | Fixed portable settings fixture |

Acceptance: focused portable-path/settings tests — **9 passed**. Full `pytest tests/ -q` — **242 passed**; `compileall` successful; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**.
