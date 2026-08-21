# PLAN_v39 — ШАГ 083: five-slot beat constructor и MIDI plan

`modules/beat_constructor.py` теперь содержит explicit 16-step genre presets for **kick, snare, hat, bass, melody** across phonk, trap and house/techno. `BeatConstructor(genre=...)` uses these five independent slots; groove `*_pattern` values remain supported overrides. `build_slot_plan(bars)` exposes deterministic events, and build results include `slot_plan`. Bass is no longer implicitly tied to the kick in the phonk preset.

To preserve the pre-existing default audio contract, constructor calls without `genre` use a `legacy` preset that retains original kick/bass/hat semantics. This was necessary because the committed golden beat regression correctly detected a material RMS change during the initial migration. The reusable `construct_beat()` wrapper passes genre/style explicitly, so new genre-aware callers receive five-slot presets while legacy default paths remain deterministic.

`modules/midi_generator.py` adds `slot_events_for_genre()` and `MIDIGenerator.export_slot_pattern()`. When `mido` is available it writes one track per slot; in this sandbox `mido` is unavailable and it returns an honest `BLOCKED` response while still exposing the deterministic event plan.

Acceptance: five-slot plans contain 128 steps per slot for eight bars; an 8-bar phonk section renders stereo in under 5 seconds; existing golden rerender remains within its 5% audio tolerance. Full `pytest tests/ -q` — **193 passed**; `compileall` successfully; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**.
