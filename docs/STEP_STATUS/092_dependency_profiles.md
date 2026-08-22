# PLAN_v39 — ШАГ 092: base/AI/AMD dependency profiles

`pyproject.toml` now exposes aligned `ai` and `amd` extras. The AI extra mirrors `requirements_ai.txt`, including `xformers` (non-Darwin marker), Matchering and the Bark VCS declaration; the AMD extra mirrors `requirements_amd.txt` with `torch-directml`. Base dependencies remain aligned with `requirements.txt` and do **not** include torch, torchaudio, audiocraft, Demucs, XTTS, Whisper, Diffusers, xformers or DirectML.

The profile contract is tested by parsing both requirements manifests and `pyproject.toml` with standard-library `tomllib`. It verifies exact package-name parity for base, AI and AMD profiles, while allowing installers to decide when optional heavy packages are actually installed. No heavy packages were installed in this sandbox as part of this change.

Full `pytest tests/ -q` — **217 passed**; `compileall` successfully; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**.
