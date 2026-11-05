"""
ZS Music Maker v13 — self_diag.py
=====================================

Единая CLI-ДИАГНОСТИКА **для пользователя**, который «ничего не понимает
в технологиях» (ТЗ 4 финальное замечание).

v12 уже имеет `health` и `kpi_dashboard`. Эти два дают
машиночитаемые JSON. Но пользователь видит консоль. Ему нужны
цветные строки, понятный Action Plan и чтобы не нужно было знать
про pip, json, venv.

self_diag читает:
  · data/health.json
  · data/kpi_dashboard.json
  · data/hw_profile*.json
  · проверяет наличие 6 обязательных папок/файлов
  · проверяет последний smoke-отчёт (v37 FIX: smoke_v12_report.json давно
    не пишется — активные: smoke_god_report.json / smoke_audio_report.json)

И выдаёт:
  · цветную ASCII-таблицу (зелёный/жёлтый/красный);
  · Action Plan: список конкретных «сделай это» строк;
  · сохранение в logs/self_diag.txt для истории.

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
    ("modules/beat/__init__.py", "OK", "Beat constructor / arrangement (ТЗ 3.5)"),
    ("modules/rvc_manager/__init__.py", "OK", "RVC v2 (ТЗ 3.10)"),
    ("modules/release/__init__.py", "OK", "Release pack (ТЗ 3.12)"),
    ("modules/health.py", "OK", "Health-check"),
    ("modules/mastering.py", "OK", "Master pipeline"),
    ("modules/kpi_dashboard/__init__.py", "OK", "KPI dashboard"),
    ("app/core/orchestrator.py", "OK", "Оркестратор пайплайна"),
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
    return _read_json_silent(ROOT / "data" / "health.json")


def check_kpi() -> dict[str, Any] | None:
    return _read_json_silent(ROOT / "data" / "kpi_dashboard.json")


def check_smoke_recent() -> dict[str, Any] | None:
    # v33 FIX (P1, SESSION_LOG v31.7): smoke_v12_report.json больше не
    # существует — smoke_audio/v29 теперь пишут собственные отчёты в logs/.
    # Берём самый свежий доступный; старый v12 — только как fallback.
    for name in ("smoke_god_report.json", "smoke_audio_report.json", "smoke_v12_report.json"):
        rep = _read_json_silent(LOGS / name)
        if rep:
            return rep
    return None


def _append_layout_actions(plan: list[str], layout: list[dict[str, Any]]) -> None:
    """Append urgent and deferred filesystem actions."""
    red_layout = [item for item in layout if item["severity"] == "red"]
    if red_layout:
        plan.append(BOLD("🔴 СРОЧНО: восстановить недостающие файлы:"))
        plan.extend(f"    ✗ {item['path']}  —  {item['message']}" for item in red_layout)
    yellow_layout = [item for item in layout if item["severity"] == "yellow"]
    if yellow_layout:
        plan.append("🟡 Эти папки появятся автоматически при первом запуске:")
        plan.extend(f"    · {item['path']}" for item in yellow_layout)


def _append_health_actions(plan: list[str], health: dict[str, Any] | None) -> None:
    """Append actionable health-report guidance."""
    if health is None:
        plan.append("🟡 Не запускался health — рекомендую прогнать `python -m modules.health`")
        return
    verdict = health.get("verdict", "?")
    advice = (health.get("advice", []) or [])[:5]
    messages = {
        "GREEN": "🟢 Стек в порядке (health GREEN) — можно делать трек.",
        "YELLOW": "🟡 Стек работает, но без этих модулей качество ниже:",
        "RED": "🔴 Стек сломан (health RED) — сначала поставь:",
    }
    if verdict in messages:
        plan.append(messages[verdict])
        if verdict != "GREEN":
            plan.extend(f"    · {item}" for item in advice)


def _append_kpi_actions(plan: list[str], kpi: dict[str, Any] | None) -> None:
    """Append actionable KPI-report guidance."""
    if kpi is None:
        plan.append("🟡 KPI дашборд ещё не строился — `python -m modules.kpi_dashboard`")
        return
    verdict = kpi.get("verdict", "?")
    percent = kpi.get("percent_tz", 0)
    if verdict == "GREEN" and percent >= 95:
        plan.append(f"🟢 Готовность ТЗ {percent}% — отлично, можно релизить.")
    elif verdict in {"YELLOW", "RED"}:
        suffix = "есть место для роста:" if verdict == "YELLOW" else "нужно доработать модули:"
        marker = "🟡" if verdict == "YELLOW" else "🔴"
        plan.append(f"{marker} Готовность ТЗ {percent}% — {suffix}")
        plan.extend(f"    · {item}" for item in (kpi.get("advice", []) or [])[:3])


def _append_smoke_actions(plan: list[str], smoke: dict[str, Any] | None) -> None:
    """Append smoke-report action guidance."""
    if smoke is None:
        plan.append("🟡 Smoke ещё не гонялся — запусти `python tools/smoke_audio.py` и `python tools/smoke_god.py`.")
        return
    passed = smoke.get("passed", 0)
    failed = smoke.get("failed", 0)
    total = smoke.get("total", 0)
    if failed == 0 and total > 0:
        plan.append(f"🟢 Smoke {passed}/{total} PASS — стабильно.")
    elif failed > 0:
        plan.append(f"🔴 Smoke {passed}/{total} PASS, {failed} FAIL — нужны исправления.")


def collect_action_plan(
    layout: list[dict[str, Any]],
    health: dict[str, Any] | None,
    kpi: dict[str, Any] | None,
    smoke: dict[str, Any] | None,
) -> list[str]:
    """Build the ordered human action plan from layout and report snapshots."""
    plan: list[str] = []
    _append_layout_actions(plan, layout)
    _append_health_actions(plan, health)
    _append_kpi_actions(plan, kpi)
    _append_smoke_actions(plan, smoke)
    return plan or ["🟢 Все системы в порядке. Запускай wizard!"]


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
    lines.append(f"  • health: {health_verdict} ({health_pct}%)")
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
        # v30 FIX (P1): раньше при отсутствии каталога logs/ (свежий clone)
        # write_text падал с FileNotFoundError и main.py --self-diag завершался
        # с "failed: [Errno 2]". Создаём каталог лениво перед записью.
        LOGS.mkdir(parents=True, exist_ok=True)
        (LOGS / "self_diag.txt").write_text(
            report
            + "\n\n# JSON snapshot #\n"
            + json.dumps(out, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return out


def main_entry() -> int:
    run(save_to_log=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main_entry())
