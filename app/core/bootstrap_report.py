"""Explain setup blockers independently of the heuristic readiness percentage."""
from __future__ import annotations


def summarize_setup(result: dict) -> dict:
    """Successful setup is not a guarantee of successful song generation."""
    blockers = []
    for stage in ("heavy", "models"):
        state = result.get(stage) or {}
        for key in ("failed", "skipped"):
            for name in state.get(key) or []:
                blockers.append(f"{stage}.{name}: {key}")
    ollama = result.get("ollama") or {}
    if ollama.get("ok") is not True:
        blockers.append("ollama: " + str(ollama.get("reason") or ollama.get("action") or "not verified"))
    for stage, flag in (("rvc", "present"), ("rvc_trainer", "present"), ("rvc_env", "ok")):
        state = result.get(stage) or {}
        if state.get(flag) is not True:
            blockers.append(stage + ": " + str(state.get("reason") or "not verified"))
    return {"ok": not blockers, "blockers": blockers, "inference_verified": False}
