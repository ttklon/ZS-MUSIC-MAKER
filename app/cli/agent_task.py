# -*- coding: utf-8 -*-
"""
app/cli/agent_task.py — «Сделать хит» из окна: тихая докачка, прогон, отчёт.

Почему отдельная задача, а не `--hit-factory`: окну нужен не список треков,
а один понятный результат и построчный лог. Плюс первый запуск обязан сам
себя подготовить: `--agent-hit` сначала молча проверяет тяжёлые движки и,
если сеть разрешена, докачивает их — иначе человек нажимает кнопку и получает
«heavy engines unavailable» вместо трека.

Флаги повторяют чек-лист агентика (4 вопроса), а не настройки пайплайна:

    python main.py --agent-hit --agent-mood "ночной город" \
        --agent-artist ICEGERGERT --agent-refs "C:\\ref.wav" --agent-voice record
"""

from __future__ import annotations

import json

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


def _progress(message: str) -> None:
    safe_print(f"[agent-hit] {message}")


def run_agent_hit(args) -> int:
    """Выполнить прогон и вернуть код: 0 — трек есть, 1 — нет, 2 — сбой."""
    from app.core.net_policy import network_allowed

    allow_online = bool(getattr(args, "online", False)) or network_allowed()
    _progress("проверяю окружение и движки (тихо, без вопросов)…")
    _prepare(allow_online)

    try:
        from modules.agent_guide import narrate, run_conversation_hit, verdict

        report = run_conversation_hit(
            build_payload(args),
            output_root=getattr(args, "agent_output", "") or "output/hits",
            progress=_progress,
        )
    except Exception as exc:  # noqa: BLE001 — причина видна человеку, не трейсбек
        safe_print(f"[agent-hit] прогон упал: {type(exc).__name__}: {exc}")
        return 2

    safe_print(json.dumps(
        {
            "verdict": verdict(report),
            "master_path": report.get("master_path"),
            "hit_score": report.get("hit_score"),
            "blocked": report.get("blocked"),
            "elapsed_sec": report.get("elapsed_sec"),
        },
        ensure_ascii=False,
    ))
    for line in narrate(report).splitlines():
        safe_print(f"[agent-hit] {line}")
    return 0 if report.get("master_path") else 1
