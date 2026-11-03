# -*- coding: utf-8 -*-
"""
app/core/pipeline_runtime.py — рантайм стадий: тайминг, честные статусы,
детерминизм и управление частичным прогоном.

Здесь нет ни одной предметной стадии. Только правила, по которым пайплайн
вызывает стадию и трактует её результат:

* `_timed`  — исключение стадии становится статусом FAILED, а не падением;
* `_blocked`— стадия не выполнялась по заведомой причине;
* `STAGE_KEYS` / `--only` — явный список того, что можно запускать по частям;
* `_apply_seed` — фиксирует ГПСЧ, без этого «детерминизм» — лозунг.
"""

from __future__ import annotations

import logging

import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.pipeline import StageResult, StageStatus, classify


# --------------------------------------------------------------------------- #
#  Детерминизм, частичный прогон и возобновление
# --------------------------------------------------------------------------- #
# Ключи стадий для `--only` — ровно те шаги, которые пользователь различает.
STAGE_KEYS = (
    "analysis",
    "groove",
    "arrangement",
    "beat",
    "texture",
    "lyrics",
    "vocal",
    "mix",
    "master",
    "polish",
    "stems",
    "hit_score",
    "release",
)

MASTER_STANDS = (
    "streaming",
    "car",
    "club",
    "tiktok",
    "airpods",
    "bluetooth",
    "headphones",
    "monitors",
)
STEM_NAMES = ("drums", "bass", "vocals", "other")

STAGE_RECORDS = (
    "_stage_analyze", "_stage_groove",
    "_stage_arrangement",
    "_stage_beat",
    "_stage_texture",
    "_stage_lyrics",
    "_stage_voice_synth",
    "_stage_rvc",
    "_stage_vocal_fx",
    "_stage_mix_and_sidechain",
    "_stage_mastering",
    "_stage_polish",
    "_stage_stems",
    "_stage_hit_score",
    "_stage_release_pack",
)

def _apply_seed(seed: int | None) -> None:
    """Зафиксировать глобальные ГПСЧ, чтобы прогон был воспроизводим."""
    if seed is None:
        return
    import random

    random.seed(int(seed))
    try:
        import numpy as np

        np.random.seed(int(seed) % (2**32 - 1))
    except Exception:  # noqa: BLE001 - numpy опционален
        logging.getLogger(__name__).debug("ignored exception", exc_info=True)


def _wanted(only: set[str] | None, key: str) -> bool:
    return only is None or key in only


def _timed(name: str, fn: Callable[[], Any]) -> StageResult:
    """Выполнить стадию, замерить время и классифицировать результат.

    Исключение внутри стадии не роняет пайплайн: оно становится статусом
    FAILED с текстом ошибки, чтобы отчёт показал, что именно сломалось.
    """
    started = time.time()
    output: Any = None
    failed = False
    reason: str | None = None
    try:
        output = fn()
    except Exception as exc:  # noqa: BLE001 - стадия обязана быть изолирована
        failed = True
        reason = f"{type(exc).__name__}: {exc}"
    return classify(
        output,
        failed=failed,
        reason=reason,
        duration_sec=time.time() - started,
        name=name,
    )


def _blocked(name: str, reason: str) -> StageResult:
    """Честно пропущенная стадия (нет входа или выключена пользователем)."""
    return StageResult(name=name, status=StageStatus.BLOCKED, reason=reason)


def _normalize_path_map(data: Any, keys: list[str] | None = None) -> dict[str, str]:
    """Оставить в словаре только реальные пути, отбросив пустые значения."""
    out: dict[str, str] = {}
    if not isinstance(data, dict):
        return out
    allow = set(keys or [])
    for name, value in data.items():
        if allow and name not in allow:
            continue
        path = None
        if isinstance(value, (str, Path)):
            path = str(value)
        elif isinstance(value, dict):
            path = value.get("out_wav") or value.get("path")
        if path:
            out[str(name)] = str(path)
    return out


def _output(stage: StageResult) -> dict[str, Any]:
    return stage.output if isinstance(stage.output, dict) else {}


def _quality_gate_failures(stages: list[StageResult]) -> list[str]:
    """Quality is separate from execution: a written WAV can still fail gates."""
    failures: list[str] = []
    for stage in stages:
        output = _output(stage)
        if stage.name == "_stage_mix_and_sidechain":
            if output.get("gates_passed") is False:
                bad = [name for name, passed in (output.get("gates") or {}).items() if not passed]
                failures.append("mix: " + (", ".join(bad) or "gates failed"))
            reference = output.get("reference") or {}
            if reference.get("gates_passed") is False:
                bad = [name for name, passed in (reference.get("gates") or {}).items() if not passed]
                failures.append("reference match: " + (", ".join(bad) or "gates failed"))
        if stage.name == "_stage_mastering":
            summary = output.get("summary") or {}
            if summary.get("gates_passed") is False:
                failures.append("mastering: " + str(summary.get("failed_gates") or "gates failed"))
    return failures
