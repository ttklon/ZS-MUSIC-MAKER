"""Наблюдаемость стадии релиза: сбой сборщика не маскируется успехом."""

from types import SimpleNamespace

from app.core import orchestrator
from app.core.stages import release as release_stage


def test_release_pack_failure_is_recorded_with_engine_and_error(monkeypatch, tmp_path):
    def fail_pack(*_args, **_kwargs):
        raise RuntimeError("pack dependency unavailable")

    monkeypatch.setitem(
        __import__("sys").modules,
        "modules.release",
        SimpleNamespace(build_pack=fail_pack),
    )
    monkeypatch.setattr(
        release_stage,
        "_minimal_release_pack",
        lambda *_args: {"ok": True, "path": "minimal-release", "fallback_used": True},
    )

    result = orchestrator._stage_release_pack("master.wav", {"title": "Test"}, tmp_path)

    assert result["ok"] is True
    assert result["fallback_used"] is True
    assert result["fallback_attempts"] == [
        {
            "engine": "modules.release",
            "status": "failed",
            "error": "RuntimeError: pack dependency unavailable",
        }
    ]


def test_release_pack_invalid_result_is_reported(monkeypatch, tmp_path):
    monkeypatch.setitem(
        __import__("sys").modules,
        "modules.release",
        SimpleNamespace(build_pack=lambda *_a, **_k: "not-a-dict"),
    )
    monkeypatch.setattr(
        release_stage,
        "_minimal_release_pack",
        lambda *_args: {"ok": True, "path": "minimal-release", "fallback_used": True},
    )

    result = orchestrator._stage_release_pack("master.wav", {"title": "Test"}, tmp_path)

    assert result["fallback_attempts"] == [
        {"engine": "modules.release", "status": "invalid_result", "error": "expected dict, got str"}
    ]
