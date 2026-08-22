# PLAN_v39 — ШАГ 074: память плана и финализация integrity

`tools/plan_integrity.py` now validates the plan as an immutable UTF-8 artifact without modifying it. It strictly decodes UTF-8, checks the final newline, extracts the primary headings using the same `ШАГ NNN — title` grammar as the execution report and requires the exact ordered sequence 001–100. It also records reproducible byte, character, line and SHA-256 measurements.

Measured authoritative plan evidence:

| Metric | Value |
|---|---:|
| UTF-8 strict decode | PASS |
| Primary steps | 100, ordered 001–100 |
| Bytes | 3,595,003 |
| Characters | 2,419,839 |
| Lines | 26,254 |
| SHA-256 | `84c048cd1b223cd375ad2bcac01e8cef9d92bb09f934414d18d28c9e31775e87` |

Acceptance: targeted integrity tests — **2 passed**, including rejection of a 99-step plan. Full `pytest tests/ -q` — **237 passed**; `compileall` successful; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**. The SHA-256 is an evidence value for this exact finalisation revision and must be intentionally regenerated if the plan source changes.
