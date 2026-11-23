"""Environment blockers stop audio rerenders; transient/quality failures do not."""
import json

import pytest

from modules.hit_factory.retry import stop_for_environment
from modules.llm.router import _no_llm_result
from app.core.stages.lyrics_providers import _interpret_router_result, _retry_metadata


def static_errors():
    return {"openrouter": "no_internet", "grok": "no_api_key",
            "gemini": "no_internet", "ollama": "no_local_daemon"}


def test_environment_marker_survives_router_and_lyrics_provider(monkeypatch):
    monkeypatch.delenv("ZSMM_ALLOW_TEMPLATE_LYRICS", raising=False)
    result = _no_llm_result([], static_errors(), "test", "trap", "ru")
    assert result["retry_scope"] == "environment"
    output, failure = _interpret_router_result(result, "trap")
    assert output is None
    assert failure["retry_scope"] == "environment"
    assert _retry_metadata([failure]) == {"retry_scope": "environment"}
    assert _retry_metadata([failure, {"engine": "local", "error": "timeout"}]) == {}


@pytest.mark.parametrize("provider,error", [("ollama", "ReadTimeout"), ("openrouter", "http_503"),
                                            ("gemini", None)])
def test_transient_or_unknown_provider_failure_has_no_environment_marker(monkeypatch, provider, error):
    monkeypatch.delenv("ZSMM_ALLOW_TEMPLATE_LYRICS", raising=False)
    errors = static_errors()
    errors[provider] = error
    assert "retry_scope" not in _no_llm_result([], errors, "test", "trap", "ru")


@pytest.mark.parametrize("status", ["OK", "FALLBACK", "FAILED"])
def test_only_explicit_blocked_stage_can_stop(status):
    attempt = {"report": {"stages": [{"name": "_stage_lyrics", "status": status,
                                       "output": {"retry_scope": "environment"}}]}}
    assert not stop_for_environment(attempt, lambda message: None)


def test_reason_text_alone_does_not_stop_evolution():
    attempt = {"report": {"stages": [{"name": "_stage_lyrics", "status": "BLOCKED",
                                       "reason": "no model installed", "output": {}}]}}
    assert not stop_for_environment(attempt, lambda message: None)


@pytest.mark.parametrize("environment,expected", [(True, 1), (False, 3)])
def test_factory_stop_and_summary_preserve_remediation(tmp_path, monkeypatch, environment, expected):
    from modules.hit_factory import generator

    monkeypatch.setattr(generator, "_maybe_auto_genre", lambda genre, theme: genre)
    monkeypatch.setattr("modules.hit_factory.kpi.build_kpi", lambda *a, **kw: {})
    factory = generator.HitFactory(output_root=tmp_path, adaptive=False, max_attempts=3, verbose=False)
    calls = []

    def render(project_id, state, rng):
        calls.append(project_id)
        output = {"reason": "provider unavailable", "action": "prepare local model"}
        if environment:
            output["retry_scope"] = "environment"
        return {"project_id": project_id, "out_root": str(tmp_path), "master_path": None,
                "hit_score": 40, "verdict": "needs_work", "report": {"verdict": "PARTIAL",
                "quality_gate_failures": ["crest"], "stages": [
                    {"name": "_stage_lyrics", "status": "BLOCKED", "output": output}]}}

    monkeypatch.setattr(factory, "_run_pipeline_once", render)
    result = factory.make_one(genre="trap", theme="test", seed=42, duration_sec=10)
    assert len(calls) == expected
    assert not result["readiness"]["ready"]
    summary = json.loads((tmp_path / "factory_summary.json").read_text())
    assert len(summary["attempts"]) == expected
    if environment:
        assert result["evolution_stop"]["reason"] == "environment_blocked"
        assert summary["evolution_stop"]["blockers"][0]["action"] == "prepare local model"
    else:
        assert summary["evolution_stop"] is None


def test_actual_lyrics_stage_exposes_static_provider_blocker(monkeypatch):
    from app.core.stages import lyrics
    from modules.llm.router import LLMRouter

    monkeypatch.delenv("ZSMM_ALLOW_TEMPLATE_LYRICS", raising=False)
    monkeypatch.setattr(lyrics, "_discover_auto_model", lambda registry: None)
    monkeypatch.setattr(lyrics, "_try_local_lyrics_model", lambda *a, **kw: (None, []))
    monkeypatch.setattr(lyrics, "LLMRouter", LLMRouter)
    monkeypatch.setattr(LLMRouter, "_preflight", lambda self: {"internet": False, "ollama": False})
    result = lyrics._stage_lyrics("test", "trap")
    assert result["blocked"]
    assert result["retry_scope"] == "environment"


def test_quality_failure_without_provider_blocker_remains_retryable():
    attempt = {"report": {"verdict": "PARTIAL", "quality_gate_failures": ["crest"],
                           "stages": [{"name": "_stage_lyrics", "status": "OK", "output": {"text": "lyrics"}}]}}
    assert not stop_for_environment(attempt, lambda message: None)


def test_optional_export_cannot_force_environment_stop():
    attempt = {"report": {"stages": [{"name": "_stage_stems", "status": "BLOCKED",
                                       "output": {"retry_scope": "environment"}}]}}
    assert not stop_for_environment(attempt, lambda message: None)
