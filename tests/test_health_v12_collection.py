from __future__ import annotations

import json
from pathlib import Path

import modules.health as health


def test_collect_preserves_scoring_advice_and_persistence_with_stubbed_probes(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        health,
        "CHECKS",
        [
            {"mod": "core_ok", "name": "Core", "req": "core"},
            {"mod": "gui_ok", "name": "GUI", "req": "core_alt", "group": "gui"},
            {"mod": "quality_missing", "name": "Quality", "req": "quality"},
            {"mod": "optional_ok", "name": "Optional", "req": "optional"},
        ],
    )
    monkeypatch.setattr(health, "INTERNAL_MODULES", ["internal_ok", "internal_missing"])
    outcomes = {
        "core_ok": True,
        "gui_ok": True,
        "quality_missing": False,
        "optional_ok": True,
        "internal_ok": True,
        "internal_missing": False,
    }

    def fake_probe(module_path: str, name: str, requirement: str) -> health.ProbeResult:
        ok = outcomes[module_path]
        return health.ProbeResult(
            module_path, name, requirement, ok, "1.0" if ok else None, None if ok else "missing"
        )

    monkeypatch.setattr(health, "_probe", fake_probe)
    monkeypatch.setattr(health, "_hw_probe", lambda: {"mode": "fallback_hw"})
    output = tmp_path / "health.json"

    report = health.collect(output)

    assert report.core_ok is True
    assert report.quality_ok is False
    assert report.optional_ok_count == 1
    assert report.optional_total == 1
    assert report.percent_ready == 62
    assert report.verdict == "YELLOW"
    assert any("[INTERNAL] internal_missing" in advice for advice in report.advice)
    persisted = json.loads(output.read_text(encoding="utf-8"))
    assert persisted["verdict"] == "YELLOW"
    assert persisted["hw_profile"] == {"mode": "fallback_hw"}
