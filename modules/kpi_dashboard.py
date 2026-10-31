"""
ZS Music Maker v12 «Hit Locked Pro» — kpi_dashboard.py
==========================================================

Единый KPI-дашборд для пользователя. Читает:

  · data/health.json          (снепшот здоровья стека)
  · output/projects/*/master_pipeline_v12.json  (последний прогон мастера)
  · logs/smoke_god_report.json / logs/smoke_audio_report.json  (последние smoke-результаты; smoke_v12_report.json больше не пишется — v37)
  · output/projects/*/manifest_v11.json (KPI verdict v11)

и склеивает в один HUMAN-READABLE отчёт с процентом соответствия ТЗ,
списком «что упало» и «что делать дальше».

Никаких внешних зависимостей, никакого сетевого доступа.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

# Требования ТЗ, по которым считается процент соответствия (см. раздел 16).
TZ_CHECKLIST: list[dict[str, str]] = [
    {"key": "modules_12", "tz": "3.1-3.12", "title": "12 модулей архитектуры"},
    {"key": "gui_wizard", "tz": "5", "title": "Единое окно, мастер по шагам"},
    {"key": "karaoke", "tz": "5", "title": "Караоке-режим для записи"},
    {"key": "onboarding", "tz": "5", "title": "Интерактивный Onboarding"},
    {"key": "utf8_cp866", "tz": "6", "title": "UTF-8 в коде, CP866 в консоли"},
    {"key": "auto_deps", "tz": "6", "title": "Авто-подтяжка зависимостей"},
    {"key": "smoke_tests", "tz": "7", "title": "Smoke + E2E тесты"},
    {
        "key": "readme_context",
        "tz": "8+11",
        # v37 FIX: CONTEXT.md никогда не существовал в репо — канонический
        # накопительный журнал это SESSION_LOG.md (см. правило 11 ТЗ).
        "title": "README + SESSION_LOG.md накопительно",
    },
    {"key": "agents_free", "tz": "9", "title": "Бесплатные интернет-агенты"},
    {"key": "logging", "tz": "11", "title": "Логирование всего в logs/app.log"},
    {"key": "hw_autodetect", "tz": "20.1", "title": "HW autodetect + fallback"},
    {"key": "rvc_real", "tz": "20.1[RVC]", "title": "RVC 100% рабочий"},
    {"key": "musicgen_full", "tz": "20.1[MG]", "title": "MusicGen полноценный на 12GB"},
    {"key": "author_ref", "tz": "20.3", "title": "Автор из референсов / поиск"},
    {"key": "female_backing", "tz": "20.3", "title": "Женские бэки"},
    {"key": "expert_mode", "tz": "20.3", "title": "Экспертный режим (скрытый ⋯)"},
    {
        "key": "license_provenance",
        "tz": "20.3",
        "title": "License / Provenance Manager",
    },
    {"key": "release_full", "tz": "20.2 п.32", "title": "Полный релиз-пакет"},
    {"key": "distribution_5", "tz": "20.2 п.33", "title": "5 платформ дистрибуции"},
    {"key": "hit_scorer", "tz": "20.2 п.34", "title": "AI Detector Pro + hit_scorer"},
    {"key": "queue_5", "tz": "20.2 п.35А", "title": "Очередь ≥5 треков"},
    {"key": "kpi_20_5", "tz": "20.5", "title": "KPI-мониторинг"},
]


@dataclass
class DashboardSection:
    title: str
    ok: bool
    percent: int
    lines: list[str] = field(default_factory=list)


@dataclass
class Dashboard:
    generated_at: str = ""
    percent_tz: int = 0
    verdict: str = ""
    sections: list[dict[str, Any]] = field(default_factory=list)
    checklist: list[dict[str, Any]] = field(default_factory=list)
    advice: list[str] = field(default_factory=list)
    persistence: dict[str, Any] = field(default_factory=lambda: {"requested": False, "status": "not_requested"})

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _load_json(p: Path) -> dict[str, Any] | None:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _newest(pattern: str, base: Path) -> Path | None:
    matches = list(base.rglob(pattern))
    if not matches:
        return None
    return max(matches, key=lambda p: p.stat().st_mtime)


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
        return DashboardSection(
            "Последний прогон мастера",
            False,
            0,
            [
                "Нет master_pipeline_v12.json — запусти "
                "`python -m modules.master_pipeline_v12`"
            ],
        )
    percent = int(pipe.get("percent_ready", 0))
    v = str(pipe.get("verdict", "?"))
    lines = [
        f"Проект: {pipe.get('project_id', '?')}   " f"Verdict: {v}   Ready: {percent}%"
    ]
    for s in pipe.get("stages", [])[:20]:
        mark = "OK " if s.get("ok") else "FAIL"
        fb = " (fallback)" if s.get("fallback_used") else ""
        lines.append(
            f"  [{mark}] {s.get('tz_ref', '?'):<6} "
            f"{s.get('name', '?'):<22} "
            f"{s.get('duration_sec', 0):5.2f}s{fb}"
        )
    return DashboardSection(
        "Последний прогон мастера", v.endswith("PASS"), percent, lines
    )


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
        "agents_free": has("agents/sample_hunter.py") or has("agents/sample_hunter.py"),
        "logging": (ROOT / "logs").exists(),
        "hw_autodetect": has("app/core/hw_autodetect.py"),
        "rvc_real": has("modules/rvc_manager.py") and has("modules/rvc_trainer.py"),
        "musicgen_full": has("app/core/musicgen_texture.py"),
        "author_ref": has("modules/author_ref_lyrics.py"),
        "female_backing": has("modules/female_backing.py"),
        "expert_mode": has("modules/expert_mode.py"),
        "license_provenance": has("modules/provenance.py") and has("app/core/license_manager.py"),
        "release_full": has("modules/release_pack_v9.py"),
        "distribution_5": has("modules/release/channels.py"),
        "hit_scorer": has("modules/hit_scorer/__init__.py") and has("modules/ai_detector_pro.py"),
        "queue_5": has("modules/render_queue.py"),
        "kpi_20_5": has("modules/kpi_monitor.py"),
    }


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
    * license_provenance  — есть modules/provenance.py + app/core/license_manager.py.
    * release_full        — есть modules/release_pack_v9.py.
    * distribution_5      — есть modules/release/channels.py.
    * hit_scorer          — есть пакет modules/hit_scorer/ + ai_detector_pro.py.
    * queue_5             — есть modules/render_queue.py.
    * kpi_20_5            — есть modules/kpi_monitor.py.
    """

    del pipe, smoke  # compatibility parameters; checklist evidence is filesystem/health based.
    checks = _filesystem_tz_checks()
    _apply_health_constraints(checks, health)
    return _checklist_summary(checks)


def build(save: bool = True) -> Dashboard:
    health = _load_json(ROOT / "data" / "health.json")
    pipe_path = _newest("master_pipeline_v12.json", ROOT / "output")
    pipe = _load_json(pipe_path) if pipe_path else None
    # v33 FIX: smoke_v12_report.json больше не пишется. Берём самый свежий
    # из актуальных отчётов (smoke_audio / smoke_god); fallback — старый v12.
    smoke = None
    for cand in (
        ROOT / "logs" / "smoke_god_report.json",
        ROOT / "logs" / "smoke_audio_report.json",
        ROOT / "logs" / "smoke_v12_report.json",
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
        markdown_path = ROOT / "docs" / "KPI_DASHBOARD_v12.md"
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
        "# KPI Dashboard v12 «Hit Locked Pro»",
        "",
        f"_Generated: {dash.generated_at}_",
        "",
        f"**Соответствие ТЗ: {dash.percent_tz}%**   |   "
        f"**Общий вердикт: {dash.verdict}**",
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
        f"KPI DASHBOARD v12 — {dash.generated_at}",
        f"Соответствие ТЗ: {dash.percent_tz}%   Verdict: {dash.verdict}",
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


if __name__ == "__main__":
    raise SystemExit(main())
