# -*- coding: utf-8 -*-
"""ZS Music Maker — AST dead-imports аудит (ШАГ 010)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.ast_dead_imports import DEFAULT_DIRS, scan_all, scan_file  # noqa: E402


def test_scan_finds_dead_import(tmp_path):
    f = tmp_path / "m.py"
    f.write_text("import os\nimport json\nx = json.dumps({})\n", encoding="utf-8")
    dead = scan_file(f)
    names = {n for _, n in dead}
    assert "os" in names
    assert "json" not in names


def test_scan_ignores_noqa_import(tmp_path):
    f = tmp_path / "m.py"
    f.write_text("import os  # noqa: F401\nx = 1\n", encoding="utf-8")
    dead = scan_file(f)
    assert dead == []


def test_scan_keeps_attr_root(tmp_path):
    f = tmp_path / "m.py"
    f.write_text("import os\np = os.path.join('a', 'b')\nimport json\n", encoding="utf-8")
    dead = scan_file(f)
    names = {n for _, n in dead}
    assert "os" not in names
    assert "json" in names


def test_scan_line_with_two_imports(tmp_path):
    # `import os, sys` на одной строке — оба должны быть учтены
    f = tmp_path / "m.py"
    f.write_text("import os, sys\nx = 1\n", encoding="utf-8")
    dead = scan_file(f)
    names = {n for _, n in dead}
    assert {"os", "sys"} <= names


def test_repo_is_clean_of_dead_imports():
    report = scan_all(DEFAULT_DIRS)
    assert report == {}, f"dead imports found: {report}"
