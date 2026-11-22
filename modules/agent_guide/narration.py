# -*- coding: utf-8 -*-
"""
modules.agent_guide.narration — что агентик говорит человеку после прогона.

Отчёт прогона — это данные. Здесь — одна честная фраза для окна: что
получилось, что нет и что сделать, чтобы заработало. Без «почти всё готово»:
если вокала нет, так и написано.
"""

from __future__ import annotations

from typing import Any

# Что делать с конкретной заблокированной ступенью. Ключ — имя стадии из
# `runner._blocked_stages`; текст — действие пользователя, а не отговорка.
ACTIONS = {
    "lyrics": "запусти Ollama и скачай qwen: `ollama pull qwen3:4b`",
    "voice": "запиши 30-60 секунд голоса в разделе «Вокал» — RVC сделает клон",
    "samples": "сэмплы необязательны: бит собирается из встроенного банка",
    "references": "референсы необязательны: можно указать файл или ссылку",
    "trends": "тренды недоступны офлайн — тема берётся из встроенного словаря",
}


def narrate(report: dict[str, Any]) -> str:
    """Короткий рассказ о прогоне: что сделано и что честно не вышло."""
    lines: list[str] = []
    master = report.get("master_path")
    from app.pipeline.result import assess_result
    result = assess_result(report)
    if master:
        lines.append(f"{result['label']}: {master} · статус {result['status']}")
        lines.extend(result['reasons'])
    else:
        lines.append(f"Трек не собрался: {report.get('agent_failed') or 'нет мастера'}")
    lyrics = (report.get("lyrics") or {}).get("ok")
    voice = (report.get("voice") or {}).get("ok")
    lines.append(
        f"Текст: {'локальная LLM (Ollama)' if lyrics else 'нет — BLOCKED'}; "
        f"голос: {str((report.get('voice') or {}).get('source') or 'источник не указан') if voice else 'без вокала'}"
    )
    for item in report.get("blocked") or []:
        stage = item.get("stage", "")
        action = ACTIONS.get(stage, "")
        lines.append(f"· {stage}: {item.get('reason')}" + (f" → {action}" if action else ""))
    return "\n".join(lines)


def verdict(report: dict[str, Any]) -> str:
    """Совместимая проекция контракта: COMPLETE / PARTIAL / FAILED, не HIT."""
    from app.pipeline.result import assess_result

    result = assess_result(report)
    if result["status"] in ("failed", "canceled"):
        return "FAILED"
    return "COMPLETE" if result["succeeded"] else "PARTIAL"
