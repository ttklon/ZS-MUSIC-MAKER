"""Normalize preflight decisions and build a typed refusal before pipeline work."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any


def _blocked_record(reason: str) -> dict:
    return {"schema": 1, "status": "blocked", "decision": "refuse", "can_attempt": False,
            "reasons": [reason], "inference_verified": False, "product_profile_accepted": False}


def _unpack_preflight(result: Any, error: Exception | None) -> tuple[Any, Any]:
    if error is not None:
        return _blocked_record(f"hardware preflight failed: {type(error).__name__}: {error}"), None
    if not isinstance(result, tuple) or len(result) != 2:
        return _blocked_record(
            "hardware preflight failed: TypeError: hardware preflight returned an invalid result pair"
        ), None
    return result


def _record_is_valid(preflight: Any) -> bool:
    return (
        isinstance(preflight, dict)
        and type(preflight.get("schema")) is int
        and preflight.get("schema") == 1
        and preflight.get("inference_verified") is False
        and preflight.get("product_profile_accepted") is False
        and isinstance(preflight.get("reasons"), list)
        and preflight.get("decision") in ("continue_unverified", "refuse")
    )


def _safe_attempt(preflight: Any, adaptive_config: Any, record_valid: bool) -> bool:
    return (
        record_valid
        and preflight.get("status") == "inventory_only"
        and preflight.get("decision") == "continue_unverified"
        and preflight.get("can_attempt") is True
        and preflight.get("selected_backend") == "procedural_dsp"
        and preflight.get("resource_budget_status") == "not_established"
        and isinstance(preflight.get("texture_route"), dict)
        and preflight["texture_route"].get("selected_backend") == "disabled"
        and preflight["texture_route"].get("inference_verified") is False
        and not preflight.get("reasons")
        and isinstance(adaptive_config, dict)
        and adaptive_config.get("use_acestep") is False
        and adaptive_config.get("use_musicgen") is False
        and adaptive_config.get("use_texture") is False
    )


def _refusal_record(preflight: Any, adaptive_config: Any, record_valid: bool) -> tuple[dict, dict | None, bool]:
    if not isinstance(preflight, dict):
        preflight = _blocked_record("hardware preflight returned a malformed record")
    else:
        preflight = dict(preflight)
        reasons = preflight.get("reasons")
        reasons = list(reasons) if isinstance(reasons, list) else []
        if not record_valid:
            reasons.append("hardware preflight record is malformed")
        elif preflight.get("decision") == "continue_unverified":
            reasons.append("hardware preflight did not satisfy the safe DSP/disabled-texture route")
        elif not reasons:
            reasons.append("hardware preflight refused without a reason")
        preflight["reasons"] = reasons
        preflight.update(status="blocked", decision="refuse", can_attempt=False,
                         inference_verified=False, product_profile_accepted=False)
    safe_config = adaptive_config if isinstance(adaptive_config, dict) else None
    return preflight, safe_config, False


def validate_preflight_result(result: Any, error: Exception | None = None) -> tuple[dict, dict | None, bool]:
    """Fail closed on malformed inventory/config and allow only the safe DSP route."""
    preflight, adaptive_config = _unpack_preflight(result, error)
    record_valid = _record_is_valid(preflight)
    if _safe_attempt(preflight, adaptive_config, record_valid):
        return preflight, adaptive_config, True
    return _refusal_record(preflight, adaptive_config, record_valid)


def preflight_refusal_report(
    answers: dict[str, Any], plan: dict[str, Any], preflight: dict,
    output_root: str, started: float, say,
) -> dict[str, Any]:
    """Return a visible typed refusal without invoking lyrics, voice or HitFactory."""
    from app.pipeline.result import assess_result

    reasons = preflight.get("reasons") if isinstance(preflight.get("reasons"), list) else []
    reasons = [str(reason) for reason in reasons if str(reason).strip()]
    if not reasons:
        reasons = ["Аппаратная проверка не разрешила запуск и не дала причины."]
    reason = "; ".join(reasons)
    report = {
        "master_reported": False,
        "answers": answers,
        "plan": plan,
        "trend": {"ok": False, "reason": "не запускались: preflight отказал до тяжёлой работы"},
        "style": {"ok": False, "reason": "не запускался анализ референсов после отказа preflight"},
        "dossier": {"ok": False, "reason": "не запускалось после отказа preflight"},
        "samples": {"ok": False, "reason": "не запускались после отказа preflight"},
        "lyrics": {"ok": False, "source": "BLOCKED", "text": "", "reason": reason},
        "voice": {"ok": False, "source": "BLOCKED", "reason": reason},
        "hit": {},
        "master_path": None,
        "hit_score": None,
        "verdict": "BLOCKED",
        "blocked": [{"stage": "hardware_preflight", "reason": reason}],
        "hardware_preflight": preflight,
        "elapsed_sec": round(time.time() - started, 1),
        "output_root": str(Path(output_root)),
        "agent_failed": "hardware preflight отказал до запуска тяжёлых стадий",
    }
    report["result"] = assess_result(report, requested_kind="generated_singing")
    report["ok"] = False
    report["artifact_available"] = False
    say(f"Аппаратная проверка: отказ до рендера — {reason}")
    return report
