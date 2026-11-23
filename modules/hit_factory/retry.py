"""Avoid repeating expensive renders when seed changes cannot restore a provider."""
from __future__ import annotations

from typing import Any


def stop_for_environment(attempt: dict[str, Any], log_fn) -> bool:
    """Trust explicit retry metadata on required stages, never reason substrings.

    A completed first render remains available as a draft. Unknown and transient
    errors keep the existing retry budget; quality-gate failures still evolve.
    """
    blockers = []
    for row in (attempt.get("report") or {}).get("stages") or []:
        if not isinstance(row, dict) or row.get("name") not in {"_stage_lyrics", "_stage_voice_synth"}:
            continue
        output = row.get("output") or {}
        if (row.get("status") == "BLOCKED" and isinstance(output, dict)
                and output.get("retry_scope") == "environment"):
            blockers.append({"stage": row["name"], "reason": row.get("reason") or output.get("reason"),
                             "action": output.get("action")})
    if not blockers:
        return False
    attempt["evolution_stop"] = {"reason": "environment_blocked", "blockers": blockers}
    log_fn("[HIT FACTORY] Эволюция остановлена: требуется подготовка окружения; см. evolution_stop")
    for blocker in blockers:
        log_fn(f"[HIT FACTORY] {blocker['stage']}: {blocker['reason']}; action: {blocker['action']}")
    return True
