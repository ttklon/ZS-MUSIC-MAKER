# -*- coding: utf-8 -*-
"""
app/core/pipeline_blocks.py — именованные блоки пайплайна.

`orchestrator.run_full_pipeline` был одной функцией на 315 строк: правка в
середине требовала держать в голове весь контекст, а прочитать её целиком
было нельзя. Здесь те же шаги, разложенные по блокам — входные стадии, бит,
текст, вокал, микс, пост-мастеринг, релиз — и оркестратор вызывает их по
порядку. Ни одна предметная стадия здесь не реализована: только правила
вызова, уже описанные в `app/core/pipeline_runtime.py`.

Значения по умолчанию и статусы сохранены побайтно: блок обязан вести себя
так же, как прежний линейный код (это проверяют контрактные тесты стадий).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.pipeline import StageResult

from app.core.pipeline_runtime import (
    MASTER_STANDS,
    STAGE_RECORDS,
    STEM_NAMES,
    _blocked,
    _normalize_path_map,
    _output,
    _stage_callable,
    _timed,
    _wanted,
)


# --------------------------------------------------------------------------- #
#  Блоки пайплайна: каждая группа стадий — один именованный шаг
# --------------------------------------------------------------------------- #
# Раньше `run_full_pipeline` был одной функцией на 315 строк: прочитать её
# целиком было нельзя, а правка в середине требовала держать в голове весь
# контекст. Здесь те же шаги, но по блокам; оркестратор вызывает их по порядку.

def _add_stage(
    stages: list[StageResult],
    on_stage: Callable[[str, str, int, int], None] | None,
    warnings: list[str],
    *new_stages: StageResult,
) -> None:
    """Добавить стадии и сразу отдать прогресс наружу (GUI/CLI)."""
    total = len(STAGE_RECORDS)
    for stage in new_stages:
        stages.append(stage)
        if on_stage is None:
            continue
        try:
            status = f"{stage.status.value} (reused)" if _output(stage).get("reused") else stage.status.value
            on_stage(stage.name, status, len(stages), total)
        except Exception as error:  # noqa: BLE001 - колбэк не должен ломать прогон
            warnings.append(f"progress callback failed: {type(error).__name__}: {error}")


def _call_stage(name: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
    """Вызов реализации стадии через фасад оркестратора (см. `_stage_callable`)."""
    return _stage_callable(name)(*args, **kwargs)


def _run_input_stages(
    recipe: dict[str, Any],
    reused_stages: dict[str, StageResult],
    only: Any,
    dry_run: bool,
) -> tuple[StageResult, StageResult, dict[str, Any], dict[str, Any]]:
    """Анализ, грув и стилевой вектор — вход для аранжировки."""
    if "_stage_analyze" in reused_stages:
        analysis_stage = reused_stages["_stage_analyze"]
    elif _wanted(only, "analysis"):
        analysis_stage = _timed(
            "_stage_analyze",
            lambda: _call_stage("_stage_analyze", recipe["refs"], dry_run, recipe["genre"]),
        )
    else:
        analysis_stage = _blocked("_stage_analyze", "skipped by --only")
    analysis = _output(analysis_stage).get("analysis")

    if "_stage_groove" in reused_stages:
        groove_stage = reused_stages["_stage_groove"]
    elif _wanted(only, "groove"):
        groove_stage = _timed(
            "_stage_groove",
            lambda: _call_stage("_stage_groove", recipe["refs"], recipe["genre"]),
        )
    else:
        groove_stage = _blocked("_stage_groove", "skipped by --only")
    groove = _output(groove_stage).get("groove")

    # Стилевой вектор нужен аранжировке как вход, а не как побочный результат:
    # раньше стадия получала только анализ и отдавала пустой план.
    from app.core.recipe import resolve_style_vector

    style_vector = resolve_style_vector(recipe, analysis)
    return analysis_stage, groove_stage, groove, style_vector


def _run_beat_stage(
    recipe: dict[str, Any],
    plan: dict[str, Any],
    out_root: Path,
    groove: Any,
    style_vector: dict[str, Any],
    reused_stages: dict[str, StageResult],
    only: Any,
    dry_run: bool,
) -> StageResult:
    """Бит: procedural DSP или AI-движок — по рецепту, а не по наличию файла."""
    if "_stage_beat" in reused_stages:
        return reused_stages["_stage_beat"]
    if not _wanted(only, "beat"):
        return _blocked("_stage_beat", "skipped by --only")
    procedural = recipe["beat_engine"] == "procedural" and not recipe.get("recorded_backing_sha256")
    return _timed(
        "_stage_beat",
        lambda: _call_stage("_stage_beat", plan, out_root, groove=groove, style_vector=style_vector)
        if procedural
        else _stage_callable("_stage_ai_beat")(recipe, plan, out_root, style_vector, dry_run),
    )


def _run_lyrics_text_stage(
    recipe: dict[str, Any],
    style_vector: dict[str, Any],
    reused_stages: dict[str, StageResult],
    only: Any,
    dry_run: bool,
) -> StageResult:
    """Текст: переиспользование → запуск → блокировка по `--only`."""
    if "_stage_lyrics" in reused_stages:
        return reused_stages["_stage_lyrics"]
    if not _wanted(only, "lyrics"):
        return _blocked("_stage_lyrics", "skipped by --only")
    stage, _lyrics, _text = _stage_callable("_run_lyrics_stage")(
        {**recipe, "style_vector": style_vector, "dry_run": dry_run}
    )
    return stage


def _run_vocal_stages(
    recipe: dict[str, Any],
    lyrics_text: str,
    beat_stage: StageResult,
    analysis: Any,
    out_root: Path,
    reused_stages: dict[str, StageResult],
    only: Any,
) -> tuple[list[StageResult], str | None, list[str]]:
    """Вокальная ветка: синтез → RVC → эффекты, с честной блокировкой."""
    names = ("_stage_voice_synth", "_stage_rvc", "_stage_vocal_fx")
    if "_stage_voice_synth" in reused_stages:
        # Соответствующий микс уже заморожен и переиспользуется.
        return [reused_stages[name] for name in names], None, []
    if not _wanted(only, "vocal"):
        return [_blocked(name, "skipped by --only") for name in names], None, []
    beat_output = _output(beat_stage)
    stages, vocal_final, warnings = _stage_callable("_run_vocal_chain")(
        recipe,
        lyrics_text,
        out_root,
        bpm=beat_output.get("bpm") or (analysis.get("bpm") if isinstance(analysis, dict) else None),
        key=beat_output.get("key"),
    )
    return stages, vocal_final, warnings


def _run_mix_stage(
    recipe: dict[str, Any],
    beat_stage: StageResult,
    beat_wav: str | None,
    vocal_final: str | None,
    out_root: Path,
    reused_stages: dict[str, StageResult],
    only: Any,
    warnings: list[str],
) -> StageResult:
    """Микс: без бита или без запрошенного вокала микс не выдумывается."""
    if "_stage_mix_and_sidechain" in reused_stages:
        return reused_stages["_stage_mix_and_sidechain"]
    if not _wanted(only, "mix"):
        return _blocked("_stage_mix_and_sidechain", "skipped by --only")
    if recipe.get("own_vocal_wav") and recipe["voice_mode"] != "off" and not vocal_final:
        warnings.append("requested recording unavailable; mix not rendered")
        return _blocked(
            "_stage_mix_and_sidechain",
            "requested recording unavailable; refusing instrumental substitution",
        )
    if not beat_wav:
        return _blocked("_stage_mix_and_sidechain", "no beat")
    return _timed(
        "_stage_mix_and_sidechain",
        lambda: _stage_callable("_stage_mix_and_sidechain")(
            beat_wav,
            vocal_final,
            out_root,
            recipe.get("refs") or None,
            vocal_offset_ms=recipe.get("vocal_offset_ms", 0),
        ),
    )


def _run_post_master_stages(
    streaming_master: Any,
    recipe: dict[str, Any],
    out_root: Path,
    only: Any,
) -> list[StageResult]:
    """Полировка, стемы и hit-score после мастеринга."""
    from app.core.stages.master import _stage_hit_score, _stage_polish, _stage_stems

    export_stems = recipe.get("export_stems", True)
    produced: list[StageResult] = []
    for key, name, fn in (
        ("polish", "_stage_polish", lambda: _stage_polish(streaming_master, out_root)),
        ("stems", "_stage_stems", lambda: _stage_stems(streaming_master, out_root)),
        ("hit_score", "_stage_hit_score", lambda: _stage_hit_score(streaming_master)),
    ):
        if not streaming_master:
            produced.append(_blocked(name, "no master"))
        elif not _wanted(only, key):
            produced.append(_blocked(name, "skipped by --only"))
        elif key == "stems" and not export_stems:
            # пользователь снял галочку — стадия помечается, а не исчезает молча
            produced.append(_blocked(name, "stems disabled by user (export_stems=false)"))
        else:
            produced.append(_timed(name, fn))
    return produced


def _run_release_stage(
    streaming_master: Any,
    meta: dict[str, Any],
    out_root: Path,
    stages: list[StageResult],
    lyrics_text: str,
    hit_stage: StageResult,
    stand_map: Any,
    only: Any,
) -> StageResult:
    """Релиз-пакет: собирается только при реальном мастере."""
    if not streaming_master:
        return _blocked("_stage_release_pack", "no master")
    if not _wanted(only, "release"):
        return _blocked("_stage_release_pack", "skipped by --only")
    masters_map = _normalize_path_map(stand_map, list(MASTER_STANDS))
    stems_stage = next((stage for stage in stages if stage.name == "_stage_stems"), None)
    stems_map = (
        _normalize_path_map(_output(stems_stage).get("stems") or {}, list(STEM_NAMES))
        if stems_stage is not None and stems_stage.ok
        else {}
    )
    hit_metrics = {
        key: value for key, value in _output(hit_stage).items() if key not in ("ok", "reason")
    }
    return _timed(
        "_stage_release_pack",
        lambda: _stage_callable("_stage_release_pack")(
            streaming_master,
            meta,
            out_root,
            masters_map=masters_map,
            stems_map=stems_map,
            lyrics_text=lyrics_text,
            stages=[stage.to_dict() for stage in stages],
            hit_metrics=hit_metrics,
        ),
    )
