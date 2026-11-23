# -*- coding: utf-8 -*-
"""Репозиторий не должен тихо толстеть.

Поводом стал реальный случай: восемь демо-WAV на 55 МБ жили в `demo_site/`,
не были нужны ни одному тесту, и каждый клон тащил их за собой. Тест держит
границу: артефакты рендера — вне git, фикстуры тестов — с запасом внутри порога.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from tools import size_guard

ROOT = Path(__file__).resolve().parents[1]


def test_no_tracked_file_is_oversized() -> None:
    report = size_guard.audit()
    assert report["oversized"] == [], (
        "в git появились крупные файлы — это почти всегда артефакт рендера: "
        + ", ".join(f"{item['path']} ({item['mb']} МБ)" for item in report["oversized"])
    )


def test_repository_stays_under_total_budget() -> None:
    report = size_guard.audit()
    assert report["total_ok"], (
        f"отслеживаемое занимает {report['total_mb']} МБ при пороге {report['max_total_mb']} МБ"
    )


def test_demo_audio_is_not_versioned() -> None:
    """Демо-WAW генерируются, а не версионируются: 55 МБ за непроверяемый звук."""
    result = subprocess.run(
        ["git", "ls-files", "demo_site/*.wav"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.stdout.strip() == "", f"демо-WAV вернулись в git: {result.stdout.strip()}"


def test_test_fixtures_are_still_tracked() -> None:
    """Обратная сторона: фикстуры тестов удалять нельзя — тесты на них держатся."""
    result = subprocess.run(
        ["git", "ls-files", "tests/fixtures/audio/"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.stdout.strip(), "аудио-фикстуры тестов исчезли из git"
