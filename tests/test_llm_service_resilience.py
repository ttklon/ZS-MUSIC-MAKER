from __future__ import annotations

import time

from app.ai import llm_service
from modules import llm_clients_v15


class StaticChatHandle:
    def __init__(self, text: str = "stable answer") -> None:
        self.text = text
        self.calls = 0

    def create_chat_completion(self, **kwargs):
        self.calls += 1
        return {"choices": [{"message": {"content": self.text}}]}


class FailingChatHandle:
    def __init__(self, failures: int) -> None:
        self.failures = failures
        self.calls = 0

    def create_chat_completion(self, **kwargs):
        self.calls += 1
        if self.calls <= self.failures:
            raise RuntimeError("backend unavailable")
        return {"choices": [{"message": {"content": "recovered"}}]}


class CallableFallbackHandle:
    def create_chat_completion(self, **kwargs):
        raise RuntimeError("chat interface unavailable")

    def __call__(self, prompt, **kwargs):
        return {"choices": [{"text": "callable answer"}]}


class SlowHandle:
    def create_chat_completion(self, **kwargs):
        time.sleep(0.05)
        return {"choices": [{"message": {"content": "too late"}}]}


def test_retry_two_recovers_on_third_attempt() -> None:
    handle = FailingChatHandle(failures=2)
    breaker = llm_service.CircuitBreaker()

    report = llm_service.complete_with_report(
        handle, "system", "prompt", retries=2, timeout_sec=1.0, breaker=breaker
    )

    assert report.ok is True
    assert report.text == "recovered"
    assert report.attempts == 3
    assert handle.calls == 3
    assert breaker.is_open is False


def test_timeout_is_honest_and_bounded() -> None:
    breaker = llm_service.CircuitBreaker()

    report = llm_service.complete_with_report(
        SlowHandle(), "system", "prompt", retries=0, timeout_sec=0.001, breaker=breaker
    )

    assert report.ok is False
    assert report.error == "timeout"
    assert report.attempts == 1


def test_circuit_opens_after_three_failed_requests() -> None:
    handle = FailingChatHandle(failures=99)
    breaker = llm_service.CircuitBreaker()

    for expected_open in (False, False, True):
        report = llm_service.complete_with_report(
            handle, "system", "prompt", retries=0, timeout_sec=1.0, breaker=breaker
        )
        assert report.ok is False
        assert report.circuit_open is expected_open
    blocked = llm_service.complete_with_report(
        handle, "system", "prompt", retries=0, timeout_sec=1.0, breaker=breaker
    )

    assert blocked.error == "circuit_open"
    assert blocked.attempts == 0
    assert handle.calls == 3


def test_callable_handle_remains_supported_after_chat_failure() -> None:
    breaker = llm_service.CircuitBreaker()

    report = llm_service.complete_with_report(
        CallableFallbackHandle(), "system", "prompt", retries=0, timeout_sec=1.0, breaker=breaker
    )

    assert report.ok is True
    assert report.text == "callable answer"


def test_v15_local_wrapper_matches_shared_service_text() -> None:
    llm_service.reset_circuit_breaker()
    direct = llm_service.complete(StaticChatHandle(), "system", "prompt", retries=0)
    llm_service.reset_circuit_breaker()
    wrapped = llm_clients_v15.complete_local_handle(
        StaticChatHandle(), "prompt", system="system", timeout_sec=1.0
    )

    assert direct == "stable answer"
    assert wrapped["ok"] is True
    assert wrapped["text"] == direct
    assert wrapped["provider"] == "local_llm_service"
