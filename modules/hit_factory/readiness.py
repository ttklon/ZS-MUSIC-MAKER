"""Separate pipeline completion from a heuristic musical rating."""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any


def usable_score(value: Any) -> bool:
    """Only finite scores in the scorer's documented range are comparable."""
    return (
        isinstance(value, (int, float)) and not isinstance(value, bool)
        and math.isfinite(value) and 0 <= value <= 100
    )


def attempt_readiness(attempt: dict[str, Any]) -> dict[str, Any]:
    """A high score alone never certifies a complete, verified render.

    Missing evidence is a blocker, not an implicit success. This is technical
    readiness only: neither a completed render nor a high rating guarantees
    audience success.
    """
    reasons: list[str] = []
    master = attempt.get("master_path")
    if not master or not Path(master).is_file():
        reasons.append("master file missing")
    if not usable_score(attempt.get("hit_score")):
        reasons.append("invalid or missing hit score")
    hit = attempt.get("hit") or {}
    if hit.get("error") or hit.get("verdict") == "invalid_audio":
        reasons.append(str(hit.get("error") or hit.get("reason") or "invalid audio"))
    report = attempt.get("report") or {}
    if report.get("verdict") not in {"PASS", "PASS_WITH_FALLBACK"}:
        reasons.append("pipeline incomplete: " + str(report.get("verdict") or "unknown"))
    if report.get("dry_run"):
        reasons.append("dry run is not a render")
    if report.get("quality_gate_failures"):
        reasons.append("audio quality gates failed")
    status = report.get("status_summary") or {}
    if status.get("failed") or status.get("blocked"):
        reasons.append("pipeline has failed or blocked stages")
    if hit.get("warnings"):
        reasons.append("scoring has unverified measurements")
    return {"ready": not reasons, "reasons": reasons}


def attempt_rank(attempt: dict[str, Any]) -> tuple[bool, bool, float]:
    """Prefer complete renders, then valid audio, then heuristic score."""
    readiness = attempt_readiness(attempt)
    hit = attempt.get("hit") or {}
    score = attempt.get("hit_score")
    valid = usable_score(score) and not hit.get("error") and hit.get("verdict") != "invalid_audio"
    if "master_path" in attempt:
        master = attempt.get("master_path")
        valid = valid and bool(master) and Path(master).is_file()
    return readiness["ready"], bool(valid), float(score) if valid else -1.0
