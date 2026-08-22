#!/usr/bin/env python3
"""Read-only preflight evidence for a ZS Music Maker release candidate."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _git(*args: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(ROOT), *args], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def collect_preflight(root: Path = ROOT) -> dict[str, Any]:
    """Collect non-mutating release invariants and the tag implied by source data."""
    try:
        version_data = json.loads((root / "version.json").read_text(encoding="utf-8"))
        version = str(version_data["version"])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {"ok": False, "reason": f"invalid version.json: {exc}", "checks": {}}

    version_mirror = (root / "VERSION").read_text(encoding="utf-8").strip() if (root / "VERSION").exists() else ""
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8") if (root / "pyproject.toml").exists() else ""
    branch = _git("branch", "--show-current")
    head = _git("rev-parse", "HEAD")
    dirty = _git("status", "--porcelain")
    tag = f"v{version}"
    local_tag = _git("tag", "--list", tag)
    remote_tag = _git("ls-remote", "--tags", "origin", f"refs/tags/{tag}")
    checks = {
        "branch_main": branch == "main",
        "version_mirror_matches": version_mirror == version,
        "pyproject_uses_version_mirror": 'version = {file = ["VERSION"]}' in pyproject,
        "console_entrypoint_declared": 'zs-music-maker = "main:main"' in pyproject,
        "working_tree_clean": dirty == "",
        "release_tag_available": not local_tag and not remote_tag,
    }
    return {
        "ok": all(checks.values()),
        "version": version,
        "proposed_tag": tag,
        "head": head,
        "branch": branch,
        "checks": checks,
        "tag_state": "available" if checks["release_tag_available"] else "already exists",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only release preflight for the current source version")
    parser.add_argument("--json", action="store_true", help="Print machine-readable evidence")
    args = parser.parse_args(argv)
    report = collect_preflight()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"release preflight: version={report.get('version')} tag={report.get('proposed_tag')}")
        for name, passed in report.get("checks", {}).items():
            print(f"  {'PASS' if passed else 'FAIL'} {name}")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
