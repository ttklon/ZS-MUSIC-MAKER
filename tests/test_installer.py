from __future__ import annotations

import install


def test_installation_plan_keeps_ai_dependencies_opt_in() -> None:
    core = install.installation_plan(install_ai=False, system_deps=False)
    ai = install.installation_plan(install_ai=True, system_deps=False)

    assert len(core) == 2
    assert len(ai) == 3
    assert str(install.CORE_REQUIREMENTS) in core[0]
    assert str(install.AI_REQUIREMENTS) in ai[1]
    assert core[-1][-2:] == ["pip", "check"] and ai[-1][-2:] == ["pip", "check"]


def test_setup_dry_run_does_not_change_filesystem_or_run_commands(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(install, "ROOT", tmp_path)
    monkeypatch.setattr(install, "CORE_REQUIREMENTS", tmp_path / "requirements.txt")
    monkeypatch.setattr(install, "AI_REQUIREMENTS", tmp_path / "requirements_ai.txt")
    monkeypatch.setattr(install, "run_cmd", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("must not run")))

    assert install.setup(install_ai=True, dry_run=True) == 0
    assert list(tmp_path.iterdir()) == []


def test_core_and_ai_constraints_share_safe_voice_and_text_dependencies() -> None:
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    core = (root / "requirements.txt").read_text(encoding="utf-8")
    ai = (root / "requirements_ai.txt").read_text(encoding="utf-8")
    metadata = (root / "pyproject.toml").read_text(encoding="utf-8")
    for line in ("huggingface_hub>=0.24.0,<2", "click>=8.0,<8.2"):
        assert line in core and line in ai and line in metadata
    assert "filelock>=3.32.7" in core and "filelock>=3.32.7" in metadata


def test_setup_initialises_and_checks_dependencies_when_not_dry(tmp_path, monkeypatch):
    monkeypatch.setattr(install, "ROOT", tmp_path)
    (tmp_path / ".env.example").write_text("EXAMPLE=1\n", encoding="utf-8")
    calls = []
    monkeypatch.setattr(install, "run_cmd", lambda cmd, critical: calls.append((cmd, critical)) or True)
    assert install.setup(install_ai=True) == 0
    assert (tmp_path / "voice_vault").is_dir() and (tmp_path / ".env").is_file()
    assert len(calls) == 3 and calls[-1][0][-2:] == ["pip", "check"]
    assert all(critical for _, critical in calls)
