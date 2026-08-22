from __future__ import annotations

from types import SimpleNamespace

from tools import readiness


def test_plan_v39_contains_exactly_one_hundred_ordered_step_headings() -> None:
    steps = readiness.planned_v39_steps()

    assert len(steps) == 100
    assert [row["step"] for row in steps] == [f"{number:03d}" for number in range(1, 101)]


def test_git_evidence_parser_expands_explicit_step_ranges(monkeypatch) -> None:
    output = "a" * 40 + "\x1fPLAN_v39 ШАГИ 018-022: grouped acceptance\n" + "b" * 40 + "\x1fPLAN_v39 ШАГ 089: execution report\n"
    monkeypatch.setattr(readiness.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(stdout=output))

    found = readiness.git_step_commits()

    assert set(found) == {"018", "019", "020", "021", "022", "089"}
    assert found["020"][0]["subject"].endswith("grouped acceptance")


def test_execution_report_marks_only_git_evidenced_steps(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(readiness, "planned_v39_steps", lambda: [
        {"step": "001", "title": "first"},
        {"step": "002", "title": "second"},
    ])
    monkeypatch.setattr(readiness, "git_step_commits", lambda: {"001": [{"commit": "abc12345", "subject": "ШАГ 001: done"}]})

    report = readiness.execution_report_markdown()
    target = readiness.write_execution_report(tmp_path / "report.md")

    assert "Plan headings: **2**. Git-evidenced commits: **1**. Pending headings: **1**." in report
    assert "| 001 | first | COMMITTED | `abc12345` ШАГ 001: done |" in report
    assert "| 002 | second | PENDING | — |" in report
    assert target.read_text(encoding="utf-8") == report


def test_report_cli_writes_execution_report(capsys, monkeypatch, tmp_path) -> None:
    target = tmp_path / "PLAN_v39_EXEC_REPORT.md"
    monkeypatch.setattr(readiness, "EXECUTION_REPORT_PATH", target)

    assert readiness.main(["--report"]) == 0
    output = capsys.readouterr().out

    assert "execution report:" in output
    assert target.exists()
