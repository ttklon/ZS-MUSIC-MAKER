"""Canonical task outcome; legacy percentages are work accounting, not readiness."""
from __future__ import annotations

STATES = {"OK": "success", "FALLBACK": "degraded", "BLOCKED": "blocked",
          "FAILED": "failed", "CANCELED": "canceled"}


def _normalize(stage, index, required_names):
    try:
        row = stage.to_dict() if hasattr(stage, "to_dict") else dict(stage)
    except (TypeError, ValueError):
        row = {}
    name = row.get("name")
    invalid = not isinstance(name, str) or not name.strip()
    name = f"invalid-stage-{index}" if invalid else name
    raw = row.get("status")
    raw = getattr(raw, "value", raw)
    status = STATES.get(raw, "failed") if isinstance(raw, str) else "failed"
    reason = row.get("reason")
    required = row.get("required", True)
    if type(required) is not bool or invalid or (status == "success" and row.get("ok") is False):
        status, required, reason = "failed", True, "Некорректный или противоречивый результат стадии"
    if name in required_names:
        required = True  # executor cannot downgrade the caller's required contract
    output = row.get("output")
    if status == "success" and isinstance(output, dict) and any(output.get(k) for k in ("synthetic", "dry_run", "placeholder")):
        status = "degraded"
    return {"name": name, "status": status, "required": required,
            "reason": str(reason) if reason else ("" if status == "success" else "Причина не предоставлена исполнителем")}


def stage_outcome(stages, *, required_names=()) -> dict:
    required_names = set(required_names)
    reasons, normalized, present = [], [], set()
    for index, stage in enumerate(stages, 1):
        row = _normalize(stage, index, required_names)
        if row['name'] in present:
            row.update(status="failed", required=True, reason="Повтор имени стадии: результат неоднозначен")
        present.add(row['name'])
        normalized.append(row)
    for name in sorted(required_names - present):
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


def report_outcome(stages, *, quality_failures=(), dry_run=False, only=None, required_names=()) -> dict:
    outcome = stage_outcome(stages, required_names=required_names)
    if quality_failures:
        outcome.update(status="failed", succeeded=False)
        outcome["reasons"].extend(str(item) for item in quality_failures)
    elif (dry_run or only) and outcome["status"] == "success":
        outcome.update(status="degraded", succeeded=False)
        outcome["reasons"].append("Пробный или частичный прогон не подтверждает полный конвейер.")
    return outcome


def outcome_from_report(report) -> dict:
    """Adapters cannot promote a legacy PASS or override a stricter producer outcome."""
    outcome = report_outcome(report.get('stages', []),
        quality_failures=report.get('quality_gate_failures') or (),
        dry_run=bool(report.get('dry_run')), only=report.get('only'))
    declared = report.get('outcome')
    if declared is not None:
        order = ('failed', 'canceled', 'blocked', 'degraded', 'success')
        if (not isinstance(declared, dict) or declared.get('status') not in order
                or ('succeeded' in declared and declared['succeeded'] is not (declared.get('status') == 'success'))):
            outcome.update(status='failed', succeeded=False)
            outcome['reasons'].append('Некорректный канонический outcome исполнителя')
        elif order.index(declared['status']) < order.index(outcome['status']):
            outcome.update(status=declared['status'], succeeded=False)
            outcome['reasons'].extend(declared.get('reasons') or [])
    return outcome
