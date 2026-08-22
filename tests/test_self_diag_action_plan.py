from __future__ import annotations

from modules.self_diag_v13 import collect_action_plan


def test_action_plan_preserves_severity_guidance_and_advice_limits() -> None:
    plan = collect_action_plan(
        layout=[
            {"severity": "red", "path": "required.py", "message": "missing"},
            {"severity": "yellow", "path": "output/", "message": "created later"},
        ],
        health={"verdict": "YELLOW", "advice": [f"health {index}" for index in range(7)]},
        kpi={"verdict": "RED", "percent_tz": 62, "advice": [f"kpi {index}" for index in range(5)]},
        smoke={"passed": 12, "failed": 2, "total": 14},
    )

    rendered = "\n".join(plan)
    assert "required.py  —  missing" in rendered
    assert "output/" in rendered
    assert "Стек работает, но без этих модулей качество ниже" in rendered
    assert "health 4" in rendered
    assert "health 5" not in rendered
    assert "Готовность ТЗ 62% — нужно доработать модули" in rendered
    assert "kpi 2" in rendered
    assert "kpi 3" not in rendered
    assert "Smoke 12/14 PASS, 2 FAIL" in rendered


def test_action_plan_keeps_all_clear_fallback_for_unknown_empty_reports() -> None:
    plan = collect_action_plan([], {"verdict": "?"}, {"verdict": "?"}, {"total": 0})

    assert plan == ["🟢 Все системы в порядке. Запускай wizard!"]
