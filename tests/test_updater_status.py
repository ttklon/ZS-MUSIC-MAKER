from __future__ import annotations

import subprocess

from updater.updater import check_git_update_status


def test_git_update_status_is_read_only(tmp_path, monkeypatch) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_output(command, text=True):
        args = tuple(command[3:])
        calls.append(args)
        answers = {
            ("branch", "--show-current"): "main\n",
            ("rev-parse", "HEAD"): "abc123\n",
            ("status", "--porcelain"): "",
            ("ls-remote", "origin", "refs/heads/main"): "abc123\trefs/heads/main\n",
        }
        return answers[args]

    monkeypatch.setattr(subprocess, "check_output", fake_output)
    report = check_git_update_status(tmp_path, allow_online=True)

    assert report["ok"] is True
    assert report["relation"] == "up_to_date"
    assert report["working_tree_clean"] is True
    assert report["apply_performed"] is False
    assert all(command[0] not in {"fetch", "pull", "reset", "checkout"} for command in calls)


def test_install_rolls_back_when_smoke_process_cannot_start(tmp_path, monkeypatch) -> None:
    """A launch failure must not report the replaced installation as accepted."""
    import zipfile

    from updater import updater

    program = tmp_path / "program"
    program.mkdir()
    (program / "old.txt").write_text("old", encoding="utf-8")
    staging = tmp_path / "staging"
    backup = tmp_path / "backup.zip"
    package = tmp_path / "release.zip"
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("main.py", "print('new')\n")
        archive.writestr("version.json", '{"version": "test"}')

    monkeypatch.setattr(updater, "program_dir", lambda: program)
    monkeypatch.setattr(updater, "staging_dir", lambda: staging)
    monkeypatch.setattr(updater, "verify_zip", lambda *_args: {"ok": True})
    monkeypatch.setattr(updater, "make_backup", lambda **_kwargs: backup)
    monkeypatch.setattr(updater, "_stash_user_data", lambda *_args: {})
    monkeypatch.setattr(updater, "_restore_user_data", lambda *_args: [])
    monkeypatch.setattr(updater, "rollback_last", lambda: {"ok": True})

    def fail_to_start(*_args, **_kwargs):
        raise OSError("launcher unavailable")

    monkeypatch.setattr(updater.subprocess, "run", fail_to_start)

    result = updater.install_from_zip(str(package), smoke_test=True)

    assert result["ok"] is False
    assert result["stage"] == "smoke_test"
    assert result["rolled_back"] is True
    assert result["error"] == "smoke launch failed: OSError: launcher unavailable"
