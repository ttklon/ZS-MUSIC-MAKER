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


def _preparation_summary(value) -> dict:
    """Keep setup outcome visible without confusing it with inference success."""
    if not isinstance(value, dict):
        return {"schema": 1, "ok": False, "blockers": ["setup returned no object"],
                "inference_verified": False}
    blockers = value.get("blockers")
    has_blocker_summary = isinstance(blockers, list)
    if not has_blocker_summary:
        blockers = [value.get("error") or "setup did not return a validated summary"]
    protocol = value.get("worker_protocol")
    protocol_summary = None
    if isinstance(protocol, dict):
        protocol_summary = {key: protocol.get(key) for key in ("ok", "profile", "isolated")
                            if key in protocol}
        protocol_summary["inference_verified"] = False
    return {
        "schema": 1,
        "ok": value.get("ok") is True and has_blocker_summary and not blockers,
        "blockers": [str(item)[:300] for item in blockers[:24]],
        "readiness_before": value.get("readiness_before"),
        "readiness_after": value.get("readiness_after"),
        "worker_protocol": protocol_summary,
        "inference_verified": False,
    }


def run_agent_hit(args) -> int:
    """Код 0 — контракт результата принят, 1 — неполный/ошибочный результат, 2 — сбой."""
    from app.core.net_policy import network_allowed

    from app.cli.task_events import TaskEvents

    events = TaskEvents()
    allow_online = bool(getattr(args, "online", False)) or network_allowed()
    events.progress("Проверяю окружение и движки…")
    preparation = _preparation_summary(_prepare(allow_online))
    events.progress("Подготовка проверена; inference отдельно не подтверждён." if preparation["ok"] else
                    "Подготовка неполная; выбранный маршрут будет проверен отдельно.")

    try:
        from modules.agent_guide import narrate, run_conversation_hit

        report = run_conversation_hit(
            build_payload(args),
            output_root=getattr(args, "agent_output", "") or "output/hits",
            progress=events.progress,
            preparation=preparation,
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
    report.setdefault("preparation", preparation)
    hardware_preflight = report.get("hardware_preflight")
    if not isinstance(hardware_preflight, dict):
        nested_hit = report.get("hit") if isinstance(report.get("hit"), dict) else {}
        nested_pipeline = nested_hit.get("report") if isinstance(nested_hit.get("report"), dict) else {}
        hardware_preflight = nested_pipeline.get("hardware_preflight") or nested_hit.get("hardware_preflight")
    result = assess_result(report, requested_kind="generated_singing")
    summary = {
        "verdict": "COMPLETE" if result["succeeded"] else ("FAILED" if result["status"] in ("failed", "canceled") else "PARTIAL"),
        "result": result, "master_path": report.get("master_path"),
        "hit_score": report.get("hit_score"), "blocked": report.get("blocked"),
        "elapsed_sec": report.get("elapsed_sec"),
        "preparation": report.get("preparation"),
        "hardware_preflight": hardware_preflight,
    }
    if report.get("master_path"):
        events.emit("artifact", role="master", path=str(report["master_path"]))
    events.emit("done", ok=result["succeeded"], report=summary)
    for line in narrate(dict(report, requested_kind="generated_singing")).splitlines():
        safe_print(f"[agent-hit] {line}")
    return 0 if result["succeeded"] else 1
