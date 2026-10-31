# -*- coding: utf-8 -*-
"""
updater/checks.py — проверка доступных обновлений.

Сеть по умолчанию запрещена: и `git ls-remote`, и запрос release-манифеста
выполняются только после явного `--online` или `network.online=true`.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from updater.paths import online_enabled, program_dir


def check_git_update_status(
    repo: Path | None = None, allow_online: bool = False
) -> dict[str, Any]:
    """Проверить remote revision without changing the working tree.

    ``git ls-remote`` is a network call, so it is skipped until ``--online``
    or ``network.online=true`` in settings explicitly permits it.
    """
    repo = Path(repo or program_dir())
    if not online_enabled(allow_online):
        return {
            "ok": True,
            "offline": True,
            "reason": "remote update check requires --online or network.online=true",
            "apply_performed": False,
        }
    try:
        def git(*args: str) -> str:
            return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()
        branch = git("branch", "--show-current") or "main"
        local = git("rev-parse", "HEAD")
        dirty = bool(git("status", "--porcelain"))
        remote_line = git("ls-remote", "origin", f"refs/heads/{branch}")
        remote = remote_line.split()[0] if remote_line else None
        relation = "unknown" if not remote else ("up_to_date" if remote == local else "update_available")
        return {"ok": True, "branch": branch, "local": local, "remote": remote,
                "relation": relation, "working_tree_clean": not dirty,
                "apply_performed": False}
    except Exception as exc:
        return {"ok": False, "reason": str(exc), "apply_performed": False}


def check_updates(release_url: str, allow_online: bool = False) -> dict[str, Any]:
    if not online_enabled(allow_online):
        return {
            "ok": True,
            "offline": True,
            "reason": "release check requires --online or network.online=true",
        }
    try:
        import urllib.request as urlreq

        with urlreq.urlopen(release_url, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"ok": False, "reason": str(e)}
    return {"ok": True, "data": data}
