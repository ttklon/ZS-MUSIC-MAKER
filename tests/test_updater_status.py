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
    report = check_git_update_status(tmp_path)

    assert report["ok"] is True
    assert report["relation"] == "up_to_date"
    assert report["working_tree_clean"] is True
    assert report["apply_performed"] is False
    assert all(command[0] not in {"fetch", "pull", "reset", "checkout"} for command in calls)
