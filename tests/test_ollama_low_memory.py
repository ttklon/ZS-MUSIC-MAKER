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


def test_bootstrap_model_is_attempted_even_when_ram_estimate_is_tight() -> None:
    """Скачанный `qwen3:4b` должен пробоваться, а не отбрасываться по оценке.

    Раньше адаптер выбирал только «влезающие в RAM» модели: пользователь с
    4 ГБ делал `--bootstrap --online`, получал `qwen3:4b` на диске — и всё
    равно `BLOCKED`, без единой попытки.
    """
    from modules.llm.ollama_adaptive import prefer_installed

    models = [{"name": "qwen3:4b", "size": 2_684_354_560}]
    tight = {"model": None, "reason": "no known installed text model fits estimated free RAM"}

    chosen = prefer_installed(tight, models, "qwen3:4b")

    assert chosen["model"] == "qwen3:4b"
    assert chosen["installed_but_tight"] is True
    assert "attempting anyway" in chosen["reason"]


def test_fitting_model_still_wins_over_tight_bootstrap_model() -> None:
    from modules.llm.ollama_adaptive import prefer_installed

    models = [{"name": "qwen3:4b", "size": 2_684_354_560}]
    fitting = {"model": "llama3.2:1b", "reason": "fits"}

    assert prefer_installed(fitting, models, "qwen3:4b") == fitting


def test_absent_bootstrap_model_is_not_invented() -> None:
    """Модели нет на диске — значит нет: выдуманное имя дало бы `http_404`."""
    from modules.llm.ollama_adaptive import prefer_installed

    selection = {"model": None, "reason": "no known installed text model fits"}

    assert prefer_installed(selection, [{"name": "llama3.2:1b"}], "qwen3:4b") == selection
