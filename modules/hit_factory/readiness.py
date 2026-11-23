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




def _explicit_optional_skip(row: dict[str, Any]) -> bool:
    """A bypassed vocal processor must preserve real, decodable upstream audio."""
    output = row.get("output")
    if (row.get("status") != "BLOCKED" or not isinstance(output, dict)
            or output.get("requested") is not False
            or output.get("skip_kind") != "user_disabled"):
        return False
    if row.get("name") == "_stage_stems":
        return True
    if row.get("name") in {"_stage_rvc", "_stage_vocal_fx"} and not output.get("synthetic"):
        from modules.voice_output import usable_voice

        path = output.get("retained_path")
        return isinstance(path, str) and usable_voice(path)
    return False


def _pipeline_issues(report: dict[str, Any]) -> list[str]:
    """Only an explicit user opt-out of optional processing may be non-blocking.

    Do not infer consent from human-readable reasons, absent dependencies,
    partial runs, or a generic 'optional' flag on an essential stage.
    Keep the original BLOCKED stage and pipeline verdict visible in reports.
    """
    status = report.get("status_summary") or {}
    rows = [row for row in report.get("stages") or [] if isinstance(row, dict)]
    blocked = set(status.get("blocked") or [])
    failed = set(status.get("failed") or [])
    opted_out = set()
    for row in rows:
        name = row.get("name")
        if row.get("status") == "FAILED":
            failed.add(name)
        if row.get("status") == "BLOCKED":
            blocked.add(name)
    for name in blocked:
        matching = [row for row in rows if row.get("name") == name]
        if matching and all(_explicit_optional_skip(row) for row in matching):
            opted_out.add(name)
    issues = []
    verdict = report.get("verdict")
    accepted = verdict in {"PASS", "PASS_WITH_FALLBACK"}
    if verdict == "PASS_BLOCKED" and opted_out and not (blocked - opted_out) and not failed:
        accepted = True
    if not accepted:
        issues.append("pipeline incomplete: " + str(verdict or "unknown"))
    if failed or blocked - opted_out:
        issues.append("pipeline has failed or blocked stages")
    if report.get("only"):
        issues.append("partial --only run is not a complete render")
    return issues


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
    reasons.extend(_pipeline_issues(report))
    if report.get("dry_run"):
        reasons.append("dry run is not a render")
    if report.get("quality_gate_failures"):
        reasons.append("audio quality gates failed")
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
