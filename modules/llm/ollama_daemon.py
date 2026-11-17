"""Start an already installed local Ollama without a manual terminal step."""
from __future__ import annotations

import os
import subprocess
import time
from urllib.parse import urlsplit

from modules.errors import failure_reason


def start_local_daemon(binary: str, base_url: str, probe, timeout: float = 15.0) -> dict:
    """Start only a loopback daemon; never bind a public inference endpoint.

    Existing daemons are reused. On failure we terminate only the child we
    started. A healthy child remains available for subsequent lyric requests.
    Starting installed software requires no model download or remote access.
    """
    try:
        url = urlsplit(base_url)
        if (url.scheme != "http" or url.hostname not in {"localhost", "127.0.0.1", "::1"}
                or url.username or url.password or url.path not in {"", "/"}
                or url.query or url.fragment):
            return {"ok": False, "reason": "automatic daemon start requires a loopback HTTP URL"}
        port = url.port or 11434
    except ValueError as exc:
        return {"ok": False, "reason": failure_reason(exc)}
    if probe(base_url) is not None:
        return {"ok": True, "started": False}
    host = f"[{url.hostname}]" if ":" in url.hostname else url.hostname
    env = dict(os.environ, OLLAMA_HOST=f"{host}:{port}")
    options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {"start_new_session": True}
    try:
        child = subprocess.Popen(
            [binary, "serve"], env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **options,
        )
    except OSError as exc:
        return {"ok": False, "reason": failure_reason(exc)}
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if probe(base_url) is not None:
            return {"ok": True, "started": True, "pid": child.pid}
        if child.poll() is not None:
            return {"ok": False, "reason": f"ollama serve exited ({child.returncode})"}
        time.sleep(0.2)
    _stop_child(child)
    return {"ok": False, "reason": "ollama serve startup timed out"}


def _stop_child(child) -> None:
    """Reap a failed startup without killing a user's pre-existing daemon."""
    if child.poll() is not None:
        return
    child.terminate()
    try:
        child.wait(timeout=3)
    except subprocess.TimeoutExpired:
        child.kill()
        child.wait(timeout=3)


def ensure_local_server(base_url: str) -> bool:
    """Lyric requests can recover a stopped installed daemon without downloads."""
    import shutil
    from modules.llm.ollama_setup import _daemon_models

    binary = shutil.which("ollama")
    if not binary:
        return False
    return bool(start_local_daemon(binary, base_url, _daemon_models).get("ok"))
