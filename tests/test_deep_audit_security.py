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
