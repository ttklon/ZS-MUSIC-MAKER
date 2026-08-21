from __future__ import annotations

from tools import regress_v39


def test_regression_matrix_has_all_unique_app_g_scenarios() -> None:
    scenarios = regress_v39.SCENARIOS

    assert len(scenarios) == 15
    assert [item.identifier for item in scenarios] == [f"{value:02d}" for value in range(1, 16)]
    assert {item.expected for item in scenarios} == {"PASS", "BLOCKED"}
    assert {item.identifier for item in scenarios if item.expected == "BLOCKED"} == {"03", "10"}


def test_blocked_scenario_is_not_reported_as_pass_without_heavy_runtime(monkeypatch) -> None:
    scenario = next(item for item in regress_v39.SCENARIOS if item.identifier == "03")

    monkeypatch.setattr(regress_v39, "_has_heavy_runtime", lambda: False)
    result = regress_v39.run_scenario(scenario, heavy_runtime=False)

    assert result["returncode"] == 0
    assert result["status"] == "BLOCKED"
    assert "absent" in str(result["reason"])


def test_passing_contract_uses_exit_code(monkeypatch) -> None:
    scenario = next(item for item in regress_v39.SCENARIOS if item.identifier == "01")
    result = regress_v39.run_scenario(scenario, heavy_runtime=False)

    assert result["returncode"] == 0
    assert result["status"] == "PASS"
