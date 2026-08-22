import sys
from types import SimpleNamespace

from app.core import orchestrator


def test_release_pack_legacy_fallback_preserves_full_pack_failure(monkeypatch, tmp_path):
    def fail_full(*_args, **_kwargs):
        raise RuntimeError("full pack dependency unavailable")

    def legacy_pack(*_args, **_kwargs):
        return {"ok": True, "path": "legacy-release", "engine": "v13"}

    monkeypatch.setitem(sys.modules, "modules.release_pack_full", SimpleNamespace(build_pack=fail_full))
    monkeypatch.setitem(sys.modules, "modules.release_pack_v13", SimpleNamespace(build_pack=legacy_pack))

    result = orchestrator._stage_release_pack("master.wav", {"title": "Test"}, tmp_path)

    assert result["ok"] is True
    assert result["path"] == "legacy-release"
    assert result["fallback_attempts"] == [
        {
            "engine": "release_pack_full",
            "status": "failed",
            "error": "RuntimeError: full pack dependency unavailable",
        }
    ]


def test_release_pack_minimal_fallback_preserves_all_failed_engines(monkeypatch, tmp_path):
    def fail_full(*_args, **_kwargs):
        raise ImportError("full pack missing")

    def fail_legacy(*_args, **_kwargs):
        raise ValueError("legacy pack rejected metadata")

    monkeypatch.setitem(sys.modules, "modules.release_pack_full", SimpleNamespace(build_pack=fail_full))
    monkeypatch.setitem(sys.modules, "modules.release_pack_v13", SimpleNamespace(build_pack=fail_legacy))
    monkeypatch.setattr(
        orchestrator,
        "_minimal_release_pack",
        lambda *_args: {"ok": True, "path": "minimal-release", "fallback_used": True},
    )

    result = orchestrator._stage_release_pack("master.wav", {"title": "Test"}, tmp_path)

    assert result["fallback_used"] is True
    assert result["fallback_attempts"] == [
        {"engine": "release_pack_full", "status": "failed", "error": "ImportError: full pack missing"},
        {
            "engine": "release_pack_v13",
            "status": "failed",
            "error": "ValueError: legacy pack rejected metadata",
        },
    ]
