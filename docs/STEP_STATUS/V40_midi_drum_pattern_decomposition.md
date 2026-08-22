# APP_L v40 — MIDI drum-pattern decomposition

`MIDIGenerator.generate_drum_pattern()` mixed genre rhythm selection with mido object creation, MIDI file persistence and error handling. The audit classified the method as high complexity, and a failed real export used a bare console print.

The 16-step genre mapping now lives in pure `MIDIGenerator._drum_events()`. The export method retains the existing honest `""` return when `mido` is absent, creates MIDI events from the selected pattern when available, and logs failed export attempts instead of printing. Techno/house four-on-the-floor, drift-phonk kick/snare/cowbell positions, trap ranges and default pop-rock placements are preserved.

The focused tests exercise the pure selector without `mido`: they verify techno kick/hat positions, phonk cowbell/kick/snare positions and default hat velocity bounds. They do not create a MIDI file and do not claim that `mido` is installed or that an export ran.

Acceptance: focused MIDI pattern suite — **3 passed**. Full `pytest tests/ -q` — **272 passed**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **32 HIGH_COMPLEXITY** (from 33), **316 BARE_PRINT** (from 317), and **884 total heuristic records** across **223** Python files. The remaining MIDI bare prints are explicit CLI/self-test output outside the refactored export error path; raw audit JSON remains intentionally ignored.
