# -*- coding: utf-8 -*-
"""
app/core/orchestrator.py — единый пайплайн трека (фасад).

Порядок стадий зафиксирован здесь и только здесь:

    анализ → грув → аранжировка → бит → текстура → текст
    → вокал (свой микрофон / TTS / RVC) → вокальные эффекты
    → микс + сайдчейн → мастеринг по стендам → anti-neuro полировка
    → стемы → hit-score → релиз-пакет

Реализации стадий живут в `app/core/stages/*` по одной ответственности на
модуль; входные данные пользователя нормализуются в `app/core/recipe.py`;
единый формат результата стадии — `app.pipeline.StageResult` со статусом
`OK / FALLBACK / BLOCKED / FAILED`.

"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable

from app.core import pipeline_blocks as blocks
from app.core.pipeline_blocks import (  # noqa: F401 - реэкспорт для тестов и подмены
    _add_stage,
    _run_post_master_stages,
    _run_release_stage,
)
# Реэкспорт ради тестов и экспериментов: `pipeline_runtime._stage_callable`
# ищет реализацию стадии в атрибутах этого модуля, поэтому подмена
# `orchestrator._stage_*` остаётся рабочей.
from app.core.pipeline_runtime import (  # noqa: F401
    STAGE_KEYS,
    STAGE_RECORDS,
    _apply_seed,
    _output,
    _quality_gate_failures,
    _run_arrangement_stage,
    _run_mastering_stage,
    _run_texture_stage,
    _wanted,
)
from app.core.recipe import build_arrangement_plan, build_recipe
from app.core.revision import add_mix_integrity
from app.core.stages.beat import _stage_ai_beat, _stage_beat  # noqa: F401
from app.core.stages.lyrics import _run_lyrics_stage  # noqa: F401
from app.core.stages.master import (  # noqa: F401
    _stage_hit_score,
    _stage_mastering,
    _stage_polish,
    _stage_stems,
)
from app.core.stages.mix import _stage_mix_and_sidechain  # noqa: F401
from app.core.stages.prep import (  # noqa: F401
    _stage_analyze,
    _stage_arrangement,
    _stage_groove,
)
from app.core.stages.release import _stage_release_pack  # noqa: F401
from app.core.stages.texture import _stage_texture  # noqa: F401
from app.core.stages.vocal_chain import _run_vocal_chain  # noqa: F401
from app.pipeline import StageResult, summarize

ROOT = Path(__file__).resolve().parents[2]


def _prepare_run(
    project_id: str,
    wizard_state: dict[str, Any],
    only: set[str] | None,
    resumed: bool,
    reused_stages: dict[str, Any],
    out_root: Path | None,
) -> tuple[dict[str, Any], Path, Any, Any]:
    """Рецепт, каталог прогона и захват входов — до первой стадии."""
    if resumed:
        raise ValueError(
            "resume is disabled: previous artifacts were not verified; "
            "use a new full render or verified master revision"
        )
    out_root = out_root or (ROOT / "output" / "audit_v17" / project_id)
    out_root.mkdir(parents=True, exist_ok=True)

    unknown = sorted(set(only or ()) - set(STAGE_KEYS))
    if unknown:
        raise ValueError(
            "unknown stage keys for --only: " + ", ".join(unknown)
            + "; valid: " + ", ".join(STAGE_KEYS)
        )

    recipe = build_recipe({**wizard_state, "project_id": project_id})
    if only is None and isinstance(recipe.get("only"), (list, tuple, set)):
        only = set(recipe["only"])
    from app.core.input_integrity import begin_input_capture

    capture = begin_input_capture(wizard_state, not recipe.get("dry_run") and not only and not reused_stages)
    _apply_seed(recipe.get("seed"))
    return recipe, out_root, only, capture


def _write_report(report: dict[str, Any], out_root: Path, warnings: list[str]) -> None:
    """report.json пишется всегда: без него прогон нечем проверить."""
    try:
        (out_root / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
    except Exception as exc:  # noqa: BLE001 - отчёт не должен ронять рендер
        warnings.append(f"report.json not written: {exc}")


def run_full_pipeline(
    project_id: str,
    wizard_state: dict[str, Any],
    dry_run: bool = False,
    out_root: Path | None = None,
    only: set[str] | None = None,
    resume: bool = False,
    on_stage: Callable[[str, str, int, int], None] | None = None,
    reused_stages: dict[str, Any] | None = None,
    rebuild_info: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Полный прогон от рецепта до релиз-пакета.

    ``only``   — подмножество `STAGE_KEYS`; невыбранные стадии получают статус
                 BLOCKED с причиной «skipped by --only», а не тихо исчезают.
    ``resume`` — временно отключён: прежняя проверка только по имени файла небезопасно.
    ``seed``   — из `wizard_state`; при заданном seed прогон воспроизводим.
    ``on_stage`` — колбэк `(name, status, index, total)` после каждой стадии:
                 по нему GUI показывает реальный прогресс, а не «0.1 → 0.92».

    Сама функция — склейка: каждый блок живёт в `app/core/pipeline_blocks.py`.
    """
    started_at = time.time()
    reused_stages = reused_stages or {}
    recipe, out_root, only, input_capture = _prepare_run(
        project_id, wizard_state, only, resume, reused_stages, out_root
    )
    if dry_run:
        recipe["dry_run"] = True

    stages: list[StageResult] = []
    warnings: list[str] = []
    prior = (
        _output(reused_stages["_stage_mix_and_sidechain"])
        if reused_stages.get("_stage_mix_and_sidechain")
        else {}
    )
    warnings.extend(f"prior run: {w}" for w in prior.get("reused_source_warnings", []))
    if not _wanted(only, "vocal"):
        warnings.append("vocal stages skipped by --only")

    def add(*new_stages: StageResult) -> None:
        blocks._add_stage(stages, on_stage, warnings, *new_stages)

    analysis_stage, groove_stage, groove, style_vector = blocks._run_input_stages(
        recipe, reused_stages, only, dry_run
    )
    add(analysis_stage, groove_stage)
    analysis = _output(analysis_stage).get("analysis")

    arrangement_stage = _run_arrangement_stage(recipe, analysis, style_vector, reused_stages, only)
    add(arrangement_stage)
    plan = build_arrangement_plan(recipe, _output(arrangement_stage).get("plan"), analysis)

    beat_stage = blocks._run_beat_stage(
        recipe, plan, out_root, groove, style_vector, reused_stages, only, dry_run
    )
    add(beat_stage)
    # Earlier audio paths in reused stage records are historical metadata only.
    beat_wav = None if reused_stages else _output(beat_stage).get("path")

    add(_run_texture_stage(recipe, out_root, reused_stages, only))
    add(blocks._run_lyrics_text_stage(recipe, style_vector, reused_stages, only, dry_run))
    lyrics_stage = stages[-1]
    lyrics_dict = _output(lyrics_stage).get("lyrics") or {}
    lyrics_text = _output(lyrics_stage).get("text") or ""

    vocal_stages, vocal_final, vocal_warnings = blocks._run_vocal_stages(
        recipe, lyrics_text, beat_stage, analysis, out_root, reused_stages, only
    )
    warnings.extend(vocal_warnings)
    add(*vocal_stages)

    mix_stage = blocks._run_mix_stage(
        recipe, beat_stage, beat_wav, vocal_final, out_root, reused_stages, only, warnings
    )
    add(mix_stage)
    initial_integrity: dict[str, Any] = {}
    add_mix_integrity(initial_integrity, mix_stage, out_root, warnings)
    mix_wav = _output(mix_stage).get("out_wav")

    master_stage = _run_mastering_stage(recipe, mix_wav, out_root, only)
    add(master_stage)
    master_out = _output(master_stage)
    stand_map = master_out.get("masters") or master_out.get("stands") or {}
    streaming_raw = stand_map.get("streaming") if isinstance(stand_map, dict) else None
    streaming_master = (
        streaming_raw.get("out_wav") if isinstance(streaming_raw, dict) else streaming_raw
    )

    add(*blocks._run_post_master_stages(streaming_master, recipe, out_root, only))

    hit_stage = stages[-1]
    meta = {
        "title": lyrics_dict.get("title", "ZS Track"),
        "artist": recipe["artist"],
        "genre": recipe["genre"],
        "theme": recipe["theme"],
        "bpm": style_vector.get("target_bpm"),
        "hit_score": _output(hit_stage).get("hit_score") if hit_stage.ok else None,
        "verdict": _output(hit_stage).get("verdict") if hit_stage.ok else None,
        "lyrics_text": lyrics_text,
    }

    release_stage = blocks._run_release_stage(
        streaming_master, meta, out_root, stages, lyrics_text, hit_stage, stand_map, only
    )
    add(release_stage)
    warnings.extend(f"release: {w}" for w in _output(release_stage).get("warnings", []))

    summary = summarize(stages, dry_run=dry_run)
    warnings.extend(summary.pop("warnings", []))
    quality_failures = [] if dry_run else _quality_gate_failures(stages)
    if quality_failures:
        warnings.append("Quality gates failed: " + "; ".join(quality_failures))
        if summary["verdict"].startswith("PASS"):
            summary["verdict"] = "PARTIAL"
    finished_at = time.time()

    report = _build_report(
        project_id=project_id,
        recipe=recipe,
        stages=stages,
        summary=summary,
        warnings=warnings,
        quality_failures=quality_failures,
        streaming_master=streaming_master,
        started_at=started_at,
        finished_at=finished_at,
        dry_run=dry_run,
        only=only,
        resume=resume,
        rebuild_info=rebuild_info,
        out_root=out_root,
        wizard_state=wizard_state,
        input_capture=input_capture,
        mix_stage=mix_stage,
        initial_integrity=initial_integrity,
    )
    _write_report(report, out_root, warnings)
    return report


def _build_report(
    *,
    project_id: str,
    recipe: dict[str, Any],
    stages: list[StageResult],
    summary: dict[str, Any],
    warnings: list[str],
    quality_failures: list[str],
    streaming_master: Any,
    started_at: float,
    finished_at: float,
    dry_run: bool,
    only: set[str] | None,
    resume: bool,
    rebuild_info: dict[str, Any] | None,
    out_root: Path,
    wizard_state: dict[str, Any],
    input_capture: Any,
    mix_stage: StageResult,
    initial_integrity: dict[str, Any],
) -> dict[str, Any]:
    """Отчёт прогона: вердикт, стадии, предупреждения, снимок рецепта."""
    report: dict[str, Any] = {
        "project_id": project_id,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_sec": round(finished_at - started_at, 3),
        "dry_run": dry_run,
        "seed": recipe.get("seed"),
        "only": sorted(only) if only else None,
        "resume": bool(resume),
        "verdict": summary["verdict"],
        "stages": [stage.to_dict() for stage in stages],
        "percent": summary["percent"],
        "warnings": warnings,
        "quality_gate_failures": quality_failures,
        "master_path": str(streaming_master) if streaming_master else None,
        "status_summary": {
            "blocked": summary["blocked_stages"],
            "fallback": summary["fallback_stages"],
            "failed": summary["failed_stages"],
        },
        "recipe": {
            "genre": recipe["genre"],
            "voice_mode": recipe["voice_mode"],
            "quality_mode": recipe["quality_mode"],
            "n_verses": recipe["n_verses"],
            "stands": recipe["stands"],
        },
    }
    from app.core.input_integrity import finish_input_capture
    from app.core.project_snapshot import snapshot_recipe

    if rebuild_info is not None:
        report["rebuild"] = rebuild_info
    report["project_root"] = str(out_root.resolve())
    try:
        report["desktop_recipe_snapshot"] = snapshot_recipe(wizard_state)
    except ValueError as exc:
        warnings.append(f"project recipe not saved; reopening unavailable: {exc}")
    finish_input_capture(report, wizard_state, input_capture, warnings)
    add_mix_integrity(report, mix_stage, out_root, warnings)
    if initial_integrity.get("artifact_integrity") != report.get("artifact_integrity"):
        report.pop("artifact_integrity", None)
        warnings.append("mix changed during render; master revision is unavailable")
    return report


def build_gradio_ui():
    """Fallback-UI на Gradio (PySide6-визард — основной интерфейс)."""
    try:
        import gradio as gr
    except Exception:  # noqa: BLE001 - UI опционален
        return None

    def _run(refs_str, theme, genre):
        refs = [r.strip() for r in (refs_str or "").split(",") if r.strip()]
        result = run_full_pipeline(
            "gradio_" + str(int(time.time())),
            {"references": refs, "theme": theme, "genre": genre},
            dry_run=False,
        )
        return json.dumps(result, ensure_ascii=False, indent=2, default=str)

    with gr.Blocks(title="ZS Music Maker (fallback UI)") as demo:
        gr.Markdown("# ZS Music Maker — fallback UI (Gradio)")
        refs = gr.Textbox(label="Референсы (пути через запятую)")
        theme = gr.Textbox(value="лето, тачки, движ", label="Тема")
        genre = gr.Textbox(value="drift_phonk", label="Жанр")
        btn = gr.Button("Запустить полный пайплайн")
        out = gr.Textbox(lines=30, label="Результат")
        btn.click(_run, [refs, theme, genre], out)
    return demo
