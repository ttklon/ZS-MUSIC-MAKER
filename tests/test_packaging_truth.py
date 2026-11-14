"""T21: упаковка и зависимости — один источник правды каждое.

Что было не так:

* CI собирал `--onefile --add-data ...` в обход `packaging/zsmm.spec`, который
  аргументирует onedir. Два места задавали состав сборки, и они расходились:
  spec тянул `config/`, `models/`, `scripts/`, CI — нет.
* `tools/quality_gate.sh` требовал `mypy`/`pylint`, которых нет ни в одном
  requirements, и печатал «10/10 SCORE», ничего не проверив.
* `requirements.txt` содержал 8 пакетов без единого импорта.

Здесь фиксируется результат, а не намерение.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "build.yml"
SPEC = ROOT / "packaging" / "zsmm.spec"
REQUIREMENTS = ROOT / "requirements.txt"
QUALITY_GATE = ROOT / "tools" / "quality_gate.sh"

# Пакеты, убранные из requirements: ни одного импорта в прод-коде.
REMOVED_PACKAGES = ("matplotlib", "audioread", "omegaconf", "tqdm", "plyer", "mingus")


def test_ci_builds_from_the_spec() -> None:
    """CI не передаёт свой состав сборки — только spec."""
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "packaging/zsmm.spec" in text
    assert "--onefile" not in text, "workflow снова собирает в обход spec"


def test_ci_uploads_the_onedir_output() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "dist/ZS Music Maker/" in text, "onedir-сборка должна уезжать каталогом"
    assert "ZS-Music-Maker.exe" not in text


def test_spec_documents_the_real_default() -> None:
    text = SPEC.read_text(encoding="utf-8")

    assert "onedir" in text
    assert "ZSMM_ONEFILE" in text


@pytest.mark.parametrize("package", REMOVED_PACKAGES)
def test_unused_packages_left_requirements(package: str) -> None:
    lines = [
        line.split("#", 1)[0].strip().lower()
        for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines()
    ]
    declared = [line for line in lines if line.startswith(package)]

    assert not declared, f"{package} снова в requirements без импортов в коде"


def test_requirements_keep_what_is_really_used() -> None:
    text = REQUIREMENTS.read_text(encoding="utf-8")

    for package in ("soundfile", "librosa", "scipy", "numpy", "pedalboard", "mutagen"):
        assert re.search(rf"^{package}[><=]", text, re.MULTILINE), package


def test_quality_gate_no_longer_claims_fake_success() -> None:
    text = QUALITY_GATE.read_text(encoding="utf-8")

    assert "10/10" not in text
    assert "QUALITY GATE PASSED" not in text
    assert "exit 2" in text, "заглушка обязана честно сообщать об отказе"
    assert "python -m pytest tests/" in text, "заглушка называет реальные команды"
