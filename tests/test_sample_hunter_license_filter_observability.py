"""Regression coverage for safe observable sample-license filtering."""

import sys
import types

from agents.sample_hunter import hunter as sample_hunter


def test_hunt_reports_applied_license_filter(monkeypatch):
    monkeypatch.setattr(sample_hunter, "network_allowed", lambda allow=False: True)
    monkeypatch.setattr(sample_hunter, "list_local", lambda query: [])
    monkeypatch.setattr(
        sample_hunter,
        "search_online",
        lambda query, limit: [
            {"name": "cleared", "source": "catalog", "license": "CC0", "url": "https://example.test/cleared"},
            {"name": "restricted", "source": "catalog", "license": "unknown", "url": "https://example.test/restricted"},
        ],
    )
    fake_license_manager = types.SimpleNamespace(
        is_free_commercial=lambda license_name: license_name == "CC0"
    )
    monkeypatch.setitem(sys.modules, "app.core.license_manager", fake_license_manager)

    result = sample_hunter.hunt("kick", max_results=8)

    assert result["license_filter"] == {"ok": True, "status": "applied"}
    assert [sample["name"] for sample in result["online"]] == ["cleared"]


def test_hunt_fails_closed_when_license_validator_errors(monkeypatch):
    monkeypatch.setattr(sample_hunter, "network_allowed", lambda allow=False: True)
    local = {"name": "local", "source": "local", "license": "user", "path": "/tmp/local.wav"}
    online = {"name": "unverified", "source": "catalog", "license": "CC0", "url": "https://example.test/a"}
    monkeypatch.setattr(sample_hunter, "list_local", lambda query: [local])
    monkeypatch.setattr(sample_hunter, "search_online", lambda query, limit: [online])
    fake_license_manager = types.SimpleNamespace(
        is_free_commercial=lambda license_name: (_ for _ in ()).throw(RuntimeError("validator offline"))
    )
    monkeypatch.setitem(sys.modules, "app.core.license_manager", fake_license_manager)

    result = sample_hunter.hunt("kick", max_results=8)

    assert result["online"] == []
    assert result["samples"] == [local]
    assert result["license_filter"] == {
        "ok": False,
        "status": "failed_closed",
        "error": "RuntimeError: validator offline",
    }
