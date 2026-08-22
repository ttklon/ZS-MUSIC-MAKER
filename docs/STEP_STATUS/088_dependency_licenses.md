# PLAN_v39 — ШАГ 088: dependency license inventory

`tools/readiness.py --licenses` now parses direct declarations in `requirements.txt` and `requirements_ai.txt`, deduplicates shared packages while retaining their base/optional-AI groups, reads available distribution metadata through `importlib.metadata`, and regenerates `docs/LICENSES.md`. The report currently inventories **46 direct requirements**.

The generated table is intentionally evidentiary: installed package metadata is displayed as reported, while unavailable distributions are marked `UNKNOWN (distribution unavailable)` rather than assigned a guessed license. `docs/LICENSES.md` includes a GPL-compatibility checklist that distinguishes completed inventory work from review still required for unknown packages, transitive dependencies, bundled models and content licenses.

Acceptance covers base/AI/shared requirements, unavailable metadata behavior, deterministic Markdown generation and the real `python tools/readiness.py --licenses` command. Full `pytest tests/ -q` — **207 passed**; `compileall` successfully; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**.
