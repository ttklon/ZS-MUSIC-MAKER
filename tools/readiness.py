"""
ZS Music Maker — tools/readiness.py

Честный расчёт готовности: статическая матрица модулей + проверка того, что
реально установлено, без превращения отсутствия зависимости в успех.

Использование:
    python tools/readiness.py                  # JSON: percent + blocks
    python tools/readiness.py --inventory-markdown
    python tools/readiness.py --json

`REAL_PASS` в матрице означает «файл парсится и на него есть статическая
ссылка из production или тестов», а НЕ утверждение о реальном inference.
"""

from __future__ import annotations

import argparse
import ast
import json
import math
import sys
from importlib import metadata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

INVENTORY_ROOTS = ("app", "agents", "config", "modules", "tools", "ui", "updater")
TEST_ROOT = "tests"

WEIGHTS = {
    "architecture": 10,
    "core_modules": 25,
    "audio_pipeline": 25,
    "voice_recording": 20,
    "release": 10,
    "testing": 10,
}

STATUS_WEIGHT = {
    "REAL_PASS": 1.00,
    "PARTIAL": 0.50,
    "FALLBACK_ONLY": 0.25,
    "MOCK": 0.00,
    "FAILED": 0.00,
    "MISSING": 0.00,
    "NOT_TESTED": 0.00,
    "BLOCKED": 0.00,
}


# --------------------------------------------------------------------------- #
#  Инвентаризация версионированного дерева
# --------------------------------------------------------------------------- #
def tracked_python_modules() -> list[str]:
    """Return tracked production Python files (git if available, else filesystem)."""
    try:
        import subprocess

        out = subprocess.run(
            ["git", "ls-files", "*.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        if out.returncode == 0 and out.stdout.strip():
            paths = []
            for line in out.stdout.splitlines():
                rel = line.strip()
                if not rel or rel.startswith(TEST_ROOT + "/"):
                    continue
                top = rel.split("/", 1)[0]
                # root-level entrypoints (main.py, install.py) и пакеты из ROOTS
                if "/" not in rel or top in INVENTORY_ROOTS:
                    paths.append(rel)
            return sorted(paths)
    except Exception:  # pragma: no cover - git отсутствует
        pass
    paths = ["main.py"] if (ROOT / "main.py").exists() else []
    for root in INVENTORY_ROOTS:
        base = ROOT / root
        if not base.exists():
            continue
        paths.extend(str(p.relative_to(ROOT)) for p in base.rglob("*.py"))
    return sorted(paths)


def _source_texts() -> tuple[str, str]:
    production = "\n".join(
        (ROOT / path).read_text(encoding="utf-8", errors="replace")
        for path in tracked_python_modules()
    )
    tests_dir = ROOT / TEST_ROOT
    tests = (
        "\n".join(
            p.read_text(encoding="utf-8", errors="replace")
            for p in tests_dir.glob("test_*.py")
        )
        if tests_dir.exists()
        else ""
    )
    return production, tests


def module_inventory() -> list[dict[str, Any]]:
    """Одна аудиторская строка на каждый версионированный production-модуль."""
    production, tests = _source_texts()
    rows: list[dict[str, Any]] = []
    for path in tracked_python_modules():
        source = (ROOT / path).read_text(encoding="utf-8", errors="replace")
        module_dot = path[:-3].replace("/", ".")
        basename = Path(path).stem
        try:
            ast.parse(source, filename=path)
            syntax_ok = True
        except SyntaxError:
            syntax_ok = False
        production_refs = max(0, production.count(module_dot) + production.count(basename) - 1)
        test_refs = tests.count(module_dot) + tests.count(basename)
        status = (
            "REAL_FAIL"
            if not syntax_ok
            else "REAL_PASS"
            if (production_refs or test_refs)
            else "PLANNED"
        )
        rows.append(
            {
                "path": path,
                "status": status,
                "syntax_ok": syntax_ok,
                "production_references": production_refs,
                "test_references": test_refs,
            }
        )
    return rows


def module_inventory_summary() -> dict[str, int]:
    rows = module_inventory()
    return {
        "tracked_modules": len(rows),
        "REAL_PASS": sum(row["status"] == "REAL_PASS" for row in rows),
        "REAL_FAIL": sum(row["status"] == "REAL_FAIL" for row in rows),
        "PLANNED": sum(row["status"] == "PLANNED" for row in rows),
    }


def inventory_markdown() -> str:
    lines = [
        "| Versioned module | Status | AST syntax | Production refs | Test refs |",
        "|---|---|---:|---:|---:|",
    ]
    for row in module_inventory():
        lines.append(
            "| {path} | {status} | {syntax} | {production} | {tests} |".format(
                path=row["path"],
                status=row["status"],
                syntax="PASS" if row["syntax_ok"] else "FAIL",
                production=row["production_references"],
                tests=row["test_references"],
            )
        )
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
#  Пробы
# --------------------------------------------------------------------------- #
def _module_exists(name: str) -> bool:
    try:
        __import__(name)
        return True
    except Exception:
        return False


def _file_exists(rel: str) -> bool:
    return (ROOT / rel).exists()


def _dependency_status(name: str) -> str:
    return "REAL_PASS" if _module_exists(name) else "BLOCKED"


def probe_architecture() -> dict[str, str]:
    p: dict[str, str] = {}
    p["main_py_unified"] = (
        "REAL_PASS"
        if _file_exists("main.py") and not list(ROOT.glob("main_v*.py"))
        else ("PARTIAL" if _file_exists("main.py") else "MISSING")
    )
    p["requirements_txt"] = "REAL_PASS" if _file_exists("requirements.txt") else "MISSING"
    p["orchestrator_present"] = (
        "REAL_PASS" if _file_exists("app/core/orchestrator.py") else "MISSING"
    )
    p["ai_pipeline"] = (
        "REAL_PASS" if _file_exists("app/core/orchestrator_ai.py") else "MISSING"
    )
    p["updater_module"] = "REAL_PASS" if _file_exists("updater/updater.py") else "MISSING"
    p["single_pipeline"] = (
        "REAL_PASS"
        if len(list((ROOT / "app" / "core").glob("orchestrator*.py"))) <= 4
        else "PARTIAL"
    )
    return p


def probe_core_modules() -> dict[str, str]:
    p: dict[str, str] = {}
    for key, module in (
        ("analyzer", "modules.analyzer"),
        ("groove_extractor", "modules.groove_extractor"),
        ("beat_constructor", "modules.beat_constructor"),
        ("arrangement", "modules.arrangement_engine"),
        ("lyrics_gen", "modules.lyrics_gen"),
        ("sidechain", "modules.sidechain"),
        ("anti_neuro", "modules.anti_neuro"),
        ("hit_scorer", "modules.hit_scorer"),
    ):
        p[key] = "REAL_PASS" if _module_exists(module) else "MISSING"
    p["mastering"] = "REAL_PASS" if _module_exists("modules.mastering") else "MISSING"
    p["stem_splitter"] = "PARTIAL" if _module_exists("modules.stem_splitter") else "MISSING"
    presets_dir = ROOT / "data" / "genre_presets"
    n_presets = len(list(presets_dir.glob("*.json"))) if presets_dir.exists() else 0
    p["presets_library"] = (
        "REAL_PASS" if n_presets >= 50 else ("PARTIAL" if n_presets else "MISSING")
    )
    return p


def probe_audio_pipeline() -> dict[str, str]:
    p: dict[str, str] = {}
    p["matchering_runtime"] = _dependency_status("matchering")
    p["pedalboard_runtime"] = _dependency_status("pedalboard")
    p["pyloudnorm_runtime"] = _dependency_status("pyloudnorm")
    p["librosa_soundfile_runtime"] = (
        "REAL_PASS"
        if _module_exists("librosa") and _module_exists("soundfile")
        else "BLOCKED"
    )
    p["musicgen_runtime"] = _dependency_status("audiocraft")
    p["demucs_runtime"] = _dependency_status("demucs")
    p["mastering_adapter"] = (
        "REAL_PASS" if _module_exists("modules.mastering_ai") else "MISSING"
    )
    p["smoke_scripts"] = (
        "REAL_PASS"
        if _file_exists("tools/smoke_audio.py") and _file_exists("tools/smoke_god.py")
        else "MISSING"
    )
    return p


def probe_voice_recording() -> dict[str, str]:
    """Голос — основной путь релиза, поэтому проба честная: микрофон + vault."""
    p: dict[str, str] = {}
    p["voice_recording"] = (
        "REAL_PASS" if _module_exists("modules.voice_recording") else "MISSING"
    )
    p["voice_vault"] = "REAL_PASS" if _module_exists("modules.voice_vault") else "MISSING"
    p["voice_onboarding"] = (
        "REAL_PASS" if _module_exists("modules.voice_onboarding") else "MISSING"
    )
    p["voice_cleaner"] = "REAL_PASS" if _module_exists("modules.voice_cleaner") else "MISSING"
    p["vocal_fx"] = "REAL_PASS" if _module_exists("modules.vocal_fx") else "MISSING"
    p["rvc_model"] = (
        "REAL_PASS" if list((ROOT / "models" / "rvc").rglob("*.pth")) else "MISSING"
    )
    try:
        from modules import voice_recording as vr

        cap = vr.capability_report()
        p["mic_recording"] = "REAL_PASS" if cap.get("real_recording_possible") else "BLOCKED"
    except Exception:
        p["mic_recording"] = "MISSING"
    return p


def probe_release() -> dict[str, str]:
    p: dict[str, str] = {}
    p["release_export"] = (
        "REAL_PASS" if _module_exists("modules.release_export") else "MISSING"
    )
    p["release_pack"] = (
        "REAL_PASS" if _module_exists("modules.release_pack_full") else "MISSING"
    )
    p["distribution"] = (
        "REAL_PASS" if _module_exists("modules.distribution") else "MISSING"
    )
    p["cover_art"] = (
        "REAL_PASS" if _module_exists("modules.cover_art_gen") else "MISSING"
    )
    p["mutagen_runtime"] = _dependency_status("mutagen")
    return p


def probe_testing() -> dict[str, str]:
    p: dict[str, str] = {}
    tests = list((ROOT / TEST_ROOT).glob("test_*.py"))
    p["pytest_suite"] = "REAL_PASS" if tests else "MISSING"
    p["fallback_audit"] = (
        "REAL_PASS" if _file_exists("tools/fallback_audit.py") else "MISSING"
    )
    p["dead_import_audit"] = (
        "REAL_PASS" if _file_exists("tools/ast_dead_imports.py") else "MISSING"
    )
    p["data_audit"] = (
        "REAL_PASS" if _file_exists("tools/audit_data_inventory.py") else "MISSING"
    )
    return p


def _block_percent(probes: dict[str, str]) -> float:
    if not probes:
        return 0.0
    score = sum(STATUS_WEIGHT.get(v, 0.0) for v in probes.values())
    return round(100.0 * score / len(probes), 2)


def compute() -> tuple[float, dict[str, Any]]:
    blocks_raw = {
        "architecture": probe_architecture(),
        "core_modules": probe_core_modules(),
        "audio_pipeline": probe_audio_pipeline(),
        "voice_recording": probe_voice_recording(),
        "release": probe_release(),
        "testing": probe_testing(),
    }
    block_pcts = {key: _block_percent(value) for key, value in blocks_raw.items()}

    total = 0.0
    for key, weight in WEIGHTS.items():
        total += block_pcts.get(key, 0.0) * weight / 100.0

    caps: list[tuple[float, str]] = []
    if blocks_raw["voice_recording"].get("mic_recording") != "REAL_PASS":
        caps.append((80.0, "no real microphone recording available"))
    heavy = [
        key
        for key in ("musicgen_runtime", "demucs_runtime")
        if blocks_raw["audio_pipeline"].get(key) == "BLOCKED"
    ]
    if heavy:
        caps.append((65.0, f"heavy engines unavailable: {heavy}"))
    if blocks_raw["architecture"].get("updater_module") != "REAL_PASS":
        caps.append((85.0, "no updater module"))

    cap_min = min([cap[0] for cap in caps], default=100.0)
    final = math.floor(min(total, cap_min))

    return float(final), {
        "module_inventory": module_inventory_summary(),
        "block_scores": block_pcts,
        "weights": WEIGHTS,
        "raw_probes": blocks_raw,
        "caps_triggered": caps,
        "weighted_sum": round(total, 2),
        "cap_min": cap_min,
        "final_floor": final,
    }


def dependency_requirements() -> list[dict[str, str]]:
    """Разбирает манифесты зависимостей без их резолва (для отчётов)."""
    groups = (
        ("base", ROOT / "requirements.txt"),
        ("optional-ai", ROOT / "requirements_ai.txt"),
    )
    entries: dict[str, dict[str, str]] = {}
    for group, path in groups:
        if not path.exists():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("git+"):
                name = "bark" if "suno-ai/bark" in line.lower() else line.rsplit("/", 1)[-1]
            else:
                name = line.split(";")[0].split(">=")[0].split("==")[0].split("<")[0].strip()
            entries[name] = {"group": group, "spec": line}
    return [{"name": name, **spec} for name, spec in sorted(entries.items())]


def installed_version(package: str) -> str:
    try:
        return metadata.version(package)
    except Exception:
        return ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compute factual ZS Music Maker readiness")
    parser.add_argument(
        "--inventory-markdown",
        action="store_true",
        help="render the tracked Python module matrix as Markdown",
    )
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    if args.inventory_markdown:
        print(inventory_markdown())
        return 0

    percent, details = compute()
    if args.json:
        print(json.dumps({"percent": percent, **details}, ensure_ascii=False, indent=2))
        return 0

    print(f"readiness: {percent:.0f}%")
    for block, value in details["block_scores"].items():
        print(f"  {block:18s} {value:6.2f}%")
    for cap_value, reason in details["caps_triggered"]:
        print(f"  cap <= {cap_value:.0f}%: {reason}")
    missing = [row["path"] for row in module_inventory() if row["status"] != "REAL_PASS"]
    if missing:
        print("  modules without static signal: " + ", ".join(missing))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
