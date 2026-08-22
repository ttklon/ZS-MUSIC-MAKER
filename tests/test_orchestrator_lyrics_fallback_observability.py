from app.core import orchestrator


def test_lyrics_template_fallback_preserves_router_exception(monkeypatch):
    class BrokenRouter:
        def __init__(self, **_kwargs):
            pass

        def complete(self, *_args, **_kwargs):
            raise ConnectionError("local router offline")

    monkeypatch.setattr(orchestrator, "LLMRouter", BrokenRouter)

    result = orchestrator._stage_lyrics("night drive", "phonk")

    assert result["ok"] is True
    assert result["provider"] == "local_template"
    assert result["fallback_used"] is True
    assert result["fallback_attempts"] == [
        {
            "engine": "LLMRouter",
            "status": "failed",
            "error": "ConnectionError: local router offline",
        }
    ]


def test_lyrics_template_fallback_preserves_unusable_router_response(monkeypatch):
    class EmptyRouter:
        def __init__(self, **_kwargs):
            pass

        def complete(self, *_args, **_kwargs):
            return {"ok": True, "text": "", "reason": "empty completion"}

    monkeypatch.setattr(orchestrator, "LLMRouter", EmptyRouter)

    result = orchestrator._stage_lyrics("night drive", "phonk")

    assert result["provider"] == "local_template"
    assert result["fallback_attempts"] == [
        {
            "engine": "LLMRouter",
            "status": "empty_or_failed_response",
            "error": "empty completion",
        }
    ]
