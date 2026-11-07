# -*- coding: utf-8 -*-
"""`modules/self_diag.py`: диагностика для человека и её обещания.

Это то, что пользователь видит по `main.py --self-diag`: цветная сводка,
Action Plan и запись в `logs/self_diag.txt`. Покрытие было 45 % — проверялся
рендер, а решения («что считать сломанным», «что советовать») нет.

Главное, что здесь держится: список обязательных путей не должен требовать
того, чего в проекте быть не может. Нашлось, что диагностика требовала
`modules/mastering.py`, хотя мастеринг живёт в пакете `modules/mastering/`, а
`test_code_hygiene.py` прямо запрещает возвращать одиночный файл. То есть
пользователь получал «🔴 СРОЧНО: восстановить недостающие файлы» по здоровой
установке.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from modules import self_diag


@pytest.fixture
def root(tmp_path, monkeypatch) -> Path:
    """Свой корень проекта: настоящий репозиторий диагностика не трогает."""
    (tmp_path / "logs").mkdir()
    monkeypatch.setattr(self_diag, "ROOT", tmp_path)
    monkeypatch.setattr(self_diag, "LOGS", tmp_path / "logs")
    return tmp_path


def _touch(root: Path, rel: str) -> None:
    """Путь с «/» на конце — каталог, иначе файл; родители создаются."""
    target = root / rel
    if rel.endswith("/"):
        target.mkdir(parents=True, exist_ok=True)
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("x", encoding="utf-8")


# --------------------------------------------------------------------------- #
#  Обязательные пути
# --------------------------------------------------------------------------- #

def test_expected_paths_do_not_demand_forbidden_single_file() -> None:
    """`modules/mastering.py` запрещён тестом гигиены: это пакет, не файл."""
    declared = {rel for rel, _need, _descr in self_diag.EXPECTED_PATHS}

    assert "modules/mastering.py" not in declared
    assert "modules/mastering/__init__.py" in declared


def test_every_declared_path_exists_in_the_real_project() -> None:
    """Список обязательных путей обязан сходиться с репозиторием.

    Исключение — пути `FLEX`: они создаются при первом запуске.
    """
    project = Path(__file__).resolve().parents[1]
    missing = [
        rel for rel, need, _descr in self_diag.EXPECTED_PATHS
        if need == "OK" and not (project / rel).exists()
    ]

    assert not missing, f"self_diag требует несуществующие пути: {missing}"


def test_layout_reports_missing_required_path_as_red(root) -> None:
    for rel, need, _descr in self_diag.EXPECTED_PATHS:
        if need == "OK" and rel != "main.py":
            _touch(root, rel)

    rows = {row["path"]: row for row in self_diag.check_layout()}

    assert rows["main.py"]["severity"] == "red"
    assert rows["main.py"]["status"] == "MISSING"
    assert "нужно создать" in rows["main.py"]["message"]


def test_flexible_paths_are_never_red(root) -> None:
    """Необязательный путь — либо зелёный (есть), либо жёлтый (создастся)."""
    rows = {row["path"]: row for row in self_diag.check_layout()}

    flex = [rel for rel, need, _descr in self_diag.EXPECTED_PATHS if need == "FLEX"]
    assert flex, "в списке должен быть хотя бы один необязательный путь"
    for rel in flex:
        assert rows[rel]["severity"] in {"green", "yellow"}
        assert rows[rel]["status"] in {"PRESENT", "AUTO"}


def test_absent_flexible_path_is_yellow_with_explanation(root) -> None:
    rows = {row["path"]: row for row in self_diag.check_layout()}

    absent = [
        rel for rel, need, _descr in self_diag.EXPECTED_PATHS
        if need == "FLEX" and not (root / rel).exists()
    ]
    assert absent, "нужен хотя бы один отсутствующий необязательный путь"
    for rel in absent:
        assert rows[rel]["severity"] == "yellow"
        assert rows[rel]["status"] == "AUTO"
        assert "первом запуске" in rows[rel]["message"]


def test_complete_layout_is_all_green(root) -> None:
    for rel, _need, _descr in self_diag.EXPECTED_PATHS:
        _touch(root, rel)

    rows = self_diag.check_layout()

    assert all(row["severity"] == "green" for row in rows)
    present = {row["path"]: row["status"] for row in rows if row["path"].endswith("/")}
    assert set(present.values()) <= {"PRESENT", "OK"}


# --------------------------------------------------------------------------- #
#  Чтение отчётов
# --------------------------------------------------------------------------- #

def test_broken_json_is_none_not_crash(root) -> None:
    (root / "data").mkdir()
    (root / "data" / "health.json").write_text("{ битый", encoding="utf-8")

    assert self_diag.check_health() is None


def test_health_and_kpi_are_read(root) -> None:
    (root / "data").mkdir()
    (root / "data" / "health.json").write_text(json.dumps({"verdict": "GREEN"}), encoding="utf-8")
    (root / "data" / "kpi_dashboard.json").write_text(json.dumps({"verdict": "YELLOW"}), encoding="utf-8")

    assert self_diag.check_health()["verdict"] == "GREEN"
    assert self_diag.check_kpi()["verdict"] == "YELLOW"


def test_smoke_report_prefers_newest_name(root) -> None:
    (root / "logs" / "smoke_v12_report.json").write_text('{"total": 1}', encoding="utf-8")
    (root / "logs" / "smoke_audio_report.json").write_text('{"total": 2}', encoding="utf-8")

    assert self_diag.check_smoke_recent()["total"] == 2


def test_smoke_report_falls_back_to_legacy_name(root) -> None:
    (root / "logs" / "smoke_v12_report.json").write_text('{"total": 3}', encoding="utf-8")

    assert self_diag.check_smoke_recent()["total"] == 3


def test_missing_smoke_report_is_none(root) -> None:
    assert self_diag.check_smoke_recent() is None


# --------------------------------------------------------------------------- #
#  Action Plan
# --------------------------------------------------------------------------- #

def _layout(*rows) -> list[dict]:
    return [
        {"path": path, "status": status, "message": message, "severity": severity}
        for path, status, message, severity in rows
    ]


def test_plan_lists_missing_files_first() -> None:
    plan = self_diag.collect_action_plan(
        _layout(("main.py", "MISSING", "нет", "red"), ("logs/", "AUTO", "создастся", "yellow")),
        {"verdict": "GREEN"},
        {"verdict": "GREEN", "percent_tz": 99},
        {"passed": 6, "failed": 0, "total": 6},
    )

    assert "СРОЧНО" in plan[0]
    assert any("main.py" in line for line in plan)
    assert any("появятся автоматически" in line for line in plan)


def test_plan_asks_to_run_health_when_absent() -> None:
    plan = self_diag.collect_action_plan([], None, None, None)

    assert any("health" in line for line in plan)
    assert any("KPI" in line for line in plan)
    assert any("Smoke" in line for line in plan)


def test_plan_for_red_health_lists_advice() -> None:
    plan = self_diag.collect_action_plan(
        [], {"verdict": "RED", "advice": ["поставь numpy", "поставь scipy"]}, None, None
    )

    assert any("health RED" in line for line in plan)
    assert any("поставь numpy" in line for line in plan)


def test_plan_caps_health_advice_at_five() -> None:
    advice = [f"шаг {i}" for i in range(9)]

    plan = self_diag.collect_action_plan([], {"verdict": "YELLOW", "advice": advice}, None, None)

    assert sum(1 for line in plan if line.strip().startswith("· шаг")) == 5


def test_plan_celebrates_full_readiness() -> None:
    plan = self_diag.collect_action_plan(
        [], {"verdict": "GREEN"}, {"verdict": "GREEN", "percent_tz": 97}, None
    )

    assert any("Готовность ТЗ 97%" in line for line in plan)


def test_plan_for_low_readiness_names_modules() -> None:
    plan = self_diag.collect_action_plan(
        [], None,
        {"verdict": "RED", "percent_tz": 40, "advice": ["модуль A", "модуль B", "модуль C", "модуль D"]},
        None,
    )

    assert any("нужно доработать" in line for line in plan)
    assert sum(1 for line in plan if line.strip().startswith("· модуль")) == 3


def test_plan_reports_failed_smoke() -> None:
    plan = self_diag.collect_action_plan(
        [], None, None, {"passed": 5, "failed": 1, "total": 6}
    )

    assert any("5/6" in line and "1 FAIL" in line for line in plan)


def test_plan_for_empty_smoke_does_not_claim_success() -> None:
    """Отчёт с total=0 не должен звучать как «стабильно»."""
    plan = self_diag.collect_action_plan([], None, None, {"passed": 0, "failed": 0, "total": 0})

    assert not any("стабильно" in line for line in plan)


def test_plan_is_never_empty() -> None:
    plan = self_diag.collect_action_plan(
        _layout(("main.py", "OK", "ок", "green")),
        {"verdict": "GREEN"},
        {"verdict": "GREEN", "percent_tz": 100},
        {"passed": 8, "failed": 0, "total": 8},
    )

    assert plan, "пустой план не показывается пользователю"
    assert any("в порядке" in line or "отлично" in line for line in plan)


def test_unknown_health_verdict_is_not_translated_into_good_news() -> None:
    plan = self_diag.collect_action_plan([], {"verdict": "WEIRD"}, None, None)

    assert not any("Стек в порядке" in line for line in plan)


# --------------------------------------------------------------------------- #
#  Отчёт и запуск
# --------------------------------------------------------------------------- #

def test_report_contains_summary_plan_and_table(root) -> None:
    layout = self_diag.check_layout()

    text = self_diag.render_report(layout, {"verdict": "GREEN", "percent_ready": 90},
                                   {"verdict": "YELLOW", "percent_tz": 70},
                                   {"passed": 6, "failed": 0, "total": 6},
                                   ["сделай это"])

    assert "Self-Diagnostic" in text
    assert "Что делать дальше:" in text
    assert "сделай это" in text
    assert "Структура проекта" in text
    assert "GREEN (90%)" in text


def test_report_survives_all_reports_missing(root) -> None:
    text = self_diag.render_report(self_diag.check_layout(), None, None, None, ["план"])

    assert "не запускался" in text
    assert "—" in text


def test_run_writes_log_and_returns_snapshot(root, capsys) -> None:
    for rel, _need, _descr in self_diag.EXPECTED_PATHS:
        _touch(root, rel)

    out = self_diag.run(save_to_log=True)

    assert out["layout"]
    assert set(out) >= {"generated_at", "layout", "action_plan"}
    assert (root / "logs" / "self_diag.txt").is_file()
    text = (root / "logs" / "self_diag.txt").read_text(encoding="utf-8")
    assert "# JSON snapshot #" in text
    assert "Self-Diagnostic" in capsys.readouterr().out


def test_run_creates_logs_directory_on_fresh_clone(root, monkeypatch) -> None:
    """Каталога logs/ может не быть вовсе — `--self-diag` не должен падать."""
    monkeypatch.setattr(self_diag, "LOGS", root / "fresh" / "logs")

    self_diag.run(save_to_log=True)

    assert (root / "fresh" / "logs" / "self_diag.txt").is_file()


def test_run_without_log_does_not_write(root) -> None:
    self_diag.run(save_to_log=False)

    assert not (root / "logs" / "self_diag.txt").exists()


def test_main_entry_returns_zero(root) -> None:
    assert self_diag.main_entry() == 0
