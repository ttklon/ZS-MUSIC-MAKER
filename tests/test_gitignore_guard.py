# -*- coding: utf-8 -*-
"""Сторож .gitignore: код проекта не должен молча выпадать из репозитория."""

from __future__ import annotations

from tools import gitignore_guard


def test_no_project_code_is_hidden_by_gitignore() -> None:
    report = gitignore_guard.audit()

    assert report["ok"] is True, (
        "эти пути игнорируются .gitignore: "
        + ", ".join(report["ignored_protected_paths"])
        + " — используйте якорный шаблон (/release/ вместо release/)"
    )


def test_guard_protects_every_code_root() -> None:
    roots = set(gitignore_guard.PROTECTED_ROOTS)
    assert {"app/", "modules/", "tools/", "tests/", "updater/"} <= roots
