from app.core.stages import lyrics as lyrics_stage


def test_lyrics_blocked_preserves_router_exception(monkeypatch):
    """Роутер упал — текста нет, причина сохранена.

    Шаблон в проде больше не подставляется: «текст» из punch-библиотеки не
    является текстом песни, и отчёт не должен показывать его как результат.
    """
    monkeypatch.delenv("ZSMM_ALLOW_TEMPLATE_LYRICS", raising=False)

    class BrokenRouter:
        def __init__(self, **_kwargs):
            pass

        def complete(self, *_args, **_kwargs):
            raise ConnectionError("local router offline")

    monkeypatch.setattr(lyrics_stage, "LLMRouter", BrokenRouter)

    result = lyrics_stage._stage_lyrics("night drive", "phonk")

    assert result["ok"] is False
    assert result["provider"] == "BLOCKED"
    assert result["fallback_used"] is False
    assert result["text"] == ""
    assert result["fallback_attempts"] == [
        {
            "engine": "LLMRouter",
            "status": "failed",
            "error": "ConnectionError: local router offline",
        }
    ]


def test_lyrics_blocked_preserves_unusable_router_response(monkeypatch):
    monkeypatch.delenv("ZSMM_ALLOW_TEMPLATE_LYRICS", raising=False)

    class EmptyRouter:
        def __init__(self, **_kwargs):
            pass

        def complete(self, *_args, **_kwargs):
            return {"ok": True, "text": "", "reason": "empty completion"}

    monkeypatch.setattr(lyrics_stage, "LLMRouter", EmptyRouter)

    result = lyrics_stage._stage_lyrics("night drive", "phonk")

    assert result["provider"] == "BLOCKED"
    assert result["blocked"] is True
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


def test_router_error_details_are_not_lost_on_template_fallback(monkeypatch):
    from app.ai.registry import registry
    monkeypatch.setattr(registry, "is_available", lambda key: False)
    class Router:
        def __init__(self, **kwargs): pass
        def complete(self, *args, **kwargs):
            return {"ok": True, "text": "fallback", "provider": "local_template",
                    "fallback_used": True, "error": {"ollama": "http_404"}}
    monkeypatch.setattr(lyrics_stage, "LLMRouter", Router)
    result = lyrics_stage._stage_lyrics("пуэр", "house")
    assert result["provider_errors"]["ollama"] == "http_404"


def test_configured_ollama_model_skips_heavy_registered_gguf(monkeypatch):
    from app.ai.registry import registry
    from modules.lyrics import ai
    monkeypatch.setenv("ZSMM_OLLAMA_MODEL", "qwen3.5:4b")
    monkeypatch.setattr(registry, "is_available", lambda key: True)
    monkeypatch.setattr(ai, "generate_lyrics_ai", lambda *a, **kw: (_ for _ in ()).throw(AssertionError("GGUF must be skipped")))
    class Router:
        def __init__(self, **kwargs): pass
        def complete(self, *args, **kwargs): return {"ok": True, "text": "lyrics", "provider": "ollama"}
    monkeypatch.setattr(lyrics_stage, "LLMRouter", Router)
    result = lyrics_stage._stage_lyrics("пуэр", "house")
    assert result["provider"] == "ollama" and not result["fallback_attempts"]
