# -*- coding: utf-8 -*-
"""app/core/report_finalize.py — сборка отчёта прогона и запись артефактов.

Вынесено из `orchestrator`: функция собиралась из двух частей — «словарь
отчёта» и «всё, что нужно проверить после рендера» (снимок рецепта, хеши
микса и финального мастера). Отдельный модуль даёт этому шагу имя и не
раздувает оркестратор.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.input_integrity import finish_input_capture
from app.core.project_snapshot import snapshot_recipe
from app.core.revision import add_master_integrity, add_mix_integrity


def _stage_warnings(stages: list[Any]) -> list[str]:
    """Предупреждения из результатов стадий — в общий список отчёта.

    Стадия может честно сказать «здесь я не измерила, а оценила»
    (`output["warnings"]`). Пока эти строки не поднимались наверх, отчёт о них
    молчал: балл за громкость выглядел измеренным, хотя был оценкой.
    """
    collected: list[str] = []
    for stage in stages:
        output = getattr(stage, "output", None) or {}
        if not isinstance(output, dict):
            continue
        for item in output.get("warnings") or []:
            text = str(item).strip()
            if text and text not in collected:
                collected.append(text)
    return collected


def finalize_report(
    *,
    project_id: str,
    recipe: dict[str, Any],
    stages: list[Any],
    summary: dict[str, Any],
    warnings: list[str],
    quality_failures: list[str],
    streaming_master: Any,
    started_at: float,
    finished_at: float,
    dry_run: bool,
    only: Any,
    resume: bool,
    rebuild_info: dict[str, Any] | None,
    out_root: Path,
    wizard_state: dict[str, Any],
    input_capture: Any,
    mix_stage: Any,
    initial_integrity: dict[str, Any],
) -> dict[str, Any]:
    """Отчёт прогона: вердикт, стадии, предупреждения, снимок рецепта."""
    # Причина, по которой заданный референс не применился, обязана быть видна в
    # отчёте: иначе всё выглядит так, будто референсов не было вовсе
    # (`source=genre_default`, `n_refs=0`, ноль предупреждений).
    warnings.extend(str(w) for w in recipe.get("ref_warnings") or [])
    # Предупреждения самих стадий (например, «громкость не измерена, балл —
    # RMS-оценка») раньше оставались внутри `output` и до отчёта не доходили.
    warnings.extend(_stage_warnings(stages))
    report = _report_skeleton(
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
    )
    _verify_after_render(
        report=report,
        wizard_state=wizard_state,
        input_capture=input_capture,
        mix_stage=mix_stage,
        out_root=out_root,
        streaming_master=streaming_master,
        warnings=warnings,
        initial_integrity=initial_integrity,
    )
    if rebuild_info is not None:
        report["rebuild"] = rebuild_info
    from app.pipeline.outcome import report_outcome
    report["outcome"] = report_outcome(stages, quality_failures=quality_failures, dry_run=dry_run, only=only)
    return report


def _report_skeleton(
    *,
    project_id: str,
    recipe: dict[str, Any],
    stages: list[Any],
    summary: dict[str, Any],
    warnings: list[str],
    quality_failures: list[str],
    streaming_master: Any,
    started_at: float,
    finished_at: float,
    dry_run: bool,
    only: Any,
    resume: bool,
) -> dict[str, Any]:
    """Словарь отчёта: всё, что известно до проверок целостности."""
    return {
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


def _verify_after_render(
    *,
    report: dict[str, Any],
    wizard_state: dict[str, Any],
    input_capture: Any,
    mix_stage: Any,
    out_root: Path,
    streaming_master: Any,
    warnings: list[str],
    initial_integrity: dict[str, Any],
) -> None:
    """Проверки после рендера: снимок рецепта, хеши микса и мастера."""
    report["project_root"] = str(out_root.resolve())
    try:
        report["desktop_recipe_snapshot"] = snapshot_recipe(wizard_state)
    except ValueError as exc:
        warnings.append(f"project recipe not saved; reopening unavailable: {exc}")
    finish_input_capture(report, wizard_state, input_capture, warnings)
    add_mix_integrity(report, mix_stage, out_root, warnings)
    add_master_integrity(report, streaming_master, out_root, warnings)
    # Сравниваем только микс: у мастера своя запись (`master`), и она по
    # определению появляется позже — иначе проверка всегда «находила» подмену
    # и стирала весь манифест целостности.
    initial_mix = (initial_integrity.get("artifact_integrity") or {}).get("mix")
    current_mix = (report.get("artifact_integrity") or {}).get("mix")
    if initial_mix != current_mix:
        report.pop("artifact_integrity", None)
        warnings.append("mix changed during render; master revision is unavailable")
