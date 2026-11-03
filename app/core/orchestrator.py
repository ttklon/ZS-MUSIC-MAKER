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

Здесь остаётся только склейка: вызов стадий в правильном порядке, передача
артефактов между ними и итоговая сводка.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable

from app.core.revision import add_mix_integrity
from app.core.pipeline_runtime import (
    STAGE_KEYS,
    STAGE_RECORDS,
    MASTER_STANDS,
    STEM_NAMES,
    _apply_seed,
    _blocked,
    _normalize_path_map,
    _output,
    _quality_gate_failures,
    _timed,
    _wanted,
)
from app.core.recipe import build_arrangement_plan, build_recipe, resolve_style_vector
from app.core.stages.beat import _stage_beat, _stage_ai_beat
from app.core.stages.lyrics import _run_lyrics_stage
from app.core.stages.master import (
    _stage_hit_score,
    _stage_mastering,
    _stage_polish,
    _stage_stems,
)
from app.core.stages.mix import _stage_mix_and_sidechain
from app.core.stages.prep import _stage_analyze, _stage_arrangement, _stage_groove
from app.core.stages.release import _stage_release_pack
from app.core.stages.texture import _stage_texture
from app.core.stages.vocal_chain import _run_vocal_chain
from app.pipeline import summarize

ROOT = Path(__file__).resolve().parents[2]


def run_full_pipeline(
    project_id: str,
    wizard_state: dict[str, Any],
    dry_run: bool = False,
    out_root: Path | None = None,
    only: set[str] | None = None,
    resume: bool = False,
    on_stage: Callable[[str, str, int, int], None] | None = None,
    reused_stages: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Полный прогон от рецепта до релиз-пакета.

    ``only``   — подмножество `STAGE_KEYS`; невыбранные стадии получают статус
                 BLOCKED с причиной «skipped by --only», а не тихо исчезают.
    ``resume`` — временно отключён: прежняя проверка только по имени файла небезопасна.
    ``seed``   — из `wizard_state`; при заданном seed прогон воспроизводим.
    ``on_stage`` — колбэк `(name, status, index, total)` после каждой стадии:
                 по нему GUI показывает реальный прогресс, а не «0.1 → 0.92».
    """
    if resume:
        raise ValueError("resume is disabled: previous artifacts were not verified; use a new full render or verified master revision")
    started_at = time.time()
    reused_stages = reused_stages or {}
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
    _apply_seed(recipe.get("seed"))
    stages: list[StageResult] = []
    warnings: list[str] = []
    prior = _output(reused_stages.get("_stage_mix_and_sidechain")) if reused_stages.get("_stage_mix_and_sidechain") else {}
    warnings.extend(f"prior run: {w}" for w in prior.get("reused_source_warnings", []))
    # Пайплайн всегда добавляет одно и то же число записей: пропущенные стадии
    # попадают в список как BLOCKED, а не исчезают. Поэтому «всего» известно
    # заранее и прогресс в GUI не врёт.
    total_stages = len(STAGE_RECORDS)

    def add(*new_stages: StageResult) -> None:
        """Добавить стадии и сразу отдать прогресс наружу (GUI/CLI)."""
        for stage in new_stages:
            stages.append(stage)
            if on_stage is not None:
                try:
                    status = f"{stage.status.value} (reused)" if _output(stage).get("reused") else stage.status.value
                    on_stage(stage.name, status, len(stages), total_stages)
                except Exception as error:  # noqa: BLE001 - колбэк не должен ломать прогон
                    warnings.append(f"progress callback failed: {type(error).__name__}: {error}")

    if not _wanted(only, "vocal"):
        warnings.append("vocal stages skipped by --only")

    if "_stage_analyze" in reused_stages:
        analysis_stage = reused_stages["_stage_analyze"]
    elif _wanted(only, "analysis"):
        analysis_stage = _timed(
            "_stage_analyze",
            lambda: _stage_analyze(recipe["refs"], dry_run, recipe["genre"]),
        )
    else:
        analysis_stage = _blocked("_stage_analyze", "skipped by --only")
    add(analysis_stage)
    analysis = _output(analysis_stage).get("analysis")

    if "_stage_groove" in reused_stages:
        groove_stage = reused_stages["_stage_groove"]
    elif _wanted(only, "groove"):
        groove_stage = _timed(
            "_stage_groove",
            lambda: _stage_groove(recipe["refs"], recipe["genre"]),
        )
    else:
        groove_stage = _blocked("_stage_groove", "skipped by --only")
    add(groove_stage)
    groove = _output(groove_stage).get("groove")

    if "_stage_arrangement" in reused_stages:
        arrangement_stage = reused_stages["_stage_arrangement"]
    elif _wanted(only, "arrangement"):
        arrangement_stage = _timed("_stage_arrangement", lambda: _stage_arrangement(analysis))
    else:
        arrangement_stage = _blocked("_stage_arrangement", "skipped by --only")
    add(arrangement_stage)

    style_vector = resolve_style_vector(recipe, analysis)
    plan = build_arrangement_plan(recipe, _output(arrangement_stage).get("plan"), analysis)

    if "_stage_beat" in reused_stages:
        beat_stage = reused_stages["_stage_beat"]
    elif _wanted(only, "beat"):
        beat_stage = _timed(
            "_stage_beat",
            lambda: _stage_beat(plan, out_root, groove=groove, style_vector=style_vector) if recipe["beat_engine"] == "procedural" else _stage_ai_beat(recipe, plan, out_root, style_vector, dry_run),
        )
    else:
        beat_stage = _blocked("_stage_beat", "skipped by --only")
    add(beat_stage)
    # Earlier audio paths in reused stage records are historical metadata only.
    beat_wav = None if reused_stages else _output(beat_stage).get("path")

    if "_stage_texture" in reused_stages:
        add(reused_stages["_stage_texture"])
    elif _wanted(only, "texture"):
        add(
            _timed(
                "_stage_texture",
                lambda: _stage_texture(
                    f"{recipe['genre']} atmosphere with {recipe['theme']}", out_root
                ),
            )
        )
    else:
        add(_blocked("_stage_texture", "skipped by --only"))

    if "_stage_lyrics" in reused_stages:
        lyrics_stage = reused_stages["_stage_lyrics"]
        lyrics_dict = _output(lyrics_stage).get("lyrics") or {}
        lyrics_text = _output(lyrics_stage).get("text") or ""
    elif _wanted(only, "lyrics"):
        lyrics_stage, lyrics_dict, lyrics_text = _run_lyrics_stage({**recipe, "style_vector": style_vector})
    else:
        lyrics_stage = _blocked("_stage_lyrics", "skipped by --only")
        lyrics_dict, lyrics_text = {}, ""
    add(lyrics_stage)

    if "_stage_voice_synth" in reused_stages:
        vocal_stages = [reused_stages[name] for name in ("_stage_voice_synth", "_stage_rvc", "_stage_vocal_fx")]
        vocal_final = None  # The corresponding mix is already frozen and reused.
    elif not _wanted(only, "vocal"):
        vocal_stages = [
            _blocked(name, "skipped by --only")
            for name in ("_stage_voice_synth", "_stage_rvc", "_stage_vocal_fx")
        ]
        vocal_final = None
    else:
        beat_output = _output(beat_stage)
        vocal_stages, vocal_final, vocal_warnings = _run_vocal_chain(
            recipe,
            lyrics_text,
            out_root,
            bpm=beat_output.get("bpm")
            or (analysis.get("bpm") if isinstance(analysis, dict) else None),
            key=beat_output.get("key"),
        )
        warnings.extend(vocal_warnings)
    add(*vocal_stages)

    if "_stage_mix_and_sidechain" in reused_stages:
        mix_stage = reused_stages["_stage_mix_and_sidechain"]
    elif not _wanted(only, "mix"):
        mix_stage = _blocked("_stage_mix_and_sidechain", "skipped by --only")
    elif beat_wav:
        mix_stage = _timed(
            "_stage_mix_and_sidechain",
            lambda: _stage_mix_and_sidechain(
                beat_wav, vocal_final, out_root, (recipe.get("refs") or [None])[0],
                vocal_offset_ms=recipe.get("vocal_offset_ms", 0),
            ),
        )
    else:
        mix_stage = _blocked("_stage_mix_and_sidechain", "no beat")
    add(mix_stage)
    initial_integrity: dict[str, Any] = {}
    add_mix_integrity(initial_integrity, mix_stage, out_root, warnings)
    mix_wav = _output(mix_stage).get("out_wav")

    if not _wanted(only, "master"):
        master_stage = _blocked("_stage_mastering", "skipped by --only")
    elif mix_wav:
        master_stage = _timed(
            "_stage_mastering",
            lambda: _stage_mastering(mix_wav, out_root, stands=recipe["stands"] or None),
        )
    else:
        master_stage = _blocked("_stage_mastering", "no mix")
    add(master_stage)

    master_out = _output(master_stage)
    stand_map = master_out.get("masters") or master_out.get("stands") or {}
    streaming_raw = stand_map.get("streaming") if isinstance(stand_map, dict) else None
    streaming_master = (
        streaming_raw.get("out_wav") if isinstance(streaming_raw, dict) else streaming_raw
    )

    export_stems = recipe.get("export_stems", True)
    for key, name, fn in (
        ("polish", "_stage_polish", lambda: _stage_polish(streaming_master, out_root)),
        ("stems", "_stage_stems", lambda: _stage_stems(streaming_master, out_root)),
        ("hit_score", "_stage_hit_score", lambda: _stage_hit_score(streaming_master)),
    ):
        if not streaming_master:
            add(_blocked(name, "no master"))
        elif not _wanted(only, key):
            add(_blocked(name, "skipped by --only"))
        elif key == "stems" and not export_stems:
            # пользователь снял галочку — стадия помечается, а не исчезает молча
            add(_blocked(name, "stems disabled by user (export_stems=false)"))
        else:
            add(_timed(name, fn))

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

    if streaming_master and _wanted(only, "release"):
        masters_map = _normalize_path_map(stand_map, list(MASTER_STANDS))
        stems_stage = next((stage for stage in stages if stage.name == "_stage_stems"), None)
        stems_map = (
            _normalize_path_map(_output(stems_stage).get("stems") or {}, list(STEM_NAMES))
            if stems_stage is not None and stems_stage.ok
            else {}
        )
        hit_metrics = {
            key: value
            for key, value in _output(hit_stage).items()
            if key not in ("ok", "reason")
        }
        release_stage = _timed(
            "_stage_release_pack",
            lambda: _stage_release_pack(
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
    elif not streaming_master:
        release_stage = _blocked("_stage_release_pack", "no master")
    else:
        release_stage = _blocked("_stage_release_pack", "skipped by --only")
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

    report = {
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
    add_mix_integrity(report, mix_stage, out_root, warnings)
    if initial_integrity.get("artifact_integrity") != report.get("artifact_integrity"):
        report.pop("artifact_integrity", None)
        warnings.append("mix changed during render; master revision is unavailable")
    # Отчёт всегда ложится рядом с артефактами: он же — точка возобновления.
    try:
        (out_root / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
    except Exception as exc:  # noqa: BLE001 - отчёт не должен ронять рендер
        warnings.append(f"report.json not written: {exc}")
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
