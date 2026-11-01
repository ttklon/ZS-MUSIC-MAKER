"""
ZS Music Maker v12 «Hit Locked Pro» — health.py
====================================================

Единый health-check всей системы. Запускается ПЕРЕД мастером и перед
release-пайплайном, чтобы:

* сообщить пользователю, что реально работает, что деградирует, что упало;
* дать понятные советы «как включить эту фичу»;
* составить машиночитаемый snapshot (`data/health.json`), который потом
  читает KPI-dashboard и оркестратор для маршрутизации fallback-ов.

ТЗ-привязка:
  · раздел 6  — «никаких ошибок при установке»;
  · раздел 11 — логирование всего в logs/app.log;
  · раздел 20.1 [RVC/MUSICGEN] — честная диагностика режимов;
  · раздел 20.5 — KPI-контроль требует знать реальное состояние стека.

Никаких платных сервисов, никакого сетевого доступа во время health-check —
только импорт локальных модулей и опрос железа через уже установленный
`app.core.hw_autodetect`.
"""

from __future__ import annotations

import importlib
import json
import platform
import sys
import time
import traceback
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
#  1. Регистр проверок
# ---------------------------------------------------------------------------
#
# Каждая запись: (module_path, human_name, requirement_tag).
# requirement_tag:
#   "core"     — без этого приложение не запустится (RED, если нет);
#   "quality"  — без этого качество упадёт, но пайплайн выживет (YELLOW);
#   "optional" — необязательно (GREEN даже при отсутствии).
#

CHECKS: list[dict[str, str]] = [
    # ---- core ----
    {"mod": "numpy", "name": "numpy", "req": "core"},
    {"mod": "soundfile", "name": "soundfile", "req": "core"},
    {"mod": "scipy", "name": "scipy", "req": "core"},
    # GUI: любое из двух даёт зелёный, оба — идеально
    {"mod": "PySide6", "name": "PySide6 (native)", "req": "core_alt", "group": "gui"},
    {"mod": "gradio", "name": "Gradio (fallback)", "req": "core_alt", "group": "gui"},
    # ---- quality ----
    {"mod": "librosa", "name": "librosa", "req": "quality"},
    {"mod": "pydub", "name": "pydub", "req": "quality"},
    {"mod": "matchering", "name": "matchering", "req": "quality"},
    {"mod": "pyttsx3", "name": "pyttsx3 (TTS fallback)", "req": "quality"},
    {"mod": "mutagen", "name": "mutagen (ID3)", "req": "quality"},
    {"mod": "PIL", "name": "Pillow", "req": "quality"},
    # ---- optional (heavy) ----
    {"mod": "essentia", "name": "essentia", "req": "optional"},
    {"mod": "torch", "name": "torch", "req": "optional"},
    {"mod": "torch_directml", "name": "torch-directml (AMD)", "req": "optional"},
    {"mod": "demucs", "name": "demucs v4", "req": "optional"},
    {"mod": "whisper", "name": "openai-whisper", "req": "optional"},
    {"mod": "TTS", "name": "Coqui XTTS-v2", "req": "optional"},
    {"mod": "bark", "name": "suno-bark", "req": "optional"},
    {"mod": "rvc_python", "name": "rvc-python", "req": "optional"},
]

# Внутренние модули проекта: должны быть на месте (проверка накопительности).
INTERNAL_MODULES: list[str] = [
    # ядро анализа и аранжировки
    "modules.analyzer",
    "modules.beat",
    "modules.beat_constructor",
    "modules.groove_extractor",
    "modules.reference_ingest",
    "modules.arrangement_engine",
    "modules.hit_scorer",
    # голос
    "modules.voice_vault",
    "modules.voice_recording",
    "modules.rvc_manager",
    "modules.vocal_fx",
    # текст и мастеринг
    "modules.lyrics",
    "modules.author_ref_lyrics",
    "modules.mastering",
    "modules.anti_neuro",
    # выпуск и наблюдаемость
    "modules.release",
    "modules.video_edit",
    "modules.kpi_monitor",
    "modules.kpi_dashboard",
    "modules.expert_mode",
    "app.core.hw_autodetect",
    "app.core.orchestrator",
]


# ---------------------------------------------------------------------------
#  2. Модель отчёта
# ---------------------------------------------------------------------------


@dataclass
class ProbeResult:
    key: str
    name: str
    requirement: str
    ok: bool
    version: str | None = None
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HealthReport:
    generated_at: float = field(default_factory=lambda: time.time())
    generated_at_human: str = ""
    platform: str = ""
    python: str = ""
    hw_profile: dict[str, Any] = field(default_factory=dict)
    externals: list[dict[str, Any]] = field(default_factory=list)
    internals: list[dict[str, Any]] = field(default_factory=list)
    core_ok: bool = False
    quality_ok: bool = False
    optional_ok_count: int = 0
    optional_total: int = 0
    verdict: str = ""  # GREEN / YELLOW / RED
    percent_ready: int = 0  # 0..100
    advice: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
#  3. Пробы
# ---------------------------------------------------------------------------


def _probe(mod_path: str, name: str, req: str) -> ProbeResult:
    try:
        m = importlib.import_module(mod_path)
        ver = getattr(m, "__version__", None) or getattr(m, "VERSION", None)
        if ver is None and hasattr(m, "version"):
            v = m.version
            ver = v if isinstance(v, str) else None
        return ProbeResult(mod_path, name, req, True, str(ver) if ver else None)
    except Exception as e:  # noqa: BLE001
        return ProbeResult(mod_path, name, req, False, None, f"{type(e).__name__}: {e}")


def _hw_probe() -> dict[str, Any]:
    profile: dict[str, Any] = {}
    try:
        from app.core import hw_autodetect  # type: ignore

        for m in ("detect_hardware", "detect", "probe"):
            if hasattr(hw_autodetect, m):
                p = getattr(hw_autodetect, m)()
                if isinstance(p, dict):
                    profile = p
                    break
    except Exception as e:  # noqa: BLE001
        profile = {"error": f"{type(e).__name__}: {e}"}

    # На всякий случай — минимальный fallback
    if not profile:
        profile = {
            "cpu": platform.processor() or "unknown",
            "os": platform.platform(),
            "ram_gb_est": None,
            "gpu": "unknown",
            "mode": "fallback_hw",
        }
    return profile


# ---------------------------------------------------------------------------
#  4. Сборка отчёта
# ---------------------------------------------------------------------------


def _advice_for(probe: ProbeResult) -> str | None:
    """Человеко-понятный совет — что делать, если проба упала."""
    if probe.ok:
        return None
    hint = {
        "PySide6": "GUI не запустится. Установи: pip install PySide6>=6.7",
        "gradio": "Экспертный режим (Ctrl+E) не откроется. pip install gradio",
        # v37 FIX: пин <2.0 устарел (v33 снял его из requirements — стек тестируется на numpy 2.x).
        "numpy": 'Ядро не поднимется. pip install "numpy>=1.26"',
        "soundfile": "Не сможем читать/писать wav. pip install soundfile",
        "scipy": "Часть DSP работать не будет. pip install scipy",
        "librosa": "Analyzer уйдёт в очень грубый fallback. pip install librosa",
        "pydub": "Микс и mp3-экспорт деградируют. pip install pydub + ffmpeg",
        "matchering": "Мастеринг под референс отключится. pip install matchering",
        "pyttsx3": "Гарантированный TTS-fallback пропадёт. pip install pyttsx3",
        "mutagen": "ID3-теги не пропишутся. pip install mutagen",
        "PIL": "Обложки не нарисуются. pip install Pillow",
        "essentia": "Аналитика упадёт на librosa-only (это ок).",
        "torch": "Тяжёлые модели (MusicGen/RVC full) не поднимутся.",
        "torch_directml": "AMD-ускорение отключится, будет CPU.",
        "demucs": "Стемов из референса не будет — только для анализа.",
        "whisper": "Транскрипции текстов референсов не будет.",
        "TTS": "XTTS-v2 клонирование недоступно, используем Silero/Bark.",
        "bark": "Bark speakers недоступны, используем Silero/pyttsx3.",
        "rvc_python": "RVC-инференс уходит в rvc_manager fallback (форки).",
    }
    return hint.get(probe.key)


def _collect_external_checks(report: HealthReport) -> bool:
    """Probe external dependencies and return whether a GUI backend is usable."""
    gui_group_ok = False
    for entry in CHECKS:
        probe = _probe(entry["mod"], entry["name"], entry["req"])
        report.externals.append(probe.as_dict())
        if entry.get("group") == "gui" and probe.ok:
            gui_group_ok = True
    return gui_group_ok


def _collect_internal_checks(report: HealthReport) -> None:
    """Probe internal project modules into the supplied report."""
    for module_path in INTERNAL_MODULES:
        report.internals.append(_probe(module_path, module_path, "internal").as_dict())


def _calculate_readiness(report: HealthReport, gui_group_ok: bool) -> None:
    """Apply the stable health-report weighting and verdict rules."""
    core_missing = [entry for entry in report.externals if entry["requirement"] == "core" and not entry["ok"]]
    quality_missing = [entry for entry in report.externals if entry["requirement"] == "quality" and not entry["ok"]]
    optional_all = [entry for entry in report.externals if entry["requirement"] == "optional"]
    optional_ok = [entry for entry in optional_all if entry["ok"]]
    quality_total = max(1, len([entry for entry in report.externals if entry["requirement"] == "quality"]))
    internal_total = max(1, len(report.internals))
    internal_ok = sum(1 for entry in report.internals if entry["ok"])

    report.core_ok = not core_missing and gui_group_ok
    report.quality_ok = not quality_missing
    report.optional_ok_count = len(optional_ok)
    report.optional_total = len(optional_all)
    core_score = 40 if report.core_ok else 0
    quality_score = int(30 * (1 - len(quality_missing) / quality_total))
    optional_score = int(15 * report.optional_ok_count / max(1, report.optional_total))
    internal_score = int(15 * internal_ok / internal_total)
    report.percent_ready = core_score + quality_score + optional_score + internal_score
    report.verdict = "RED" if not report.core_ok else (
        "YELLOW" if not report.quality_ok or report.percent_ready < 70 else "GREEN"
    )


def _append_advice(report: HealthReport) -> None:
    """Append actionable advice for unavailable external and internal components."""
    for entry in report.externals:
        if not entry["ok"]:
            advice = _advice_for(
                ProbeResult(
                    entry["key"], entry["name"], entry["requirement"], False,
                    None, entry.get("error"),
                )
            )
            if advice:
                report.advice.append(f"[{entry['requirement'].upper()}] {entry['name']}: {advice}")
    for entry in report.internals:
        if not entry["ok"]:
            report.advice.append(
                f"[INTERNAL] {entry['name']} не импортируется: {entry.get('error')}"
            )


def _write_report(report: HealthReport, save_to: Path) -> None:
    """Persist the report while preserving the existing non-fatal write policy."""
    try:
        save_to.parent.mkdir(parents=True, exist_ok=True)
        save_to.write_text(
            json.dumps(report.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:  # noqa: BLE001
        traceback.print_exc()


def collect(save_to: Path | None = None) -> HealthReport:
    """Collect dependency status, readiness scoring, advice and a persisted report."""
    report = HealthReport()
    report.generated_at_human = time.strftime(
        "%Y-%m-%d %H:%M:%S UTC", time.gmtime(report.generated_at)
    )
    report.platform = platform.platform()
    report.python = sys.version.split()[0]
    report.hw_profile = _hw_probe()
    gui_group_ok = _collect_external_checks(report)
    _collect_internal_checks(report)
    _calculate_readiness(report, gui_group_ok)
    _append_advice(report)
    _write_report(report, save_to or ROOT / "data" / "health.json")
    return report


# ---------------------------------------------------------------------------
#  5. CLI
# ---------------------------------------------------------------------------


def _fmt_row(name: str, ok: bool, ver: str | None, req: str) -> str:
    mark = "OK " if ok else "MISS"
    v = f"v{ver}" if ver else ""
    return f"  [{mark}] [{req:<8}] {name} {v}"


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    rep = collect()
    print("=" * 72)
    print("ZS Music Maker v12 — Health Check")
    print(f"Generated: {rep.generated_at_human}")
    print(f"Platform : {rep.platform}   Python: {rep.python}")
    print(
        f"HW mode  : {rep.hw_profile.get('mode', '?')}   "
        f"GPU: {rep.hw_profile.get('gpu', '?')}"
    )
    print("-" * 72)
    print("EXTERNAL DEPENDENCIES:")
    for e in rep.externals:
        print(_fmt_row(e["name"], e["ok"], e.get("version"), e["requirement"]))
    print("-" * 72)
    print("INTERNAL MODULES:")
    for e in rep.internals:
        print(_fmt_row(e["name"], e["ok"], None, e["requirement"]))
    print("-" * 72)
    print(
        f"VERDICT: {rep.verdict}  |  READY: {rep.percent_ready}%  |  "
        f"core_ok={rep.core_ok} quality_ok={rep.quality_ok}  "
        f"optional={rep.optional_ok_count}/{rep.optional_total}"
    )
    # v33 FIX (P0-UX, SESSION_LOG v31.2): RED почти всегда означает
    # отсутствие GUI (PySide6/Gradio) или quality-зависимостей, а НЕ
    # сломанное аудио-ядро. Без этого пояснения пользователь читал RED
    # как «продукт не работает», хотя beat→mix→mastering полностью живы.
    if rep.verdict == "RED":
        core_missing = [e["name"] for e in rep.externals
                        if e["requirement"] == "core" and not e["ok"]]
        gui_missing = [e["name"] for e in rep.externals
                       if e.get("requirement") == "core_alt" and not e["ok"]]
        if core_missing:
            print(f"  ! RED причина: отсутствует ЯДРО: {', '.join(core_missing)}")
        elif gui_missing:
            print(f"  ! RED причина: нет GUI-бэкенда ({', '.join(gui_missing)}).")
            print("    Аудио-ядро (beat/mix/mastering) при этом может быть полностью")
            print("    рабочим — проверь `python tools/smoke_god.py`. Установи GUI:")
            print("    `pip install PySide6` или `pip install gradio`.")
    if rep.advice:
        print("ADVICE:")
        for a in rep.advice[:20]:
            print(f"  - {a}")
    print("=" * 72)
    return 0 if rep.core_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
