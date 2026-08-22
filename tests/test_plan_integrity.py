from __future__ import annotations

from pathlib import Path

from tools.plan_integrity import measure_plan


def _primary_plan_text(count: int = 100) -> str:
    return "\n".join(f"ШАГ {number:03d} — Проверка {number}" for number in range(1, count + 1)) + "\n"


def test_plan_integrity_measures_strict_utf8_complete_primary_steps(tmp_path: Path) -> None:
    plan = tmp_path / "plan.txt"
    plan.write_text(_primary_plan_text(), encoding="utf-8")

    report = measure_plan(plan)

    assert report["ok"] is True
    assert report["primary_step_count"] == 100
    assert report["first_step"] == 1 and report["last_step"] == 100
    assert report["checks"] == {
        "utf8_strict": True,
        "newline_at_eof": True,
        "primary_steps_exact_001_to_100": True,
    }
    assert len(report["sha256"]) == 64


def test_plan_integrity_rejects_missing_primary_step(tmp_path: Path) -> None:
    plan = tmp_path / "broken.txt"
    plan.write_text(_primary_plan_text(99), encoding="utf-8")

    report = measure_plan(plan)

    assert report["ok"] is False
    assert report["primary_step_count"] == 99
    assert report["checks"]["primary_steps_exact_001_to_100"] is False
