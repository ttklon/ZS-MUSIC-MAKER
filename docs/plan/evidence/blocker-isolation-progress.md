# Blocker implementation progress — 2026-11-15

No acceptance counters changed by this note.

- SequentialAIRunner now defaults to subprocess stages. Model availability checks,
  loading and inference happen in that process; timeout includes worker startup and
  loading. Context and sink changes commit only with a successful result. Model
  handles are not serialized. Trusted internal closures use pinned cloudpickle.
- Windows CLI and stage hosts enter kill-on-close Jobs before executing task code.
  A Windows integration test opens a detached child process handle, kills only its
  host, then requires the child handle to become signaled.
- Isolation is mandatory: the interim in-process compatibility switch and old
  SIGALRM/thread watchdog were removed. Loading is never performed in the runner.
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

## Preserved task mapping

- T0149–T0150: kill-on-close host, detached child/grandchild Windows integration.
- T0159–T0160: mandatory subprocess runner, load-inclusive timeout, transactional
  context/sink, no late write after termination, next-stage continuation and real
  artist-dossier closure integration. The interim inline escape hatch is removed.
- T0169–T0170: clean current-user NSIS, broad-write ACL rejection, bundled relocated
  Python and enforced read-only project resources. Standard-token and real model
  generation scenarios remain outside the demonstrated installer test.
- T0179–T0180: export allowlist and separate Python consumer with randomized private
  canaries and malformed-message tests. Not represented as a human privacy audit.

Newest local stage/AI/terminal/function-budget selection: 43 passed. Combined
preflight/AI/stage/diagnostic/runtime selection before the dossier-specific added
integration test: 131 passed. No model inference was claimed by these selections.

## Bundled read-only installer result

Run 45103251845, source aaa296914c9fa8718edb161f6b27ee23629e9eb3:
all three Windows jobs SUCCESS, including real bundled-core NSIS installation,
installed Electron, explicit enforced write-deny ACL, relocated installed Python
running an isolated stage, uninstall and preserved external workspace sentinel.
https://github.com/ttklon/ZS-MUSIC-MAKER/actions/runs/45103251845

Earlier bundled runs 45102096941 and 45102520833 failed the clean installer step.
Their error details were not exposed by GitHub check annotations, and artifact/log
redirect downloads were unavailable from this workspace. The follow-up introduced
explicit failure annotations and increased the bounded per-operation wait from
120 to 300 seconds; that run succeeded. Do not claim a captured root-cause stack
for those earlier failures. Current source removes the interim inline isolation
bypass and adds the actual dossier-closure test after the successful run; a new
workflow run is required to certify that final source SHA as a whole.
