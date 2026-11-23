# Blocker implementation progress — 2026-11-15

No acceptance counters changed by this note.

- SequentialAIRunner now defaults to subprocess stages. Model availability checks,
  loading and inference happen in that process; timeout includes worker startup and
  loading. Context and sink changes commit only with a successful result. Model
  handles are not serialized. Trusted internal closures use pinned cloudpickle.
- Windows CLI and stage hosts enter kill-on-close Jobs before executing task code.
  A Windows integration test opens a detached child process handle, kills only its
  host, then requires the child handle to become signaled.
- Explicit `isolate_stages=False` exists for compatibility embedders; it does NOT
  provide native-call preemption. Product call sites use the isolated default.
- Structured diagnostic export excludes free-text messages, timestamps, paths and
  original task IDs. The separate stdlib schema consumer rejects extra fields.
  This is an independent implementation check, not an independent human audit.
- Windows workflow now builds NSIS, installs to a fresh current-user destination,
  inspects install ACLs for broad write/delete/change-owner permissions, runs the
  installed window and checks uninstall preserves an external workspace sentinel.
  This lightweight installer has no bundled model runtime; it does not prove GPU
  inference, Python bundle acceptance or non-admin-token behavior.

Local evidence before first push:
- Stage integration + AI layer + terminal progress + function budgets: 40 passed.
- Preflight/pull/bootstrap/offline/runtime regression selection: 80 passed.
- Diagnostics + task lifecycle/task selection: 25 passed.
- Windows-specific descendant test is not executed on Linux.
- Export schema consumer accepted generated structured fixture: 2 entries,
  zero free-text fields.

Windows results must be recorded after CI, not inferred from these local checks.
Remaining broader acceptance includes clean standard-user/full-runtime installation,
actual model/hardware scenarios, licenses and a genuinely independent privacy audit.

## Windows evidence follow-up

- Run 45101430463 (5976512): packaged NSIS install/ACL/window/uninstall job
  succeeded, Python selection failed on catalogue fingerprint mismatch.
- The mismatch was reproduced as LF versus CRLF requirements bytes; fingerprint
  inputs now normalize line endings and have a specific regression test.
- Run 45101969547 (3c7abb5): all three Windows jobs succeeded, including the
  stage-process, kill-on-close descendant and cross-language export audit tests.
  https://github.com/ttklon/ZS-MUSIC-MAKER/actions/runs/45101969547
- Full local Node suite completed after the command collection timeout:
  578 passed, zero failed, 232215.920022 ms. The original process continued;
  the suite was not launched a second time.
- Follow-up adds actual bundled core Python to NSIS, tests relocated imports and
  an isolated stage inside the installed product, and adds detached grandchildren
  to the kill-on-close integration test. Results require the later workflow run.
- Read-only install hardening removes model-directory creation at registry import,
  uses ZSMM_WORKSPACE for registry/puller model storage, and disables bytecode writes
  in isolated stages. Installer checks now apply an explicit current-user write
  deny to installed project resources, prove a write probe fails, and require the
  installed isolated stage to work anyway. This is not a standard-token test.
