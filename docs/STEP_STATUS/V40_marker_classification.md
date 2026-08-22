# APP_L v40 — actionable comment marker classification

The two `MARKER_XXX` findings were not unresolved product work. They were ISRC placeholder explanations (`XX-XXX-00-00000`) in comments, where `XXX` is a required registrant-code field in the ISO identifier format. The prior audit searched marker text anywhere in a comment and therefore misclassified domain prose as a task marker.

`tools/deep_audit_v40.py` now recognizes a marker only when it begins the comment label, such as `# TODO:` or `# FIXME -`. The focused regression verifies that an explicit `# TODO:` is retained while an ISRC comment is excluded. A fresh audit contains **0 marker findings**, **2 global statements** and **913 total heuristic findings across 210 files**.

Acceptance: focused deep-audit tests — **7 passed**. Full `pytest tests/ -q` — **249 passed**; `compileall` successful; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**.
