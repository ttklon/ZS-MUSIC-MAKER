"""Conservative content contract. Evidence is producer provenance, NOT an AI listening test.

No current producer supplies accepted content evidence: legacy audio stays degraded.
A claimed source='rvc', high score or a transcript cannot certify singing.
"""
from __future__ import annotations

from app.pipeline.artifact import inspect_audio

KINDS = {"instrumental", "speech_draft", "own_vocal_song", "generated_singing"}
LABELS = {"instrumental": "Инструментал", "speech_draft": "Речевой черновик",
          "own_vocal_song": "Песня со своей записью", "generated_singing": "Автоматическое пение",
          "unverified_audio": "Аудиочерновик: состав не подтверждён"}
CHECKS = {
    "instrumental": {"music_present"},
    "speech_draft": {"speech_present"},
    "own_vocal_song": {"music_present", "vocal_mixed", "own_recording", "timing_checked"},
    "generated_singing": {"music_present", "vocal_mixed", "lyrics_applied", "pitch_text_aligned"},
}


def assess_result(report: dict) -> dict:
    """Validate audio, bind content evidence to its hash, enforce requested kind."""
    artifact = inspect_audio(report.get("master_path"))
    result = {"schema": 1, "status": "failed", "kind": "unverified_audio", "succeeded": False,
              "label": LABELS["unverified_audio"], "artifact": artifact, "reasons": [],
              "quality_accepted": False}
    if report.get("canceled") is True:
        result.update(status="canceled", reasons=["Операция отменена; файл не считается готовым результатом."])
        return result
    if not artifact["valid"]:
        result["reasons"].append(artifact["reason"])
        return result
    hit = report.get("hit") if isinstance(report.get("hit"), dict) else {}
    evidence = report.get("render_evidence") or hit.get("render_evidence") or {}
    kind = evidence.get("kind") if isinstance(evidence, dict) else None
    missing = _missing_evidence(evidence, kind, artifact)
    result["status"] = "degraded"
    if missing:
        result["reasons"] = missing
        return result
    result.update(kind=kind, label=LABELS[kind])
    requested = report.get("requested_kind", "generated_singing")
    if not isinstance(requested, str) or requested not in KINDS or requested != kind:
        result["reasons"].append(f"Запрошено {requested}, получено {kind}; тип результата не подменяется.")
    if report.get("blocked"):
        result["reasons"].append("В отчёте остаются заблокированные стадии.")
    if not result["reasons"]:
        result.update(status="success", succeeded=True)
    return result


def _missing_evidence(evidence, kind, artifact: dict) -> list[str]:
    if not isinstance(evidence, dict) or not isinstance(kind, str) or kind not in KINDS:
        return ["Нет подтверждения состава аудио от исполнителя; наличие WAV не доказывает песню."]
    reasons = []
    if evidence.get("schema") != 1 or evidence.get("master_sha256") != artifact["sha256"]:
        reasons.append("Происхождение не связано с текущим аудиофайлом.")
    if not evidence.get("engine") or not evidence.get("revision"):
        reasons.append("Не указаны движок и версия исполнителя.")
    checks = evidence.get("checks") or {}
    if not isinstance(checks, dict) or any(checks.get(key) is not True for key in CHECKS[kind]):
        reasons.append("Не подтверждены обязательные проверки содержимого и тайминга.")
    if kind == "generated_singing" and evidence.get("vocal_method") != "singing":
        reasons.append("TTS и RVC сами по себе не подтверждают генерацию пения.")
    return reasons
