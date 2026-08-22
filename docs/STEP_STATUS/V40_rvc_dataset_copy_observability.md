# APP_L v40 — RVC dataset-copy observability

RVC training prepares a dataset by copying eligible Voice Vault recordings. Previously, a filesystem copy failure was silently ignored: the failed clip was not counted, but neither the trainer nor an operator had any evidence why the collected dataset was smaller than expected.

`RVCTrainer` now records typed `dataset_copy_errors` during the existing dataset-preparation flow. A failed copy is not counted as a collected clip and does not imply training success or a valid RVC dataset; the dataset directory return contract remains unchanged. The listener-observability field remains separate from this transfer evidence.

Focused regression simulates `disk full` while collecting one real temporary source file. It verifies the dataset path contract and the explicit error record without running a backend or training a model.

Acceptance: focused RVC dataset-copy suite — **1 passed**. Full `pytest tests/ -q` — **309 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **92 SILENT_EXCEPT_PASS** (from 93). The selected dataset-copy record is removed; separate RVC backend-probe and progress-parser records remain. The audit reports **882 total heuristic records** across **245** Python files. Raw audit JSON remains intentionally ignored.
