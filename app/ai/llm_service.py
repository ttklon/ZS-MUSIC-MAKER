"""Shared resilient local LLM service for llama-cpp-compatible handles."""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from time import monotonic
from typing import Any, Callable, Optional

DEFAULT_TIMEOUT_SEC = 600.0
DEFAULT_RETRIES = 2
FAILURE_THRESHOLD = 3


@dataclass
class CompletionReport:
    """Outcome metadata that keeps unavailable/local model failures observable."""

    text: str
    ok: bool
    attempts: int
    error: str | None
    circuit_open: bool
    timeout_sec: float


class CircuitBreaker:
    """Close after success; open after consecutive failed completion requests."""

    def __init__(self, failure_threshold: int = FAILURE_THRESHOLD) -> None:
        self.failure_threshold = failure_threshold
        self.consecutive_failures = 0

    @property
    def is_open(self) -> bool:
        return self.consecutive_failures >= self.failure_threshold

    def record_success(self) -> None:
        self.consecutive_failures = 0

    def record_failure(self) -> None:
        self.consecutive_failures += 1


_DEFAULT_BREAKER = CircuitBreaker()


def reset_circuit_breaker() -> None:
    """Reset process-local breaker; intended for explicit recovery/tests only."""
    _DEFAULT_BREAKER.record_success()


_BUSY_HANDLES: set[int] = set()
_BUSY_LOCK = threading.Lock()


def is_handle_busy(handle: Any) -> bool:
    with _BUSY_LOCK:
        return id(handle) in _BUSY_HANDLES


def _run_bounded(operation: Callable[[], str], timeout_sec: float, handle: Any = None) -> str:
    """Return an operation result or time out without waiting for a stuck handle.

    llama-cpp does not expose a safe cancellation primitive. The timed-out worker
    is daemonized so callers continue and the circuit records an honest failure;
    it may still release resources later when the backend returns.
    """
    result: dict[str, str] = {}
    error: dict[str, BaseException] = {}

    def worker() -> None:
        try:
            result["text"] = operation()
        except BaseException as exc:  # report backend errors to retry loop
            error["exception"] = exc
        finally:
            if handle is not None:
                with _BUSY_LOCK:
                    _BUSY_HANDLES.discard(id(handle))

    if handle is not None:
        with _BUSY_LOCK:
            if id(handle) in _BUSY_HANDLES:
                raise RuntimeError("model handle is busy")
            _BUSY_HANDLES.add(id(handle))
    thread = threading.Thread(target=worker, daemon=True)
    try:
        thread.start()
    except BaseException:
        if handle is not None:
            with _BUSY_LOCK:
                _BUSY_HANDLES.discard(id(handle))
        raise
    thread.join(timeout_sec)
    if thread.is_alive():
        raise TimeoutError(f"local LLM timed out after {timeout_sec:.1f}s")
    if "exception" in error:
        raise error["exception"]
    return result.get("text", "")


def _complete_once(
    handle: Any,
    system: str,
    user: str,
    max_tokens: int,
    temperature: float,
    top_p: float,
    repeat_penalty: float,
) -> str:
    """Call either public llama-cpp chat or callable completion interface once."""
    chat_error: Exception | None = None
    if hasattr(handle, "create_chat_completion"):
        try:
            response = handle.create_chat_completion(
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                repeat_penalty=repeat_penalty,
            )
            return str(response["choices"][0]["message"]["content"]).strip()
        except Exception as exc:
            chat_error = exc
    if callable(handle):
        prompt = f"<|system|>\n{system}\n<|user|>\n{user}\n<|assistant|>\n"
        response = handle(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            repeat_penalty=repeat_penalty,
            stop=["<|user|>", "<|system|>"],
        )
        return str(response["choices"][0]["text"]).strip()
    if chat_error is not None:
        raise chat_error
    raise TypeError("handle exposes neither llama-cpp completion interface")


def complete_with_report(
    handle: Any,
    system: str,
    user: str,
    max_tokens: int = 1024,
    temperature: float = 0.85,
    top_p: float = 0.95,
    repeat_penalty: float = 1.1,
    timeout_sec: float = DEFAULT_TIMEOUT_SEC,
    retries: int = DEFAULT_RETRIES,
    breaker: CircuitBreaker | None = None,
) -> CompletionReport:
    """Attempt local completion with bounded retries and a process-local breaker."""
    active_breaker = breaker or _DEFAULT_BREAKER
    if handle is None:
        return CompletionReport("", False, 0, "handle_missing", active_breaker.is_open, timeout_sec)
    if active_breaker.is_open:
        return CompletionReport("", False, 0, "circuit_open", True, timeout_sec)
    if timeout_sec <= 0:
        return CompletionReport("", False, 0, "invalid_timeout", False, timeout_sec)

    last_error: str | None = None
    attempts = 0
    for _ in range(max(0, retries) + 1):
        attempts += 1
        started = monotonic()
        try:
            text = _run_bounded(
                lambda: _complete_once(
                    handle, system, user, max_tokens, temperature, top_p, repeat_penalty
                ),
                timeout_sec, handle,
            )
            if not text:
                raise ValueError("empty_completion")
            active_breaker.record_success()
            return CompletionReport(text, True, attempts, None, False, timeout_sec)
        except Exception as exc:
            elapsed = monotonic() - started
            last_error = "timeout" if isinstance(exc, TimeoutError) else type(exc).__name__
            if last_error == "timeout":
                break  # The worker is still using this handle; retrying is unsafe.
            if elapsed > timeout_sec and last_error != "timeout":
                last_error = "timeout"

    active_breaker.record_failure()
    return CompletionReport("", False, attempts, last_error, active_breaker.is_open, timeout_sec)


def complete(
    handle: Any,
    system: str,
    user: str,
    max_tokens: int = 1024,
    temperature: float = 0.85,
    top_p: float = 0.95,
    repeat_penalty: float = 1.1,
    timeout_sec: float = DEFAULT_TIMEOUT_SEC,
    retries: int = DEFAULT_RETRIES,
) -> str:
    """Backward-compatible text API; failures are represented by an empty string."""
    return complete_with_report(
        handle,
        system,
        user,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        repeat_penalty=repeat_penalty,
        timeout_sec=timeout_sec,
        retries=retries,
    ).text


def complete_json(
    handle: Any,
    system: str,
    user: str,
    max_tokens: int = 2048,
    temperature: float = 0.4,
) -> Optional[dict]:
    txt = complete(handle, system, user, max_tokens=max_tokens, temperature=temperature)
    if not txt:
        return None
    start, end = txt.find("{"), txt.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(txt[start : end + 1])
    except json.JSONDecodeError:
        try:
            return json.loads(txt[start : end + 1].replace("'", '"'))
        except json.JSONDecodeError:
            return None
