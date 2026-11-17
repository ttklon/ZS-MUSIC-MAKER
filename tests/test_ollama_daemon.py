"""Automatic local startup, with bounded failure cleanup and no public bind."""
from types import SimpleNamespace

import pytest

from modules.llm import ollama_daemon as daemon
from modules.llm import ollama_setup as setup


@pytest.mark.parametrize("url", ["http://example.com:11434", "http://0.0.0.0:11434", "https://localhost", "http://user:pass@localhost", "http://localhost/api", "http://localhost:bad"])
def test_refuses_nonlocal_or_malformed_endpoint(monkeypatch, url):
    monkeypatch.setattr(daemon.subprocess, "Popen", lambda *a, **k: pytest.fail("must not start"))
    assert not daemon.start_local_daemon("ollama", url, lambda url: None)["ok"]


def test_reuses_running_server(monkeypatch):
    monkeypatch.setattr(daemon.subprocess, "Popen", lambda *a, **k: pytest.fail("already running"))
    assert daemon.start_local_daemon("ollama", "http://localhost:11434", lambda url: []) == {
        "ok": True, "started": False,
    }


def test_starts_loopback_and_waits_for_api(monkeypatch):
    calls = []
    child = SimpleNamespace(pid=123, poll=lambda: None)
    monkeypatch.setattr(daemon.subprocess, "Popen", lambda *a, **kw: (calls.append((a, kw)), child)[1])
    probes = iter([None, ["qwen3:4b"]])
    result = daemon.start_local_daemon("/bin/ollama", "http://127.0.0.1:11435", lambda url: next(probes))
    assert result["ok"] and result["started"]
    assert calls[0][0][0] == ["/bin/ollama", "serve"]
    assert calls[0][1]["env"]["OLLAMA_HOST"] == "127.0.0.1:11435"


def test_timeout_reaps_only_started_child(monkeypatch):
    actions = []
    child = SimpleNamespace(
        pid=123, poll=lambda: None, terminate=lambda: actions.append("terminate"),
        wait=lambda **kw: actions.append("wait"),
    )
    monkeypatch.setattr(daemon.subprocess, "Popen", lambda *a, **kw: child)
    result = daemon.start_local_daemon("ollama", "http://localhost:11434", lambda url: None, timeout=0)
    assert not result["ok"] and "timed out" in result["reason"]
    assert actions == ["terminate", "wait"]


def test_installed_offline_model_is_started_without_download(monkeypatch):
    state = {"running": False}
    monkeypatch.setattr(setup, "_ollama_bin", lambda: "/bin/ollama")
    monkeypatch.setattr(setup, "_daemon_models", lambda url: ["qwen3:4b"] if state["running"] else None)

    def start(*args):
        state["running"] = True
        return {"ok": True, "started": True}

    monkeypatch.setattr(daemon, "start_local_daemon", start)
    monkeypatch.setattr(setup, "_pull_model", lambda *a, **kw: pytest.fail("offline cached model"))
    result = setup.ensure_ollama(allow_download=False)
    assert result["ok"] and result["ready"] and result["changed"]


def test_exact_model_tag_required(monkeypatch):
    monkeypatch.setattr(setup, "_ollama_bin", lambda: None)
    monkeypatch.setattr(setup, "_daemon_models", lambda url: ["qwen3:32b"])
    monkeypatch.setenv("ZSMM_OLLAMA_PULL_MODEL", "qwen3:4b")
    assert not setup.install_report()["ready"]


def test_router_recovers_stopped_local_server(monkeypatch):
    import socket
    from modules.llm.router import LLMRouter

    monkeypatch.setattr("app.core.net_policy.network_allowed", lambda **kw: False)
    monkeypatch.setattr(socket.socket, "connect", lambda *a: (_ for _ in ()).throw(ConnectionRefusedError()))
    calls = []
    monkeypatch.setattr(daemon, "ensure_local_server", lambda url: calls.append(url) or True)
    state = LLMRouter(keys={})._preflight()
    assert state == {"internet": False, "ollama": True}
    assert calls == ["http://127.0.0.1:11434"]


def test_failed_start_never_downloads_installer(monkeypatch):
    monkeypatch.setattr(setup, "_ollama_bin", lambda: "/bin/ollama")
    monkeypatch.setattr(setup, "_daemon_models", lambda url: None)
    monkeypatch.setattr(daemon, "start_local_daemon", lambda *a: {"ok": False, "reason": "startup failed"})
    monkeypatch.setattr(setup, "_download", lambda *a, **kw: pytest.fail("already installed"))
    result = setup.ensure_ollama(allow_download=True)
    assert not result["ok"] and result["reason"] == "startup failed"


def test_daemon_exits_before_ready(monkeypatch):
    child = SimpleNamespace(pid=123, poll=lambda: 1, returncode=1)
    monkeypatch.setattr(daemon.subprocess, "Popen", lambda *a, **kw: child)
    result = daemon.start_local_daemon("ollama", "http://localhost:11434", lambda url: None)
    assert not result["ok"] and "exited (1)" in result["reason"]


def test_pull_targets_the_configured_daemon(monkeypatch):
    captured = {}
    monkeypatch.setattr(setup, "_ollama_bin", lambda: "/bin/ollama")

    def run(*args, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(setup.subprocess, "run", run)
    assert setup._pull_model("qwen3:4b", base_url="http://localhost:11435")["ok"]
    assert captured["env"]["OLLAMA_HOST"] == "http://localhost:11435"
