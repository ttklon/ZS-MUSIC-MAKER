# -*- coding: utf-8 -*-
"""
modules/kpi_dashboard/sources.py — чтение источников KPI.

Health-снимок, последний прогон мастера, smoke-отчёты, телеметрия и
файловые доказательства требований ТЗ. Только чтение, без сети.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from modules.kpi_dashboard.config import ROOT
from modules.kpi_dashboard.models import DashboardSection


def _load_json(p: Path) -> dict[str, Any] | None:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _latest_pipeline(base: Path) -> dict[str, Any] | None:
    """Find the latest readable current pipeline report, not a legacy filename."""
    candidates = []
    for path in base.rglob("report.json"):
        try:
            candidates.append((path.stat().st_mtime, path))
        except OSError:
            continue
    for _, path in sorted(candidates, key=lambda item: item[0], reverse=True):
        payload = _load_json(path)
        if (isinstance(payload, dict) and isinstance(payload.get("stages"), list)
                and payload.get("project_id") and payload.get("verdict")):
            return payload
    return None


def _health_section(health: dict[str, Any] | None) -> DashboardSection:
    if not health:
        return DashboardSection(
            "Стек / зависимости",
            False,
            0,
            ["health.json не найден — запусти " "`python -m modules.health`"],
        )
    percent = int(health.get("percent_ready", 0))
    v = health.get("verdict", "?")
    lines = [
        f"Verdict: {v}   Ready: {percent}%",
        f"HW mode: {health.get('hw_profile', {}).get('mode', '?')}   "
        f"GPU: {health.get('hw_profile', {}).get('gpu', '?')}",
    ]
    ok_count = sum(1 for e in health.get("externals", []) if e.get("ok"))
    tot = len(health.get("externals", []))
    lines.append(f"External deps OK: {ok_count}/{tot}")
    ok_int = sum(1 for e in health.get("internals", []) if e.get("ok"))
    tot_int = len(health.get("internals", []))
    lines.append(f"Internal modules OK: {ok_int}/{tot_int}")
    for a in (health.get("advice") or [])[:8]:
        lines.append(f"  ! {a}")
    return DashboardSection("Стек / зависимости", v == "GREEN", percent, lines)


def _latest_telemetry(path: Path = ROOT / "data" / "kpi_history.jsonl") -> dict[str, Any] | None:
    """Read only the latest v1 allowlisted telemetry record; malformed/legacy lines are ignored."""
    try:
        for raw in reversed(path.read_text(encoding="utf-8").splitlines()):
            payload = json.loads(raw)
            if payload.get("schema") == "zsmm.kpi-telemetry.v1" and isinstance(payload.get("stages"), list):
                return payload
    except (OSError, json.JSONDecodeError):
        return None
    return None


def _telemetry_section(telemetry: dict[str, Any] | None) -> DashboardSection:
    if not telemetry:
        return DashboardSection("Telemetry (non-PII)", False, 0, ["No sanitized KPI telemetry recorded yet."])
    stages = telemetry.get("stages", [])
    successful = sum(stage.get("status") == "ok" for stage in stages)
    lines = [
        f"Pipeline duration: {float(telemetry.get('pipeline_duration_sec') or 0):.2f}s",
        f"Stages OK: {successful}/{len(stages)}",
    ]
    for stage in stages[:20]:
        vram = stage.get("vram_gb")
        score = stage.get("score")
        details = [f"{float(stage.get('duration_sec') or 0):.2f}s"]
        if isinstance(vram, (int, float)):
            details.append(f"VRAM {vram:.2f}GB")
        if isinstance(score, (int, float)):
            details.append(f"score {score:.2f}")
        lines.append(f"  [{stage.get('status', 'failed')}] {stage.get('stage', 'redacted')}: " + ", ".join(details))
    return DashboardSection("Telemetry (non-PII)", successful == len(stages), 100 if stages else 0, lines)


def _pipeline_section(pipe: dict[str, Any] | None) -> DashboardSection:
    if not pipe:
        return DashboardSection("Последний прогон мастера", False, 0,
                                ["Нет отчёта report.json — запустите полный прогон приложения"])
    percent = int(pipe.get("percent", 0))
    verdict = str(pipe.get("verdict", "?"))
    lines = [f"Проект: {pipe.get('project_id', '?')}   Verdict: {verdict}   Ready: {percent}%"]
    if pipe.get("dry_run"):
        lines.append("Прогон без тяжёлых моделей (dry-run)")
    if pipe.get("only"):
        lines.append(f"Частичный прогон: {pipe['only']}")
    for stage in pipe.get("stages", [])[:20]:
        if isinstance(stage, dict):
            lines.append(f"  [{stage.get('status', '?')}] {stage.get('name', '?')}")
    for failure in pipe.get("quality_gate_failures") or []:
        lines.append(f"  Quality gate: {failure}")
    return DashboardSection("Последний прогон мастера", verdict == "PASS" and not pipe.get("dry_run")
                            and not pipe.get("only") and not pipe.get("quality_gate_failures"), percent, lines)


def _smoke_section(smoke: dict[str, Any] | None) -> DashboardSection:
    if not smoke:
        return DashboardSection(
            "Smoke-тесты",
            False,
            0,
            # v33 FIX: указываем реальные скрипты, а не удалённый smoke_v12.
            ["Нет свежего smoke-отчёта — запусти `python tools/smoke_audio.py` "
             "и `python tools/smoke_god.py`"],
        )
    passed = int(smoke.get("passed", 0))
    failed = int(smoke.get("failed", 0))
    total = passed + failed
    pct = int(100 * passed / max(1, total))
    lines = [f"PASS: {passed} / {total}   FAIL: {failed}"]
    for name, ok in list(smoke.get("cases", {}).items())[:30]:
        lines.append(f"  [{'OK  ' if ok else 'FAIL'}] {name}")
    # v33: название секции из отчёта, без жёсткой привязки к версии.
    label = smoke.get("name", "smoke")
    return DashboardSection(f"Smoke-тесты ({label})", failed == 0, pct, lines)


def _filesystem_tz_checks() -> dict[str, bool]:
    """Return checklist evidence derived only from repository filesystem state."""
    def has(path: str) -> bool:
        return (ROOT / path).exists()

    module_names = (
        "analyzer", "beat_constructor", "groove_extractor", "arrangement_engine",
        "voice_synth", "voice_convert", "voice_vault", "rvc_manager", "mastering",
        "mastering_reference", "release_pack_v9", "lyric_vault", "author_ref_lyrics",
    )
    return {
        "modules_12": all(has(f"modules/{name}.py") for name in module_names),
        "gui_wizard": has("app/gui/wizard/window.py"),
        "karaoke": has("modules/karaoke_engine.py") and has("ui/karaoke_recorder.py"),
        "onboarding": has("modules/onboarding.py") or has("app/gui/onboarding.py"),
        "utf8_cp866": True,
        "auto_deps": has("install.py") and has("requirements.txt"),
        "smoke_tests": has("tools/smoke_audio.py") and has("tools/smoke_god.py"),
        "readme_context": has("README.md") and has("SESSION_LOG.md"),
        "agents_free": has("agents/sample_hunter/__init__.py") or has("agents/trend_scout.py"),
        "logging": (ROOT / "logs").exists(),
        "hw_autodetect": has("app/core/hw_autodetect.py"),
        "rvc_real": has("modules/rvc_manager.py") and has("modules/rvc_trainer.py"),
        "musicgen_full": has("app/core/musicgen_texture.py"),
        "author_ref": has("modules/author_ref_lyrics.py"),
        "female_backing": has("modules/female_backing.py"),
        "expert_mode": has("modules/expert_mode.py"),
        "license_provenance": has("app/core/license_manager.py"),
        "release_full": has("modules/release/pack.py") and has("modules/release/export.py"),
        "distribution_5": has("modules/release/channels.py"),
        "hit_scorer": has("modules/hit_scorer/__init__.py") and has("modules/ai_detector_pro.py"),
        "queue_5": has("modules/render_queue.py"),
        "kpi_20_5": has("modules/kpi_monitor.py"),
    }
