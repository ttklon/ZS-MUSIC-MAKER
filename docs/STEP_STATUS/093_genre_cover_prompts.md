# PLAN_v39 — ШАГ 093: cover prompts for all genre presets

All **50** versioned files in `data/genre_presets/` now include `prompt_cover` and `cover_instruments`. Each `prompt_cover` is a renderable template that explicitly accepts `{genre}`, `{mood}`, `{key}` and `{instruments}`; the migration tool `tools/populate_cover_prompts.py` maintains these fields deterministically.

`tools/genre_validator.py` now enforces the cover metadata schema and required placeholders alongside existing genre fields. `modules/cover_art_ai.py` renders a preset-specific creative direction and passes it to the existing cover prompt builder for both SDXL and PIL fallback paths. `stage_cover` supplies the wizard key, so actual production prompt composition receives genre, mood, key and instrument context.

Acceptance: new 50-preset cover prompt regressions passed; `python tools/genre_validator.py` reported **50/50 preset assets**, **119 runtime genres**, and zero errors. Full `pytest tests/ -q` — **220 passed**; `compileall` successfully; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**. SDXL weights/runtime remain optional and were not claimed as executed.
