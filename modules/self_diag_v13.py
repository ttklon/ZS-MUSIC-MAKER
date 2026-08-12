"""
ZS Music Maker v13 — self_diag_v13.py
=====================================

Единая CLI-ДИАГНОСТИКА **для пользователя**, который «ничего не понимает
в технологиях» (ТЗ 4 финальное замечание).

v12 уже имеет `health_v12` и `kpi_dashboard_v12`. Эти два дают
машиночитаемые JSON. Но пользователь видит консоль. Ему нужны
цветные строки, понятный Action Plan и чтобы не нужно было знать
про pip, json, venv.

self_diag_v13 читает:
  · data/health_v12.json
  · data/kpi_dashboard_v12.json
  · data/hw_profile*.json
  · проверяет наличие 6 обязательных папок/файлов
  · проверяет последний smoke_v12_report.json

И выдаёт:
  · цветную ASCII-таблицу (зелёный/жёлтый/красный);
  · Action Plan: список конкретных «сделай это» строк;
  · сохранение в logs/self_diag_v13.txt для истории.

Никаких тяжёлых зависимостей — работает на голом Python 3.8+.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "logs"
# v22: ленивое создание (не при импорте)

# ANSI codes (с деградацией на Windows <10 / non-tty)
_USE_ANSI = sys.stdout.isatty() and os.environ.get("TERM", "") != "dumb"
if os.name == "nt" and not _USE_ANSI:
    # Разрешаем enable VT-mode, cmd поддерживает с Win10 Anniversary
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        _USE_ANSI = True
    except Exception:
        _USE_ANSI = False


def _c(code: str, text: str) -> str:
    return f"\x1b[{code}m{text}\x1b[0m" if _USE_ANSI else text


GREEN = lambda t: _c("32", t)
RED = lambda t: _c("31;1", t)
YELLOW = lambda t: _c("33;1", t)
BOLD = lambda t: _c("1", t)
CYAN = lambda t: _c("36", t)


# Обязательные папки/файлы, которые должны быть в любой инсталляции
EXPECTED_PATHS: list[tuple[str, str, str]] = [
    ("main.py", "OK", "Файл запуска приложения"),
    ("modules/reference_ingest.py", "OK", "Multi-references analyzer (ТЗ 3.2)"),
    ("modules/arrangement_engine.py", "OK", "Beat constructor / arrangement (ТЗ 3.5)"),
    ("modules/rvc_manager.py", "OK", "RVC v2 (ТЗ 3.10)"),
    ("modules/release_pack_v9.py", "OK", "Release pack (ТЗ 3.12)"),
    ("modules/health_v12.py", "OK", "Health-check v12"),
    ("modules/master_pipeline_v12.py", "OK", "Master pipeline v12"),
    ("modules/kpi_dashboard_v12.py", "OK", "KPI dashboard v12"),
    ("app/core/orchestrator_v12_patch.py", "OK", "Orchestrator v12"),
    ("data/", "FLEX", "Локальная БД (создаётся)"),
    ("output/", "FLEX", "Артефакты (создаётся)"),
    ("voice_vault/", "OK", "Voice Vault (ТЗ 3.8)"),
    ("lyric_vault/", "OK", "Lyric Vault (ТЗ 3.7)"),
    ("logs/", "FLEX", "Логи (создаётся)"),
    ("models/rvc/", "OK", "Папка для голосовых моделей RVC"),
    ("models/musicgen_cache/", "FLEX", "Кэш MusicGen (опционально)"),
    ("references/", "FLEX", "Пользовательские референсы (опционально)"),
]


def _read_json_silent(p: Path) -> dict[str, Any] | None:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def check_layout() -> list[dict[str, Any]]:
    """Возвращает список {path, status, message, severity}."""
    out: list[dict[str, Any]] = []
    for rel, need, descr in EXPECTED_PATHS:
        p = ROOT / rel
        if p.exists():
            if need == "OK":
                out.append(
                    {"path": rel, "status": "OK", "message": descr, "severity": "green"}
                )
            else:
                out.append(
                    {
                        "path": rel,
                        "status": "PRESENT",
                        "message": descr,
                        "severity": "green",
                    }
                )
        else:
            if need == "OK":
                out.append(
                    {
                        "path": rel,
                        "status": "MISSING",
                        "message": f"❌ {descr} — нужно создать",
                        "severity": "red",
                    }
                )
            else:
                out.append(
                    {
                        "path": rel,
                        "status": "AUTO",
                        "message": f"⚠ {descr} — будет создан при первом запуске",
                        "severity": "yellow",
                    }
                )
    return out


def check_health() -> dict[str, Any] | None:
    return _read_json_silent(ROOT / "data" / "health_v12.json")


def check_kpi() -> dict[str, Any] | None:
    return _read_json_silent(ROOT / "data" / "kpi_dashboard_v12.json")


def check_smoke_recent() -> dict[str, Any] | None:
    rep = _read_json_silent(LOGS / "smoke_v12_report.json")
    return rep


def collect_action_plan(
    layout: list[dict[str, Any]],
    health: dict[str, Any] | None,
    kpi: dict[str, Any] | None,
    smoke: dict[str, Any] | None,
) -> list[str]:
    """Краткий список конкретных действий для пользователя."""
    plan: list[str] = []

    # 1) layout
    red_layout = [it for it in layout if it["severity"] == "red"]
    if red_layout:
        plan.append(BOLD("🔴 СРОЧНО: восстановить недостающие файлы:"))
        for it in red_layout:
            plan.append(f"    ✗ {it['path']}  —  {it['message']}")

    yellow_layout = [it for it in layout if it["severity"] == "yellow"]
    if yellow_layout:
        plan.append("🟡 Эти папки появятся автоматически при первом запуске:")
        for it in yellow_layout:
            plan.append(f"    · {it['path']}")

    # 2) health
    if health is None:
        plan.append(
            "🟡 Не запускался health_v12 — рекомендую прогнать "
            "`python -m modules.health_v12`"
        )
    else:
        verdict = health.get("verdict", "?")
        adv = health.get("advice", [])
        if verdict == "GREEN":
            plan.append("🟢 Стек в порядке (health GREEN) — можно делать трек.")
        elif verdict == "YELLOW":
            plan.append("🟡 Стек работает, но без этих модулей качество ниже:")
            for a in (adv or [])[:5]:
                plan.append(f"    · {a}")
        elif verdict == "RED":
            plan.append("🔴 Стек сломан (health RED) — сначала поставь:")
            for a in (adv or [])[:5]:
                plan.append(f"    · {a}")

    # 3) kpi
    if kpi is None:
        plan.append(
            "🟡 KPI дашборд ещё не строился — " "`python -m modules.kpi_dashboard_v12`"
        )
    else:
        verdict = kpi.get("verdict", "?")
        pct = kpi.get("percent_tz", 0)
        if verdict == "GREEN" and pct >= 95:
            plan.append(f"🟢 Готовность ТЗ {pct}% — отлично, можно релизить.")
        elif verdict == "YELLOW":
            plan.append(f"🟡 Готовность ТЗ {pct}% — есть место для роста:")
            for a in (kpi.get("advice", []) or [])[:3]:
                plan.append(f"    · {a}")
        elif verdict == "RED":
            plan.append(f"🔴 Готовность ТЗ {pct}% — нужно доработать модули:")
            for a in (kpi.get("advice", []) or [])[:3]:
                plan.append(f"    · {a}")

    # 4) smoke
    if smoke is None:
        plan.append("🟡 Smoke ещё не гонялся — запусти `smoke_v12.py`.")
    else:
        passed = smoke.get("passed", 0)
        failed = smoke.get("failed", 0)
        total = smoke.get("total", 0)
        if failed == 0 and total > 0:
            plan.append(f"🟢 Smoke {passed}/{total} PASS — стабильно.")
        elif failed > 0:
            plan.append(
                f"🔴 Smoke {passed}/{total} PASS, {failed} FAIL — " "нужны исправления."
            )

    if not plan:
        plan.append("🟢 Все системы в порядке. Запускай wizard!")
    return plan


def render_report(
    layout: list[dict[str, Any]],
    health: dict[str, Any] | None,
    kpi: dict[str, Any] | None,
    smoke: dict[str, Any] | None,
    plan: list[str],
) -> str:
    lines: list[str] = []
    lines.append(BOLD(CYAN("=" * 70)))
    lines.append(BOLD(CYAN("  ZS Music Maker v13 — Self-Diagnostic (для человека)")))
    lines.append(BOLD(CYAN("=" * 70)))

    # 1. Общая сводка
    lines.append("")
    lines.append(BOLD("Сводка состояния:"))
    n_red_layout = sum(1 for it in layout if it["severity"] == "red")
    n_yel_layout = sum(1 for it in layout if it["severity"] == "yellow")
    n_grn_layout = sum(1 for it in layout if it["severity"] == "green")
    health_verdict = (health or {}).get("verdict", "—")
    health_pct = (health or {}).get("percent_ready", "—")
    kpi_verdict = (kpi or {}).get("verdict", "—")
    kpi_pct = (kpi or {}).get("percent_tz", "—")
    smoke_str = (
        f"{smoke.get('passed','?')}/{smoke.get('total','?')}"
        if smoke
        else "не запускался"
    )
    lines.append(
        f"  • layout:     🟢 {n_grn_layout}  🟡 {n_yel_layout}  " f"🔴 {n_red_layout}"
    )
    lines.append(f"  • health_v12: {health_verdict} ({health_pct}%)")
    lines.append(f"  • KPI ТЗ:     {kpi_verdict} ({kpi_pct}%)")
    lines.append(f"  • smoke:      {smoke_str}")

    # 2. Action Plan
    lines.append("")
    lines.append(BOLD("Что делать дальше:"))
    for line in plan:
        lines.append("  " + line)

    # 3. Подробная таблица слоя
    lines.append("")
    lines.append(BOLD("Структура проекта (раздел за разделом):"))
    lines.append(f"  [{'СТАТУС':<11}] {'ПУТЬ':<45} ОПИСАНИЕ")
    for it in layout:
        if it["severity"] == "green":
            mark = GREEN("✓ OK")
        elif it["severity"] == "yellow":
            mark = YELLOW("~ AUTO")
        else:
            mark = RED("✗ MISSING")
        lines.append(f"  [{mark:<11}] {it['path']:<45} {it['message']}")

    lines.append("")
    lines.append(BOLD(CYAN("=" * 70)))
    return "\n".join(lines)


def run(save_to_log: bool = True) -> dict[str, Any]:
    layout = check_layout()
    health = check_health()
    kpi = check_kpi()
    smoke = check_smoke_recent()
    plan = collect_action_plan(layout, health, kpi, smoke)

    report = render_report(layout, health, kpi, smoke, plan)
    print(report)

    out = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "layout": layout,
        "health_present": bool(health),
        "kpi_present": bool(kpi),
        "smoke_present": bool(smoke),
        "action_plan": plan,
    }

    if save_to_log:
        try:
            LOGS.mkdir(parents=True, exist_ok=True)
            (LOGS / "self_diag_v13.txt").write_text(
                report
                + "\n\n# JSON snapshot #\n"
                + json.dumps(out, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as _e:
            # AUDIT-FIX P1: LOGS мог не существовать — отсутствие лога
            # не должно ронять self-diag (--self-diag возвращал код 2).
            print(f"[self_diag_v13] warn: cannot write log: {_e}")
    return out


def main_entry() -> int:
    run(save_to_log=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main_entry())
