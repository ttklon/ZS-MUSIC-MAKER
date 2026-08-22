# PLAN_v39 — ШАГ 097: колесо и чистый venv

`pyproject.toml` now exposes the stable `zs-music-maker` console command and ships `main.py`/`install.py` as wheel modules. An isolated build cannot safely evaluate arbitrary runtime code for dynamic metadata, so the project uses a plain `VERSION` mirror for setuptools metadata. The canonical source release record remains `version.json`; a regression test requires exact equality between both files.

`app.version_info` retains source-checkout behavior via `version.json` and falls back to installed distribution metadata only when executing from a wheel. Consequently, `--version` works without audio, GUI or AI dependencies installed.

Acceptance installed the `build` prerequisite, ran `python3 -m build` into `/tmp/zsmm-step097-dist`, created `/tmp/zsmm-step097-venv`, and installed the produced wheel with `pip install --no-deps`. Dependency resolution was intentionally disabled because this test verifies wheel packaging and CLI availability; production dependencies remain declared in the wheel metadata. Both `zs-music-maker --version` and, from outside the source tree, `python -m main --version` reported **39.9.0** from the installed wheel. Full `pytest tests/ -q` — **230 passed**; `compileall` successful; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**.
