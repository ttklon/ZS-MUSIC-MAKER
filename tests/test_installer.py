from __future__ import annotations

import install


def test_installation_plan_keeps_ai_dependencies_opt_in() -> None:
    core = install.installation_plan(install_ai=False, system_deps=False)
    ai = install.installation_plan(install_ai=True, system_deps=False)

    assert len(core) == 1
    assert len(ai) == 2
    assert str(install.CORE_REQUIREMENTS) in core[0]
    assert str(install.AI_REQUIREMENTS) in ai[1]


def test_setup_dry_run_initialises_dirs_without_commands(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(install, "ROOT", tmp_path)
    monkeypatch.setattr(install, "CORE_REQUIREMENTS", tmp_path / "requirements.txt")
    monkeypatch.setattr(install, "AI_REQUIREMENTS", tmp_path / "requirements_ai.txt")
    monkeypatch.setattr(install, "run_cmd", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("must not run")))

    assert install.setup(install_ai=True, dry_run=True) == 0
    assert (tmp_path / "data" / "ai_models").is_dir()
    assert (tmp_path / "output" / "queue").is_dir()


def test_core_and_ai_constraints_share_safe_voice_and_text_dependencies() -> None:
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    core = (root / "requirements.txt").read_text(encoding="utf-8")
    ai = (root / "requirements_ai.txt").read_text(encoding="utf-8")
    metadata = (root / "pyproject.toml").read_text(encoding="utf-8")
    for line in ("huggingface_hub>=0.24.0,<2", "click>=8.0,<8.2"):
        assert line in core and line in ai and line in metadata
    assert "filelock>=3.32.7" in core and "filelock>=3.32.7" in metadata
