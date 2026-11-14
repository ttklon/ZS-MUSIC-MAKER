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


# Гейт T1 (`docs/IMPROVEMENT_PLAN.md`): стадия, объявленная как содержательная,
# обязана вернуть непустой ключевой результат. Раньше `_stage_arrangement` отдавала
# `{"ok": True, "plan": {"sections": []}}` и получала статус OK при пустом выходе.
#
# Значения — пути через точку (`plan.sections`): контракт проверяет именно то поле,
# которое стадия обязана заполнить, а не обёртку вокруг него.
# Честные BLOCKED/FALLBACK/dry-run освобождены — у них отказ уже выражен статусом.
STAGE_CONTRACT: dict[str, tuple[str, ...]] = {
    "_stage_analysis": ("analysis",),
    "_stage_arrangement": ("plan.sections",),
    "_stage_beat": ("path",),
    "_stage_texture": ("path",),
    "_stage_lyrics": ("text", "lyrics"),
    "_stage_vocal_fx": ("path", "out_wav"),
    "_stage_mix_and_sidechain": ("out_wav", "path"),
    "_stage_mastering": ("masters", "stands"),
    "_stage_polish": ("path", "output"),
    "_stage_hit_score": ("hit_score", "metrics"),
    "_stage_release_pack": ("release_dir", "files"),
}


def _contract_value(output: dict[str, Any], path: str) -> Any:
    """Достать значение по пути `a.b.c`; отсутствие любого звена — None."""
    current: Any = output
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _is_empty_value(value: Any) -> bool:
    """Пустой результат — это None, пустая строка, пустой список/словарь."""
    if value is None:
        return True
    if isinstance(value, (str, bytes, list, tuple, dict, set)):
        return len(value) == 0
    return False


def _contract_failures(stage: StageResult, output: dict[str, Any]) -> list[str]:
    """Проверить непустоту объявленного результата стадии."""
    paths = STAGE_CONTRACT.get(stage.name)
    if not paths:
        return []
    if stage.status is StageStatus.BLOCKED:
        return []
    if output.get("dry_run") or stage.is_simulation:
        return []
    if output.get("fallback_used") or stage.status is StageStatus.FALLBACK:
        return []
    if any(not _is_empty_value(_contract_value(output, path)) for path in paths):
        return []
    declared = " / ".join(paths)
    return [f"{stage.name}: empty result ({declared})"]


def _quality_gate_failures(stages: list[StageResult]) -> list[str]:
    """Quality is separate from execution: a written WAV can still fail gates."""
    failures: list[str] = []
    for stage in stages:
        output = _output(stage)
        failures.extend(_contract_failures(stage, output))
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


def _stage_callable(name: str) -> Callable[..., dict[str, Any]]:
    """Взять реализацию стадии из фасада оркестратора во время вызова.

    Оркестратор импортирует эти функции к себе, и тесты/эксперименты подменяют
    именно его атрибуты. Прямой импорт из `app.core.stages.*` сделал бы такую
    подмену молчаливой и неработающей. Цикл импортов разрывается ленивым
    импортом внутри функции.
    """
    import sys

    facade = sys.modules.get("app.core.orchestrator")
    override = getattr(facade, name, None) if facade is not None else None
    if callable(override):
        return override
    from app.core.stages import master as master_stage
    from app.core.stages import texture as texture_stage

    from app.core.stages import prep as prep_stage

    fallback = {
        "_stage_texture": texture_stage._stage_texture,
        "_stage_mastering": master_stage._stage_mastering,
        "_stage_arrangement": prep_stage._stage_arrangement,
    }[name]
    return fallback


def _run_texture_stage(
    recipe: dict[str, Any],
    out_root: Path,
    reused_stages: dict[str, StageResult],
    only: Any,
) -> StageResult:
    """Текстура: переиспользование → запуск с режимом качества → блокировка."""
    if "_stage_texture" in reused_stages:
        return reused_stages["_stage_texture"]
    if not _wanted(only, "texture"):
        return _blocked("_stage_texture", "skipped by --only")
    return _timed(
        "_stage_texture",
        lambda: _stage_callable("_stage_texture")(
            f"{recipe['genre']} atmosphere with {recipe['theme']}",
            out_root,
            quality_mode=recipe["quality_mode"],
        ),
    )


def _run_mastering_stage(
    recipe: dict[str, Any],
    mix_wav: str | None,
    out_root: Path,
    only: Any,
) -> StageResult:
    """Мастер: число итераций доводки берётся из профиля качества рецепта."""
    if not _wanted(only, "master"):
        return _blocked("_stage_mastering", "skipped by --only")
    if not mix_wav:
        return _blocked("_stage_mastering", "no mix")
    iterations = (recipe.get("quality_profile") or {}).get("mastering_iterations")
    return _timed(
        "_stage_mastering",
        lambda: _stage_callable("_stage_mastering")(
            mix_wav,
            out_root,
            stands=recipe["stands"] or None,
            iterations=iterations,
        ),
    )


def _run_arrangement_stage(
    recipe: dict[str, Any],
    analysis: Any,
    style_vector: dict[str, Any],
    reused_stages: dict[str, StageResult],
    only: Any,
) -> StageResult:
    """Аранжировка: переиспользование → план по стилевому вектору → блокировка."""
    if "_stage_arrangement" in reused_stages:
        return reused_stages["_stage_arrangement"]
    if not _wanted(only, "arrangement"):
        return _blocked("_stage_arrangement", "skipped by --only")

    from app.core.stages.prep import DEFAULT_ARRANGEMENT_SEC

    return _timed(
        "_stage_arrangement",
        lambda: _stage_callable("_stage_arrangement")(
            analysis,
            style=style_vector,
            total_seconds=recipe.get("duration_sec") or DEFAULT_ARRANGEMENT_SEC,
            variant=recipe.get("variant") or 0,
            genre=recipe.get("genre"),
        ),
    )
