from modules.llm import providers, router


def test_ollama_uses_bounded_context_and_unloads_after_request(monkeypatch):
    sent = {}
    class Response:
        status_code = 200
        def json(self): return {"response": "тестовый текст"}
    monkeypatch.setattr(providers.requests, "post", lambda *a, **kw: sent.update(kw) or Response())
    result = providers.call_ollama("prompt", model="qwen3.5:4b", max_tokens=333, timeout=600)
    assert result.ok and result.text == "тестовый текст"
    assert sent["json"]["model"] == "qwen3.5:4b"
    assert sent["json"]["options"]["num_ctx"] == 4096
    assert sent["json"]["options"]["num_predict"] == 333
    assert sent["json"]["keep_alive"] == 0
    assert sent["timeout"] == 600


def test_router_uses_configured_ollama_and_slow_timeout(monkeypatch):
    monkeypatch.setenv("ZSMM_OLLAMA_MODEL", "qwen3.5:4b")
    monkeypatch.setattr(router.LLMRouter, "_preflight", lambda self: {"internet": False, "ollama": True})
    calls = {}
    def fake_call(*args, **kwargs):
        calls.update(kwargs)
        return providers.ProviderResult(True, text="текст", provider="ollama", model=kwargs["model"])
    monkeypatch.setattr(router, "call_ollama", fake_call)
    result = router.LLMRouter(timeout=8).complete("prompt", max_tokens=321)
    assert result["provider"] == "ollama" and not result["fallback_used"]
    assert calls["model"] == "qwen3.5:4b" and calls["timeout"] == 600
    assert calls["max_tokens"] == 321
