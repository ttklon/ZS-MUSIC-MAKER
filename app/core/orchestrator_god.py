# -*- coding: utf-8 -*-
"""
app/core/orchestrator_god.py — адаптер «God Mode» над общим DAG.

Раньше здесь жил второй, независимый пайплайн (свой порядок стадий, свой
мастеринг с целью −12 LUFS, свой `beat`-движок). Два пайплайна разъезжались
по качеству: правки в `app/core/stages/*` не доезжали до `--god`, а тесты
мерили то один, то другой. Теперь «God Mode» — это тот же
`run_full_pipeline`, только с длиной по умолчанию 120 с и отчётом в старой
форме (`status/stages/master_path`), чтобы не ломать CLI и smoke-гейты.

Отдельной логики здесь нет и не должно появляться: новая стадия добавляется
в `app/core/orchestrator.py` и автоматически доступна всем входам.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

GOD_DURATION_SEC = 120  # «God Mode» = полноценный трек, а не фрагмент

# Вердикты общего пайплайна → статус в терминах старого отчёта God Mode
_COMPLETED_VERDICTS = {"PASS", "PASS_WITH_FALLBACK", "PASS_BLOCKED", "BLOCKED_SIMULATION"}


def _status_from_verdict(verdict: str | None) -> str:
    return "completed" if (verdict or "") in _COMPLETED_VERDICTS else "partial"


def _vocal_report(stages: list[dict[str, Any]]) -> tuple[str, str | None]:
    """Честный статус вокала из стадий: OK / FALLBACK / BLOCKED / FAILED."""
    vocal = [s for s in stages if s.get("name") in
             ("_stage_voice_synth", "_stage_rvc", "_stage_vocal_fx")]
    if not vocal:
        return "SKIPPED", None
    for stage in vocal:
        if stage.get("status") == "FAILED":
            return "FAILED", stage.get("reason")
    fallback = [s for s in vocal if s.get("status") == "FALLBACK"]
    if fallback:
        return "FALLBACK", fallback[0].get("reason")
    blocked = [s for s in vocal if s.get("status") == "BLOCKED"]
    if len(blocked) == len(vocal):
        return "BLOCKED", blocked[0].get("reason")
    return "OK", None


def run_god_pipeline(
    project_id: str,
    wizard_state: dict[str, Any] | None = None,
    dry_run: bool = False,
    out_root: Path | None = None,
) -> dict[str, Any]:
    """Полный трек через общий пайплайн. `wizard_state=None` — безопасный дефолт."""
    from app.core.orchestrator import run_full_pipeline

    state: dict[str, Any] = dict(wizard_state or {})
    state.setdefault("genre", "drift_phonk")
    state.setdefault("duration_sec", GOD_DURATION_SEC)
    root = Path(out_root) if out_root is not None else (
        Path(__file__).resolve().parents[2] / "output" / project_id
    )
    root.mkdir(parents=True, exist_ok=True)

    report = run_full_pipeline(project_id, state, dry_run=dry_run, out_root=root)

    stages = [
        {
            "name": stage.get("name"),
            "ok": stage.get("status") != "FAILED",
            "status": stage.get("status"),
            "duration_sec": stage.get("duration_sec", 0.0),
            "output": stage.get("output"),
            "reason": stage.get("reason"),
        }
        for stage in report.get("stages", [])
    ]
    vocal_status, vocal_reason = _vocal_report(stages)
    status = _status_from_verdict(report.get("verdict"))
    result = {
        "project_id": project_id,
        "god_mode": True,
        "status": status,
        "verdict": report.get("verdict"),
        "percent": report.get("percent"),
        "elapsed_sec": report.get("duration_sec"),
        "stages": stages,
        "vocal_status": vocal_status,
        "vocal_reason": vocal_reason,
        "master_path": report.get("master_path") if status == "completed" else None,
        "report_path": str(root / "report.json"),
        "warnings": report.get("warnings", []),
    }
    (root / "project_meta.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    return result
