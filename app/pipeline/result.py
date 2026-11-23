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


def assess_result(report: dict, *, requested_kind=None) -> dict:
    """Validate audio, bind content evidence to its hash, enforce requested kind."""
    malformed = not isinstance(report, dict)
    report = report if not malformed else {}
    requested = requested_kind if requested_kind is not None else report.get("requested_kind", "generated_singing")
    issue = _execution_issue(report, requested)
    artifact = inspect_audio(None if issue and issue[0] == "canceled" else report.get("master_path"))
    result = {"schema": 1, "status": "failed", "kind": "unverified_audio", "succeeded": False,
              "label": LABELS["unverified_audio"], "artifact": artifact, "reasons": [],
              "quality_accepted": False, "requested_kind": requested}
    if malformed:
        result['reasons'] = ['Исполнитель не вернул объект отчёта.']
        return result
    if issue and issue[0] == 'canceled':
        result.update(status=issue[0], reasons=issue[1])
        return result
    if not artifact["valid"]:
        result["reasons"].append(artifact["reason"])
        return result
    if issue:
        result.update(status=issue[0], reasons=issue[1])
        return result
    hit = report.get("hit") if isinstance(report.get("hit"), dict) else {}
    evidence = report.get("render_evidence", hit.get("render_evidence", {}))
    kind = evidence.get("kind") if isinstance(evidence, dict) else None
    missing = _missing_evidence(evidence, kind, artifact)
    result["status"] = "degraded"
    if missing:
        result["reasons"] = missing
        return result
    result.update(kind=kind, label=LABELS[kind])
    if not isinstance(requested, str) or requested not in KINDS or requested != kind:
        result["reasons"].append(f"Запрошено {requested}, получено {kind}; тип результата не подменяется.")
    if not result["reasons"]:
        result.update(status="success", succeeded=True)
    return result


def _missing_evidence(evidence, kind, artifact: dict) -> list[str]:
    if not isinstance(evidence, dict) or not isinstance(kind, str) or kind not in KINDS:
        return ["Нет подтверждения состава аудио от исполнителя; наличие WAV не доказывает песню."]
    reasons = []
    if type(evidence.get("schema")) is not int or evidence.get("schema") != 1 or evidence.get("master_sha256") != artifact["sha256"]:
        reasons.append("Происхождение не связано с текущим аудиофайлом.")
    if any(not isinstance(evidence.get(key), str) or not evidence[key].strip() for key in ("engine", "revision")):
        reasons.append("Не указаны движок и версия исполнителя.")
    if any(evidence.get(key) for key in ("synthetic", "placeholder", "dry_run")):
        reasons.append("Симуляция или заглушка не подтверждает результат генерации.")
    checks = evidence.get("checks") or {}
    if not isinstance(checks, dict) or any(checks.get(key) is not True for key in CHECKS[kind]):
        reasons.append("Не подтверждены обязательные проверки содержимого и тайминга.")
    if kind == "generated_singing" and evidence.get("vocal_method") != "singing":
        reasons.append("TTS и RVC сами по себе не подтверждают генерацию пения.")
    return reasons


def _execution_issue(report, requested):
    """Content evidence must never override failed, partial or simulated execution."""
    from app.pipeline.outcome import outcome_from_report
    issues = []
    hit = report.get('hit')
    for data in (report, hit if isinstance(hit, dict) else {}):
        if data.get('canceled') or data.get('status') == 'canceled':
            issues.append(('canceled', ['Операция отменена; файл не считается готовым результатом.']))
        if data.get('agent_failed') or data.get('error') or data.get('failed') or data.get('status') == 'failed':
            issues.append(('failed', ['Исполнитель сообщил об ошибке; происхождение файла не отменяет отказ.']))
        if requested in ('generated_singing', 'own_vocal_song'):
            voice = data.get('voice')
            if 'voice' in data and (not isinstance(voice, dict) or voice.get('ok') is False or
                    voice.get('empty') or voice.get('silent') or voice.get('source') in ('tts', 'silero', 'xtts', 'speech')):
                issues.append(('degraded', ['Вокал отсутствует, пуст, речевой или противоречит заявленному пению.']))
        if requested == 'generated_singing' and isinstance(data.get('lyrics'), dict) and data['lyrics'].get('ok') is False:
            issues.append(('degraded', ['Применение текста не подтверждено исполнителем.']))
        if data.get('blocked') or ('blocked' in data and not isinstance(data['blocked'], list)):
            issues.append(('degraded', ['В отчёте остаются заблокированные или некорректно описанные стадии.']))
        if data.get('dry_run') or data.get('only') or data.get('synthetic') or data.get('placeholder'):
            issues.append(('degraded', ['Пробный, частичный или синтетический прогон не подтверждает полный результат.']))
        if (any(key in data for key in ('outcome', 'stages')) or data.get('quality_gate_failures')
                or ('quality_gate_failures' in data and not isinstance(data['quality_gate_failures'], list))):
            try:
                outcome = outcome_from_report(data)
                if not outcome['succeeded']:
                    status = outcome['status'] if outcome['status'] in ('failed', 'canceled') else 'degraded'
                    issues.append((status, ['Прогон не принят: ' + '; '.join(outcome['reasons'])]))
            except (TypeError, ValueError, KeyError):
                issues.append(('failed', ['Некорректные результаты стадий исполнителя.']))
    return next((item for state in ('canceled', 'failed', 'degraded') for item in issues if item[0] == state), None)
