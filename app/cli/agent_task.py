# -*- coding: utf-8 -*-
"""
app/cli/agent_task.py — «Сделать хит» из окна: тихая докачка, прогон, отчёт.

Почему отдельная задача, а не `--hit-factory`: окну нужен не список треков,
а один результат в версионированном NDJSON и отдельный обычный лог. Плюс первый запуск обязан сам
себя подготовить: `--agent-hit` сначала молча проверяет тяжёлые движки и,
если сеть разрешена, докачивает их — иначе человек нажимает кнопку и получает
«heavy engines unavailable» вместо трека.

Флаги повторяют чек-лист агентика (4 вопроса), а не настройки пайплайна:

    python main.py --agent-hit --agent-mood "ночной город" \
        --agent-artist ICEGERGERT --agent-refs "C:\\ref.wav" --agent-voice record
"""

from __future__ import annotations

from app.cli.env import safe_print


def build_payload(args) -> dict:
    """Аргументы CLI → ответы агентика (те же ключи, что у окна)."""
    return {
        "mood": getattr(args, "agent_mood", "") or "",
        "artist": getattr(args, "agent_artist", "") or "",
        "refs": getattr(args, "agent_refs", "") or "",
        "voice": getattr(args, "agent_voice", "") or "",
    }


def _prepare(allow_online: bool) -> dict:
    """Тихая подготовка: тяжесть и модели только при разрешённой сети."""
    try:
        from app.core.bootstrap import auto_bootstrap

        return auto_bootstrap(silent=True, allow_download=allow_online)
    except Exception as exc:  # noqa: BLE001 — подготовка не должна ронять прогон
        safe_print(f"[agent-hit] подготовка пропущена: {type(exc).__name__}: {exc}")
        return {"error": f"{type(exc).__name__}: {exc}"}


def run_agent_hit(args) -> int:
    """Код 0 — контракт результата принят, 1 — неполный/ошибочный результат, 2 — сбой."""
    from app.core.net_policy import network_allowed

    from app.cli.task_events import TaskEvents

    events = TaskEvents()
    allow_online = bool(getattr(args, "online", False)) or network_allowed()
    events.progress("Проверяю окружение и движки…")
    _prepare(allow_online)

    try:
        from modules.agent_guide import narrate, run_conversation_hit

        report = run_conversation_hit(
            build_payload(args),
            output_root=getattr(args, "agent_output", "") or "output/hits",
            progress=events.progress,
        )
    except Exception as exc:  # noqa: BLE001 — причина видна человеку, не трейсбек
        events.emit("error", message=f"{type(exc).__name__}: {exc}")
        events.emit("done", ok=False, report={"error": str(exc)})
        return 2

    from app.pipeline.result import assess_result
    if not isinstance(report, dict):
        events.emit("error", message="Исполнитель не вернул объект отчёта")
        events.emit("done", ok=False, report={"error": "malformed producer report"})
        return 2
    result = assess_result(report, requested_kind="generated_singing")
    summary = {
        "verdict": "COMPLETE" if result["succeeded"] else ("FAILED" if result["status"] in ("failed", "canceled") else "PARTIAL"),
        "result": result, "master_path": report.get("master_path"),
        "hit_score": report.get("hit_score"), "blocked": report.get("blocked"),
        "elapsed_sec": report.get("elapsed_sec"),
    }
    if report.get("master_path"):
        events.emit("artifact", role="master", path=str(report["master_path"]))
    events.emit("done", ok=result["succeeded"], report=summary)
    for line in narrate(dict(report, requested_kind="generated_singing")).splitlines():
        safe_print(f"[agent-hit] {line}")
    return 0 if result["succeeded"] else 1
