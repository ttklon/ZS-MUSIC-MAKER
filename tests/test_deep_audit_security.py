from __future__ import annotations

from pathlib import Path

from tools import deep_audit_v40


def _security_kinds(path: Path) -> list[str]:
    return [issue["kind"] for issue in deep_audit_v40.audit_file(path)["issues"]]


def test_security_audit_flags_direct_builtin_eval_and_exec(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "unsafe.py"
    source.write_text("value = eval('1 + 1')\nexec('answer = 42')\n", encoding="utf-8")
    monkeypatch.setattr(deep_audit_v40, "ROOT", tmp_path)

    kinds = _security_kinds(source)

    assert kinds.count("SECURITY_EVAL") == 2


def test_security_audit_does_not_flag_attribute_exec_event_loop(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "qt_loop.py"
    source.write_text("dialog.exec()\napplication.exec()\n", encoding="utf-8")
    monkeypatch.setattr(deep_audit_v40, "ROOT", tmp_path)

    assert "SECURITY_EVAL" not in _security_kinds(source)


def test_deep_audit_ignores_future_directives_but_keeps_real_dead_imports(
    tmp_path: Path, monkeypatch
) -> None:
    source = tmp_path / "imports.py"
    source.write_text(
        "from __future__ import annotations\nimport unused_module\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(deep_audit_v40, "ROOT", tmp_path)

    issues = deep_audit_v40.audit_file(source)["issues"]

    assert [issue["kind"] for issue in issues] == ["DEAD_IMPORT"]
    assert "unused_module" in issues[0]["msg"]


def test_deep_audit_honors_noqa_and_relative_reexport_imports(
    tmp_path: Path, monkeypatch
) -> None:
    source = tmp_path / "package_api.py"
    source.write_text(
        "from .submodule import public_api  # noqa: F401\n"
        "import optional_backend  # noqa\n"
        "import actually_unused\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(deep_audit_v40, "ROOT", tmp_path)

    issues = deep_audit_v40.audit_file(source)["issues"]

    assert [issue["kind"] for issue in issues] == ["DEAD_IMPORT"]
    assert "actually_unused" in issues[0]["msg"]


def test_path_audit_excludes_test_fixtures_but_keeps_production_literals(
    tmp_path: Path, monkeypatch
) -> None:
    production = tmp_path / "module.py"
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    fixture = tests_dir / "test_privacy.py"
    production.write_text('path = "/tmp/real-output.wav"\n', encoding="utf-8")
    fixture.write_text('secret_path = "/home/alice/private.txt"\n', encoding="utf-8")
    monkeypatch.setattr(deep_audit_v40, "ROOT", tmp_path)

    production_kinds = [issue["kind"] for issue in deep_audit_v40.audit_file(production)["issues"]]
    fixture_kinds = [issue["kind"] for issue in deep_audit_v40.audit_file(fixture)["issues"]]

    assert "HARDCODED_POSIX_PATH" in production_kinds
    assert "HARDCODED_POSIX_PATH" not in fixture_kinds
