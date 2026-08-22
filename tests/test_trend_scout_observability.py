"""Regression coverage for observable TrendScout source fallback."""

import sys
import time
import types

from agents import trend_scout


def test_trend_scout_reports_cached_provenance(monkeypatch):
    monkeypatch.setattr(
        trend_scout,
        "_load_cache",
        lambda: {"phonk": {"trends": ["cached vibe"], "ts": time.time()}},
    )

    result = trend_scout.scout_trends_with_diagnostics("phonk")

    assert result == {
        "trends": ["cached vibe"],
        "source": "cache",
        "diagnostics": [],
    }
    assert trend_scout.scout_trends("phonk") == ["cached vibe"]


def test_trend_scout_reports_failed_sources_and_builtin_fallback(monkeypatch):
    monkeypatch.setattr(trend_scout, "_load_cache", lambda: {})
    monkeypatch.setattr(trend_scout, "_save_cache", lambda cache: None)
    monkeypatch.setattr(
        trend_scout,
        "_duckduckgo_search",
        lambda query: (_ for _ in ()).throw(ConnectionError("offline")),
    )
    def fail_local_dictionary():
        raise RuntimeError("dictionary unreadable")

    monkeypatch.setitem(
        sys.modules,
        "modules.lyrics_gen",
        types.SimpleNamespace(load_slang_dictionary=fail_local_dictionary),
    )
    monkeypatch.setattr(trend_scout, "_fallback_trends", lambda query: ["local fallback"])

    result = trend_scout.scout_trends_with_diagnostics("phonk")

    assert result["trends"] == ["local fallback"]
    assert result["source"] == "built_in_fallback"
    assert result["diagnostics"] == [
        {"source": "duckduckgo", "ok": False, "error": "ConnectionError: offline"},
        {"source": "local_slang", "ok": False, "error": "RuntimeError: dictionary unreadable"},
    ]
