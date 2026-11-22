"""Canonical task outcome; legacy percentages are work accounting, not readiness."""
from __future__ import annotations

STATES = {"OK": "success", "FALLBACK": "degraded", "BLOCKED": "blocked",
          "FAILED": "failed", "CANCELED": "canceled"}


def stage_outcome(stages, *, required_names=()) -> dict:
    rows = [s.to_dict() if hasattr(s, "to_dict") else dict(s) for s in stages]
    reasons = []
    normalized = []
    for row in rows:
        status = STATES.get(str(row.get("status")), "failed")
        output = row.get("output")
        if status == "success" and isinstance(output, dict) and any(output.get(k) for k in ("synthetic", "dry_run", "placeholder")):
            status = "degraded"
        normalized.append({"name": row.get("name", "?"), "status": status,
                           "required": row.get("required", True),
                           "reason": row.get("reason") or ("" if status == "success" else "Причина не предоставлена исполнителем")})
    present = {row["name"] for row in normalized}
    for name in sorted(set(required_names) - present):
        normalized.append({"name": name, "status": "blocked", "required": True, "reason": "Обязательная стадия не выполнена"})
    mandatory = [row for row in normalized if row["required"]]
    if not mandatory:
        status = "blocked"
        reasons.append("Нет результатов обязательных стадий.")
    else:
        status = next((s for s in ("failed", "canceled", "blocked", "degraded")
                       if any(row["status"] == s for row in mandatory)), "success")
        if status == "success" and any(row["status"] != "success" for row in normalized):
            status = "degraded"
    reasons.extend(f"{row['name']}: {row['reason']}" for row in normalized if row["status"] != "success")
    return {"schema": 1, "status": status, "succeeded": status == "success",
            "reasons": reasons, "stages": normalized, "song_verified": False}


def report_outcome(stages, *, quality_failures=(), dry_run=False, only=None) -> dict:
    outcome = stage_outcome(stages)
    if quality_failures:
        outcome.update(status="failed", succeeded=False)
        outcome["reasons"].extend(str(item) for item in quality_failures)
    elif (dry_run or only) and outcome["status"] == "success":
        outcome.update(status="degraded", succeeded=False)
        outcome["reasons"].append("Пробный или частичный прогон не подтверждает полный конвейер.")
    return outcome
