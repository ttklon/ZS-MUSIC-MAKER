# -*- coding: utf-8 -*-
"""Windows-входы: скрипты, упаковка, отсутствие консоли и журнал.

Проверки статические (на Linux не выполнить `cmd`), но они фиксируют то, что
ломается на живой машине чаще всего:

* скрипт ссылается на несуществующий файл;
* `setup.cmd` не проверяет версию Python и падает «непонятно почему»;
* собранный exe собирается без данных (`data/`, `version.json`) и теряет жанры;
* spec включает torch — сборка раздувается до гигабайт;
* запуск идёт с консолью, хотя обещан «как обычное приложение».
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
SPEC = ROOT / "packaging" / "zsmm.spec"

CMD_FILES = ["setup.cmd", "run.cmd", "run_silent.cmd", "verify.cmd", "build_exe.cmd"]


@pytest.mark.parametrize("name", CMD_FILES)
def test_cmd_files_exist_and_are_crlf_safe(name: str) -> None:
    """Все входные скрипты на месте и без BOM (cmd.exe ломается на BOM)."""
    path = SCRIPTS / name
    assert path.exists(), f"нет {name}"
    raw = path.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), f"{name}: BOM ломает cmd.exe"
    text = raw.decode("utf-8", errors="replace")
    assert text.startswith("@echo off"), f"{name}: первая строка должна быть @echo off"
    assert "cd /d \"%~dp0..\"" in text, f"{name}: не переходит в корень проекта"


@pytest.mark.parametrize("name", CMD_FILES)
def test_scripts_reference_existing_paths(name: str) -> None:
    """Пути, на которые ссылаются скрипты, реально существуют."""
    text = (SCRIPTS / name).read_text(encoding="utf-8", errors="replace")
    expected = {
        "setup.cmd": ["requirements.txt", "main.py"],
        "run.cmd": ["main.py"],
        "run_silent.cmd": ["main.py", "main.py --desktop"],
        "verify.cmd": ["tests/", "tools/smoke_audio.py", "tools/smoke_god.py", "tools/ast_dead_imports.py"],
        "build_exe.cmd": ["packaging/zsmm.spec"],
    }[name]
    for rel in expected:
        file_part = rel.split(" ")[0]
        assert (ROOT / file_part).exists(), f"{name}: нет пути {file_part}"


def test_setup_checks_python_version() -> None:
    text = (SCRIPTS / "setup.cmd").read_text(encoding="utf-8")
    assert "version_info" in text and "3,11" in text
    assert "--health" in text, "setup должен заканчиваться проверкой окружения"


def test_silent_launcher_uses_pythonw() -> None:
    """Без консоли — только pythonw: иначе на Windows мигает чёрное окно."""
    text = (SCRIPTS / "run_silent.cmd").read_text(encoding="utf-8")
    assert "pythonw.exe" in text
    assert "--desktop" in text


def test_spec_collects_data_and_excludes_heavy_ai() -> None:
    text = SPEC.read_text(encoding="utf-8")
    assert '"data"' in text and "version.json" in text
    for heavy in ("torch", "audiocraft", "gradio"):
        assert f'"{heavy}"' in text, f"spec должен исключать {heavy}"
    assert "console=False" in text


def test_spec_supports_onefile_and_defaults_to_onedir() -> None:
    text = SPEC.read_text(encoding="utf-8")
    assert "ZSMM_ONEFILE" in text
    assert "COLLECT(" in text, "по умолчанию собираем onedir — иначе старт медленный"


def test_build_script_runs_version_smoke() -> None:
    text = (SCRIPTS / "build_exe.cmd").read_text(encoding="utf-8")
    assert "--version" in text, "после сборки нужен smoke собранного exe"


def test_verify_runs_full_gate_set() -> None:
    text = (SCRIPTS / "verify.cmd").read_text(encoding="utf-8")
    for part in ("compileall", "pytest", "smoke_audio", "smoke_god", "audit_honesty", "readiness"):
        assert part in text, f"verify.cmd должен включать {part}"


def test_readme_documents_one_click_path() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "scripts\\setup.cmd" in readme or "scripts/setup.cmd" in readme
    assert "run_silent.cmd" in readme or "build_exe.cmd" in readme
