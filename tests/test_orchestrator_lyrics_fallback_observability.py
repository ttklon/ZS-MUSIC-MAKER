from app.core.stages import lyrics as lyrics_stage


def test_lyrics_template_fallback_preserves_router_exception(monkeypatch):
    class BrokenRouter:
        def __init__(self, **_kwargs):
            pass

        def complete(self, *_args, **_kwargs):
            raise ConnectionError("local router offline")

    monkeypatch.setattr(lyrics_stage, "LLMRouter", BrokenRouter)

    result = lyrics_stage._stage_lyrics("night drive", "phonk")

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

    monkeypatch.setattr(lyrics_stage, "LLMRouter", EmptyRouter)

    result = lyrics_stage._stage_lyrics("night drive", "phonk")

    assert result["provider"] == "local_template"
    assert result["fallback_attempts"] == [
        {
            "engine": "LLMRouter",
            "status": "empty_or_failed_response",
            "error": "empty completion",
        }
    ]
