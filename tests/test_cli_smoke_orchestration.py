"""Both smoke suites must run, and failures must survive aggregation."""
import sys
from types import ModuleType
from app.cli.commands import run_smoke


def test_smoke_runs_both_and_preserves_failure(monkeypatch):
    calls = []
    first = ModuleType("tools.smoke_god")
    second = ModuleType("tools.smoke_audio")
    first.main = lambda: calls.append("god") or 1
    second.main = lambda: calls.append("audio") or 0
    monkeypatch.setitem(sys.modules, "tools.smoke_god", first)
    monkeypatch.setitem(sys.modules, "tools.smoke_audio", second)
    assert run_smoke() == 1
    assert calls == ["god", "audio"]
