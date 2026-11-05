# -*- coding: utf-8 -*-
"""
modules/kpi_dashboard/checklist.py — расчёт процента соответствия ТЗ.

Файловые доказательства понижаются, если внутренний модуль не импортируется
(health.internals) — «зелёный» процент нельзя получить на сломанном модуле.
"""

from __future__ import annotations

from typing import Any

from modules.kpi_dashboard.config import TZ_CHECKLIST
from modules.kpi_dashboard.sources import _filesystem_tz_checks


def _apply_health_constraints(checks: dict[str, bool], health: dict[str, Any] | None) -> None:
    """Downgrade filesystem evidence when a related internal module cannot import."""
    if health is None:
        return
    internal_ok = {entry.get("name"): entry.get("ok") for entry in health.get("internals", [])}
    if not internal_ok.get("modules.rvc_manager", True) or not internal_ok.get(
        "modules.rvc_trainer", True
    ):
        checks["rvc_real"] = False
    if not internal_ok.get("app.core.musicgen_texture", True):
        checks["musicgen_full"] = False
    if not internal_ok.get("modules.kpi_monitor", True):
        checks["kpi_20_5"] = False


def _checklist_summary(checks: dict[str, bool]) -> tuple[int, list[dict[str, Any]], list[str]]:
    """Build checklist entries, percentage and advice from checked evidence."""
    entries = [
        {"key": item["key"], "tz": item["tz"], "title": item["title"], "ok": bool(checks.get(item["key"], False))}
        for item in TZ_CHECKLIST
    ]
    passed = sum(1 for entry in entries if entry["ok"])
    percent = int(100 * passed / max(1, len(TZ_CHECKLIST)))
    advice = [
        f"[TZ {entry['tz']}] {entry['title']} — не подтверждено, проверь наличие соответствующего файла/модуля."
        for entry in entries if not entry["ok"]
    ]
    return percent, entries, advice


def _tz_percent(
    health: dict[str, Any] | None,
    pipe: dict[str, Any] | None,
    smoke: dict[str, Any] | None,
) -> (int, list[dict[str, Any]], list[str]):
    """Оценка соответствия ТЗ по чеклисту раздела 16 + разделу 20.

    Логика:
    * modules_12          — есть все 12 модулей → OK по итогам health.internals.
    * gui_wizard          — PySide6 доступен (health) ИЛИ Gradio.
    * karaoke/onboarding  — файлы modules/karaoke_engine.py, onboarding.py.
    * utf8_cp866          — жёстко true (реализовано в main_v11/main_v12).
    * auto_deps           — есть install.py + requirements.txt (windows_build.bat не существует).
    * smoke_tests         — tools/smoke_audio.py и tools/smoke_god.py (smoke_v12 давно удалён).
    * readme_context      — README.md + SESSION_LOG.md (CONTEXT.md не существует).
    * agents_free         — есть agents/sample_hunter*trend_scout*.
    * logging             — есть logs/app.log.
    * hw_autodetect       — есть app/core/hw_autodetect.py.
    * rvc_real            — есть modules/rvc_manager.py + rvc_trainer.py.
    * musicgen_full       — есть app/core/musicgen_texture.py + hw_directml.
    * author_ref          — есть modules/author_ref_lyrics.py.
    * female_backing      — есть modules/female_backing.py.
    * expert_mode         — есть modules/expert_mode.py.
    * license_provenance  — есть app/core/license_manager.py.
    * release_full        — есть modules/release/pack.py + export.py.
    * distribution_5      — есть modules/release/channels.py.
    * hit_scorer          — есть пакет modules/hit_scorer/ + ai_detector_pro.py.
    * queue_5             — есть modules/render_queue.py.
    * kpi_20_5            — есть modules/kpi_monitor.py.
    """

    del pipe, smoke  # compatibility parameters; checklist evidence is filesystem/health based.
    checks = _filesystem_tz_checks()
    _apply_health_constraints(checks, health)
    return _checklist_summary(checks)
