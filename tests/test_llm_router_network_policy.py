# -*- coding: utf-8 -*-
"""`modules/llm/router.py`: preflight не должен зондировать сеть сам.

Роутер стоял на обходе политики T15: перед вызовом облачных провайдеров он
открывал TCP-соединение с `8.8.8.8:53`, чтобы «проверить интернет». Это
сетевой запрос, которого пользователь не разрешал, и он же обходил
`app/core/net_policy.py`. Теперь решение принимает политика, а сокет-проба
остаётся только как проверка доступности локального Ollama.

Сеть и локальный демон подменяются: тесты проверяют решение, а не связность.
Реальные ответы LLM не запрашиваются.
"""

from __future__ import annotations

import socket

import pytest

from modules.llm import router as router_module


@pytest.fixture
def no_network(monkeypatch):
    monkeypatch.setattr(
        "app.core.net_policy.network_allowed",
        lambda allow_online=False, settings_path=None: allow_online is True,
    )
    return monkeypatch


@pytest.fixture
def contacts(monkeypatch) -> list:
    """Любая попытка открыть сокет или соединение фиксируется."""
    seen: list = []

    def connect(self, address, *a, **k):
        seen.append(("connect", address))
        raise OSError("сеть недоступна в тесте")

    monkeypatch.setattr(socket.socket, "connect", connect)
    monkeypatch.setattr(socket, "create_connection",
                        lambda *a, **k: seen.append(("create_connection", a)) or (_ for _ in ()).throw(OSError("нет")))
    return seen


def test_preflight_does_not_probe_internet_without_permission(no_network, contacts) -> None:
    router = router_module.LLMRouter(keys={}, ollama_url="http://127.0.0.1:11434")

    state = router._preflight()

    assert state["internet"] is False
    assert not [item for item in contacts if item[1] == ("8.8.8.8", 53)], (
        "preflight не должен трогать внешний адрес без разрешения пользователя"
    )


def test_preflight_reports_internet_when_policy_allows(monkeypatch, contacts) -> None:
    """Явно разрешённая сеть — единственный случай, когда проба допустима."""
    monkeypatch.setattr(
        "app.core.net_policy.network_allowed",
        lambda allow_online=False, settings_path=None: True,
    )
    router = router_module.LLMRouter(keys={}, ollama_url="http://127.0.0.1:11434")

    router._preflight(allow_online=True)

    # Сокет в тесте закрыт намеренно: проверяется попытка, а не связность.
    assert ("connect", ("8.8.8.8", 53)) in contacts


def test_local_ollama_check_is_not_blocked_by_policy(no_network, monkeypatch) -> None:
    """Локальный демон — не сеть: политика его не запрещает."""
    monkeypatch.setattr(socket.socket, "connect", lambda self, address, *a, **k: None)
    router = router_module.LLMRouter(keys={}, ollama_url="http://127.0.0.1:11434")

    state = router._preflight()

    assert state["ollama"] is True
    assert state["internet"] is False


def test_without_internet_cloud_is_not_called(no_network, contacts, monkeypatch) -> None:
    calls: list = []
    monkeypatch.setattr(router_module, "call_openrouter", lambda *a, **k: calls.append("openrouter"))
    monkeypatch.setattr(router_module, "call_grok", lambda *a, **k: calls.append("grok"))
    monkeypatch.setattr(router_module, "call_gemini", lambda *a, **k: calls.append("gemini"))
    router = router_module.LLMRouter(
        keys={"openrouter": "k1", "grok": "k2", "gemini": "k3"},
        ollama_url="http://127.0.0.1:11434",
    )

    result = router.complete("напиши куплет", theme="ночь", genre="phonk", language="ru")

    assert calls == [], "без разрешения сети облачные провайдеры не вызываются"
    assert "cloud_skipped_no_internet" in result["provider_chain"]
    assert result["ok"] is True, "локальный шаблон обязан отработать"
    assert "local_template" in result["provider_chain"]


def test_result_names_the_reason_it_stayed_offline(no_network, contacts, monkeypatch) -> None:
    monkeypatch.setattr(router_module, "call_openrouter", lambda *a, **k: None)
    router = router_module.LLMRouter(keys={"openrouter": "k1"})

    result = router.complete("текст", theme="тема")

    # роутер складывает причины в ключ "error" (dict по провайдерам)
    reasons = result.get("error") or {}
    assert reasons.get("openrouter") == "no_internet"
