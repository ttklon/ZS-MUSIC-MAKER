from __future__ import annotations

import modules.kpi_dashboard as kpi


def test_tz_percent_applies_health_constraints_to_filesystem_evidence(monkeypatch) -> None:
    monkeypatch.setattr(
        kpi,
        "TZ_CHECKLIST",
        [
            {"key": "rvc_real", "tz": "20.1", "title": "RVC"},
            {"key": "musicgen_full", "tz": "20.2", "title": "MusicGen"},
            {"key": "kpi_20_5", "tz": "20.5", "title": "KPI"},
            {"key": "unrelated", "tz": "1", "title": "Other"},
        ],
    )
    monkeypatch.setattr(
        kpi,
        "_filesystem_tz_checks",
        lambda: {"rvc_real": True, "musicgen_full": True, "kpi_20_5": True, "unrelated": True},
    )
    health = {
        "internals": [
            {"name": "modules.rvc_manager", "ok": False},
            {"name": "modules.rvc_trainer", "ok": True},
            {"name": "app.core.musicgen_texture", "ok": False},
            {"name": "modules.kpi_monitor", "ok": True},
        ]
    }

    percent, entries, advice = kpi._tz_percent(health, pipe={"ignored": True}, smoke={"ignored": True})

    statuses = {entry["key"]: entry["ok"] for entry in entries}
    assert statuses == {"rvc_real": False, "musicgen_full": False, "kpi_20_5": True, "unrelated": True}
    assert percent == 50
    assert len(advice) == 2
    assert "RVC" in advice[0]
    assert "MusicGen" in advice[1]
