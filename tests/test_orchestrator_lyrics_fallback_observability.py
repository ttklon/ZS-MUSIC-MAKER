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


def test_main_lyrics_uses_installed_local_role(monkeypatch):
    from app.ai.registry import registry
    from modules.lyrics import ai

    monkeypatch.setattr(registry, "is_available", lambda key: key == "lyrics_llm")
    calls = {}
    def generate(theme, **kwargs):
        calls.update(theme=theme, **kwargs)
        return {"ok": True, "lyrics": "[Куплет 1]\nПуэр остывает в чашке\n[Припев]\nПар на стекле"}
    monkeypatch.setattr(ai, "generate_lyrics_ai", generate)
    result = lyrics_stage._stage_lyrics("пуэр", "trap", 2, {"target_bpm": 96}, False)
    assert result["provider"] == "lyrics_llm"
    assert result["fallback_used"] is False
    assert calls["style_vector"]["target_bpm"] == 96
    assert calls["bilingual"] is False
    assert "Пуэр" in result["text"]


def test_local_model_failure_is_reported_when_router_takes_over(monkeypatch):
    from app.ai.registry import registry
    from modules.lyrics import ai

    monkeypatch.setattr(registry, "is_available", lambda key: True)
    monkeypatch.setattr(ai, "generate_lyrics_ai", lambda *a, **k: {"ok": False, "reason": "bad model"})
    class Router:
        def __init__(self, **kwargs):
            pass
        def complete(self, *args, **kwargs):
            return {"ok": True, "text": "fallback", "provider": "local_template", "fallback_used": True}
    monkeypatch.setattr(lyrics_stage, "LLMRouter", Router)
    result = lyrics_stage._stage_lyrics("пуэр", "trap")
    assert result["fallback_used"] is True
    assert result["fallback_attempts"][0]["error"] == "bad model"
