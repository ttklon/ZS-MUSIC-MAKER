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
from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.core.recipe import build_arrangement_plan, build_recipe, resolve_style_vector
from app.core.stages.beat import _stage_beat
from app.core.stages.lyrics import _stage_lyrics, _struct_to_text, _text_to_struct
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
from app.core.stages.vocal import _stage_rvc, _stage_vocal_fx, _stage_voice_synth
from app.pipeline import StageResult, StageStatus, classify, summarize

ROOT = Path(__file__).resolve().parents[2]

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
    return classify(output, failed=failed, reason=reason, duration_sec=time.time() - started, name=name)


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


def _run_vocal_chain(
    recipe: dict[str, Any],
    lyrics_text: str,
    out_root: Path,
) -> tuple[list[StageResult], str | None, list[str]]:
    """Вокальная ветка: запись пользователя → TTS → RVC → эффекты.

    Инструментальный режим (`voice_mode=off`) честно помечает все вокальные
    стадии BLOCKED. Синтетический скаффолд без RVC в мастер не попадает —
    это пластмасса, которая убивает «живость» трека.
    """
    warnings: list[str] = []
    if recipe["voice_mode"] == "off":
        reason = "voice_mode='off' (instrumental) — vocal pipeline skipped by user choice"
        stages = [
            _blocked("_stage_voice_synth", reason),
            _blocked("_stage_rvc", "voice_mode='off' (instrumental)"),
            _blocked("_stage_vocal_fx", "voice_mode='off' (instrumental)"),
        ]
        return stages, None, warnings

    own_vocal = recipe.get("own_vocal_wav")
    if own_vocal and Path(str(own_vocal)).exists():
        synth = StageResult(
            name="_stage_voice_synth",
            status=StageStatus.OK,
            output={
                "ok": True,
                "path": str(own_vocal),
                "engine": "user_recording",
                "reason": "own microphone recording used as primary vocal path",
            },
        )
    else:
        synth = _timed("_stage_voice_synth", lambda: _stage_voice_synth(lyrics_text, out_root))
    stages = [synth]

    voice_wav = _output(synth).get("path")
    synthetic = bool(_output(synth).get("synthetic"))

    if voice_wav:
        rvc = _timed(
            "_stage_rvc",
            lambda: _stage_rvc(voice_wav, out_root, upstream_synthetic=synthetic),
        )
    else:
        rvc = _blocked("_stage_rvc", "no voice_wav upstream (voice_synth failed)")
    stages.append(rvc)

    rvc_path = _output(rvc).get("path") if rvc.ok else None
    vocal_final = rvc_path or voice_wav

    if vocal_final:
        fx = _timed("_stage_vocal_fx", lambda: _stage_vocal_fx(vocal_final, out_root))
    else:
        fx = _blocked("_stage_vocal_fx", "no vocal")
    stages.append(fx)
    if fx.ok:
        vocal_final = _output(fx).get("path") or _output(fx).get("out_wav") or vocal_final

    if synthetic and not rvc_path:
        warnings.append(
            "vocal skipped: synthetic scaffold not mixed "
            "(instrumental master; record voice or install TTS)"
        )
        vocal_final = None
    return stages, vocal_final, warnings


def _run_lyrics_stage(recipe: dict[str, Any]) -> tuple[StageResult, dict[str, Any], str]:
    """Текст: свои строки пользователя приоритетнее любой генерации."""
    user_lines = recipe["user_lyrics_lines"]
    if user_lines:
        own_text = "\n".join(user_lines)
        struct = _text_to_struct(own_text, recipe["genre"])
        return (
            StageResult(
                name="_stage_lyrics",
                status=StageStatus.OK,
                output={
                    "ok": True,
                    "text": own_text,
                    "lyrics": struct,
                    "provider": "user_lyrics",
                    "reason": "user-provided lyrics from wizard",
                },
            ),
            struct,
            own_text,
        )
    stage = _timed("_stage_lyrics", lambda: _stage_lyrics(recipe["theme"], recipe["genre"]))
    out = _output(stage)
    struct = out.get("lyrics") or {}
    text = out.get("text") or _struct_to_text(struct)
    return stage, struct, text


def run_full_pipeline(
    project_id: str,
    wizard_state: dict[str, Any],
    dry_run: bool = False,
    out_root: Path | None = None,
) -> dict[str, Any]:
    """Полный прогон от рецепта до релиз-пакета."""
    started_at = time.time()
    out_root = out_root or (ROOT / "output" / "audit_v17" / project_id)
    out_root.mkdir(parents=True, exist_ok=True)

    recipe = build_recipe({**wizard_state, "project_id": project_id})
    stages: list[StageResult] = []
    warnings: list[str] = []

    analysis_stage = _timed(
        "_stage_analyze",
        lambda: _stage_analyze(recipe["refs"], dry_run, recipe["genre"]),
    )
    stages.append(analysis_stage)
    analysis = _output(analysis_stage).get("analysis")

    groove_stage = _timed(
        "_stage_groove",
        lambda: _stage_groove(recipe["refs"], recipe["genre"]),
    )
    stages.append(groove_stage)
    groove = _output(groove_stage).get("groove")

    arrangement_stage = _timed("_stage_arrangement", lambda: _stage_arrangement(analysis))
    stages.append(arrangement_stage)

    style_vector = resolve_style_vector(recipe, analysis)
    plan = build_arrangement_plan(recipe, _output(arrangement_stage).get("plan"), analysis)

    beat_stage = _timed(
        "_stage_beat",
        lambda: _stage_beat(plan, out_root, groove=groove, style_vector=style_vector),
    )
    stages.append(beat_stage)
    beat_wav = _output(beat_stage).get("path")

    stages.append(
        _timed(
            "_stage_texture",
            lambda: _stage_texture(f"{recipe['genre']} atmosphere with {recipe['theme']}", out_root),
        )
    )

    lyrics_stage, lyrics_dict, lyrics_text = _run_lyrics_stage(recipe)
    stages.append(lyrics_stage)

    vocal_stages, vocal_final, vocal_warnings = _run_vocal_chain(recipe, lyrics_text, out_root)
    stages.extend(vocal_stages)
    warnings.extend(vocal_warnings)

    if beat_wav:
        mix_stage = _timed(
            "_stage_mix_and_sidechain",
            lambda: _stage_mix_and_sidechain(beat_wav, vocal_final, out_root),
        )
    else:
        mix_stage = _blocked("_stage_mix_and_sidechain", "no beat")
    stages.append(mix_stage)
    mix_wav = _output(mix_stage).get("out_wav")

    if mix_wav:
        master_stage = _timed(
            "_stage_mastering",
            lambda: _stage_mastering(mix_wav, out_root, stands=recipe["stands"] or None),
        )
    else:
        master_stage = _blocked("_stage_mastering", "no mix")
    stages.append(master_stage)

    master_out = _output(master_stage)
    stand_map = master_out.get("masters") or master_out.get("stands") or {}
    streaming_raw = stand_map.get("streaming") if isinstance(stand_map, dict) else None
    streaming_master = (
        streaming_raw.get("out_wav") if isinstance(streaming_raw, dict) else streaming_raw
    )

    if streaming_master:
        stages.append(_timed("_stage_polish", lambda: _stage_polish(streaming_master, out_root)))
        stages.append(_timed("_stage_stems", lambda: _stage_stems(streaming_master, out_root)))
        stages.append(_timed("_stage_hit_score", lambda: _stage_hit_score(streaming_master)))
    else:
        stages.append(_blocked("_stage_polish", "no master"))
        stages.append(_blocked("_stage_stems", "no master"))
        stages.append(_blocked("_stage_hit_score", "no master"))

    hit_stage = stages[-1]
    meta = {
        "title": lyrics_dict.get("title", "ZS Track"),
        "artist": recipe["artist"],
        "genre": recipe["genre"],
        "theme": recipe["theme"],
        "bpm": analysis.get("bpm") if isinstance(analysis, dict) else None,
        "hit_score": _output(hit_stage).get("hit_score") if hit_stage.ok else None,
        "verdict": _output(hit_stage).get("verdict") if hit_stage.ok else None,
        "lyrics_text": lyrics_text,
    }

    if streaming_master:
        masters_map = _normalize_path_map(stand_map, list(MASTER_STANDS))
        stems_map = _normalize_path_map(
            _output(stages[-2]).get("stems") or _output(stages[-2]), list(STEM_NAMES)
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
    else:
        release_stage = _blocked("_stage_release_pack", "no master")
    stages.append(release_stage)

    summary = summarize(stages, dry_run=dry_run)
    warnings.extend(summary.pop("warnings", []))
    finished_at = time.time()

    return {
        "project_id": project_id,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_sec": round(finished_at - started_at, 3),
        "dry_run": dry_run,
        "verdict": summary["verdict"],
        "stages": [stage.to_dict() for stage in stages],
        "percent": summary["percent"],
        "warnings": warnings,
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
