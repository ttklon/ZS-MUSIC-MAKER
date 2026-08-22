from __future__ import annotations

import json
from pathlib import Path

from tools import release_preflight


def _write_release_root(root: Path, version: str = "39.9.0", mirror: str | None = None) -> None:
    (root / "version.json").write_text(json.dumps({"version": version}), encoding="utf-8")
    (root / "VERSION").write_text((mirror or version) + "\n", encoding="utf-8")
    (root / "pyproject.toml").write_text(
        '[project.scripts]\nzs-music-maker = "main:main"\n'
        '[tool.setuptools.dynamic]\nversion = {file = ["VERSION"]}\n',
        encoding="utf-8",
    )


def test_release_preflight_uses_current_source_version_and_read_only_invariants(
    tmp_path: Path, monkeypatch
) -> None:
    _write_release_root(tmp_path)
    answers = {
        ("branch", "--show-current"): "main",
        ("rev-parse", "HEAD"): "abc123",
        ("status", "--porcelain"): "",
        ("tag", "--list", "v39.9.0"): "",
        ("ls-remote", "--tags", "origin", "refs/tags/v39.9.0"): "",
    }
    monkeypatch.setattr(release_preflight, "_git", lambda *args: answers[args])

    report = release_preflight.collect_preflight(tmp_path)

    assert report["ok"] is True
    assert report["version"] == "39.9.0"
    assert report["proposed_tag"] == "v39.9.0"
    assert all(report["checks"].values())


def test_release_preflight_rejects_version_mirror_drift(tmp_path: Path, monkeypatch) -> None:
    _write_release_root(tmp_path, mirror="39.0.0")
    monkeypatch.setattr(release_preflight, "_git", lambda *_args: "" if _args[0] != "branch" else "main")

    report = release_preflight.collect_preflight(tmp_path)

    assert report["ok"] is False
    assert report["checks"]["version_mirror_matches"] is False
