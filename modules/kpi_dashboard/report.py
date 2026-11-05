# -*- coding: utf-8 -*-
"""
modules/kpi_dashboard/report.py — сборка, сохранение и рендер отчёта.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from modules.kpi_dashboard.checklist import _tz_percent
from modules.kpi_dashboard.config import ROOT
from modules.kpi_dashboard.models import Dashboard
from modules.kpi_dashboard.sources import (
    _health_section,
    _latest_telemetry,
    _load_json,
    _latest_pipeline,
    _pipeline_section,
    _smoke_section,
    _telemetry_section,
)


def build(save: bool = True) -> Dashboard:
    health = _load_json(ROOT / "data" / "health.json")
    pipe = _latest_pipeline(ROOT / "output")
    # Используем отчёты актуальных smoke-наборов.
    smoke = None
    for cand in (
        ROOT / "logs" / "smoke_god_report.json",
        ROOT / "logs" / "smoke_audio_report.json",
    ):
        smoke = _load_json(cand)
        if smoke:
            break

    dash = Dashboard()
    dash.generated_at = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

    s1 = _health_section(health)
    s2 = _pipeline_section(pipe)
    s3 = _smoke_section(smoke)
    s4 = _telemetry_section(_latest_telemetry())
    dash.sections = [asdict(s1), asdict(s2), asdict(s3), asdict(s4)]

    tz_pct, entries, advice = _tz_percent(health, pipe, smoke)
    dash.checklist = entries
    dash.advice = advice
    dash.percent_tz = tz_pct

    # Общий вердикт
    if s1.ok and s2.ok and s3.ok and tz_pct >= 90:
        dash.verdict = "GREEN"
    elif tz_pct >= 70:
        dash.verdict = "YELLOW"
    else:
        dash.verdict = "RED"

    if save:
        json_path = ROOT / "data" / "kpi_dashboard.json"
        markdown_path = ROOT / "output" / "kpi_dashboard.md"
        try:
            json_path.parent.mkdir(exist_ok=True)
            markdown_path.parent.mkdir(exist_ok=True)
            markdown_path.write_text(render_markdown(dash), encoding="utf-8")
            dash.persistence = {
                "requested": True,
                "ok": True,
                "status": "saved",
                "paths": [str(json_path), str(markdown_path)],
            }
            json_path.write_text(
                json.dumps(dash.as_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            dash.persistence = {
                "requested": True,
                "ok": False,
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
            }
    return dash


def render_markdown(dash: Dashboard) -> str:
    lines = [
        "# KPI Dashboard «Hit Locked Pro»",
        "",
        f"_Generated: {dash.generated_at}_",
        "",
        f"**Наличие файлов по чеклисту: {dash.percent_tz}%**   |   "
        f"**Общий вердикт: {dash.verdict}**",
        "",
        "Показатель не подтверждает качество музыки, работу моделей или готовность Windows.",
        "",
    ]
    for s in dash.sections:
        badge = "🟢" if s["ok"] else "🔴"
        lines += [f"## {badge} {s['title']} — {s['percent']}%", ""]
        for ln in s.get("lines", []):
            lines.append(f"    {ln}")
        lines.append("")
    lines += ["## Чеклист ТЗ (раздел 16 + 20)", ""]
    lines += ["| # | ТЗ | Пункт | Статус |", "|---|----|-------|--------|"]
    for i, c in enumerate(dash.checklist, 1):
        lines.append(
            f"| {i} | {c['tz']} | {c['title']} | " f"{'✅' if c['ok'] else '❌'} |"
        )
    if dash.advice:
        lines += ["", "## Что не подтверждено / рекомендации", ""]
        for a in dash.advice:
            lines.append(f"- {a}")
    return "\n".join(lines) + "\n"


def render_text(dash: Dashboard) -> str:
    out = [
        "=" * 72,
        f"KPI DASHBOARD — {dash.generated_at}",
        f"Наличие файлов: {dash.percent_tz}%   Verdict: {dash.verdict}",
        "Не подтверждает работу моделей, качество музыки или готовность Windows.",
        "-" * 72,
    ]
    for s in dash.sections:
        out.append(f"[{'OK' if s['ok'] else 'X '}] {s['title']} " f"({s['percent']}%)")
        for ln in s.get("lines", []):
            out.append(f"    {ln}")
    out.append("-" * 72)
    out.append("TZ CHECKLIST:")
    for c in dash.checklist:
        out.append(f"  [{'V' if c['ok'] else ' '}] {c['tz']:<10} " f"{c['title']}")
    if dash.advice:
        out.append("-" * 72)
        out.append("ADVICE:")
        for a in dash.advice[:15]:
            out.append(f"  - {a}")
    out.append("=" * 72)
    return "\n".join(out)


def main() -> int:
    dash = build()
    print(render_text(dash))
    return 0 if dash.verdict == "GREEN" else (1 if dash.verdict == "YELLOW" else 2)
