"""T17: индикатор готовности не считает «файл есть» связностью.

`tools/readiness/inventory.py` объявлял модуль `REAL_PASS`, если на его имя
встречается подстрока в прод-коде — включая упоминания в самом `tools/` и в
комментариях внутри самого файла. В результате 284 из 287 модулей были
«REAL_PASS», хотя 34 из них недостижимы из точек входа (`expert_mode`,
`kpi_monitor`, `tiktok_edit`, `modules/video_edit/*` и др.).

Теперь достижимость считается по графу импортов от точек входа, а
недостижимый модуль получает честный `DEPRECATED` c весом 0.25.
"""

from __future__ import annotations

import importlib

import pytest

inventory = importlib.import_module("tools.readiness.inventory")
paths = importlib.import_module("tools.readiness.paths")
scoring = importlib.import_module("tools.readiness.scoring")


def test_deprecated_status_has_its_own_weight() -> None:
    assert "DEPRECATED" in paths.STATUS_WEIGHT
    assert paths.STATUS_WEIGHT["DEPRECATED"] < paths.STATUS_WEIGHT["REAL_PASS"]
    assert paths.STATUS_WEIGHT["DEPRECATED"] > paths.STATUS_WEIGHT["MISSING"]


def test_unreachable_modules_are_marked_deprecated() -> None:
    rows = {row["path"]: row for row in inventory.module_inventory()}

    for expected in (
        "modules/expert_mode.py",
        "modules/kpi_monitor.py",
        "modules/tiktok_edit.py",
        "modules/sidechain.py",
        "app/core/pipeline_core.py",
    ):
        assert expected in rows, f"{expected} отсутствует в инвентаре"
        assert rows[expected]["status"] == "DEPRECATED", rows[expected]
        assert rows[expected].get("reachable") is False


def test_reachable_modules_stay_real_pass() -> None:
    rows = {row["path"]: row for row in inventory.module_inventory()}

    for path in ("app/core/orchestrator.py", "modules/mastering/chain.py", "main.py"):
        assert rows[path]["status"] == "REAL_PASS", rows[path]
        assert rows[path]["reachable"] is True


def test_self_mentions_do_not_count_as_reachability() -> None:
    """Комментарий внутри самого файла не делает модуль используемым."""
    rows = {row["path"]: row for row in inventory.module_inventory()}

    assert rows["modules/expert_mode.py"]["production_references"] == 0


def test_summary_accounts_for_every_status() -> None:
    summary = inventory.module_inventory_summary()

    assert summary["tracked_modules"] == (
        summary["REAL_PASS"] + summary["REAL_FAIL"] + summary["PLANNED"] + summary["DEPRECATED"]
    )
    assert summary["DEPRECATED"] >= 15, summary


def test_readiness_percent_reflects_dead_code() -> None:
    """Недостижимый код должен снижать процент, а не украшать матрицу."""
    total, detail = scoring.compute()

    assert total <= 65.0, (total, detail["cap_min"])
    inventory_summary = detail["module_inventory"]
    assert inventory_summary["DEPRECATED"] >= 15
    assert inventory_summary["PLANNED"] + inventory_summary["DEPRECATED"] >= 15


@pytest.mark.parametrize("path", ["modules/expert_mode.py", "modules/kpi_monitor.py"])
def test_deprecated_modules_are_still_present_on_disk(path: str) -> None:
    """Пометка не удаляет код: удаление — отдельная итерация."""
    assert (paths.ROOT / path).is_file()
