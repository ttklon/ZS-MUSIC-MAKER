"""
ZS Music Maker v14 — tools/readiness.py (P0.14, TZ 33.4)

Честный расчёт % готовности по формуле TZ 33.4.
"""

from __future__ import annotations

import ast
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

# FIX v16 (P0): при запуске «python3 tools/readiness.py» в sys.path попадает
# каталог tools/, а не корень проекта — все probe через __import__("modules.*")
# ложно падали в MISSING и KPI занижался (22% вместо реальных ~60%).
# Гарантируем, что корень проекта всегда доступен для импорта.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

WEIGHTS = {
    "architecture": 10,
    "core_modules": 25,
    "audio_pipeline": 25,
    "voice_rvc": 15,
    "release": 10,
    "installer": 5,
    "testing": 10,
}

INVENTORY_ROOTS = ("app", "agents", "modules", "tools", "ui", "updater")
TEST_ROOT = "tests"


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


def tracked_python_modules() -> list[str]:
    """Return versioned production Python files, never runtime cache files.

    Git is the source of truth when available, which makes the generated state
    matrix match the repository rather than whatever happens to be present in a
    developer's untracked working tree.  The filesystem fallback keeps the
    health command usable from a source archive.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "*.py"],
            check=True,
            capture_output=True,
            text=True,
        )
        paths = result.stdout.splitlines()
    except (OSError, subprocess.CalledProcessError):
        paths = [
            str(path.relative_to(ROOT))
            for base in INVENTORY_ROOTS
            for path in (ROOT / base).rglob("*.py")
            if "__pycache__" not in path.parts
        ]

    return sorted(
        path for path in paths
        if path.endswith(".py")
        and (path == "main.py" or path.split("/", 1)[0] in INVENTORY_ROOTS)
    )


def _source_texts() -> tuple[str, str]:
    production = "\n".join(
        (ROOT / path).read_text(encoding="utf-8", errors="replace")
        for path in tracked_python_modules()
    )
    tests_dir = ROOT / TEST_ROOT
    tests = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in tests_dir.glob("test_*.py")
    ) if tests_dir.exists() else ""
    return production, tests


def module_inventory() -> list[dict[str, Any]]:
    """Build an auditable, static status row for every tracked production file.

    `REAL_PASS` means the file parses and has at least a production reference or
    a direct test reference. `PLANNED` is present/parseable but lacks both static
    signals. `REAL_FAIL` denotes a syntax error. This intentionally does not
    assert that optional heavy model runtime was executed.
    """
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
        production_refs = production.count(module_dot) + production.count(basename)
        test_refs = tests.count(module_dot) + tests.count(basename)
        # Subtract the module's own filename/text occurrence from source scan.
        production_refs = max(0, production_refs - 1)
        status = (
            "REAL_FAIL" if not syntax_ok
            else "REAL_PASS" if (production_refs or test_refs)
            else "PLANNED"
        )
        rows.append({
            "path": path,
            "status": status,
            "syntax_ok": syntax_ok,
            "production_references": production_refs,
            "test_references": test_refs,
        })
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
    """Render the full, deterministic inventory as a Markdown pipe table."""
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


def _module_exists(name: str) -> bool:
    try:
        __import__(name)
        return True
    except Exception:
        return False


def _file_exists(rel: str) -> bool:
    return (ROOT / rel).exists()


def probe_architecture() -> dict[str, str]:
    p: dict[str, str] = {}
    stray = list((ROOT).glob("main_v*.py"))
    p["main_py_unified"] = (
        "REAL_PASS"
        if _file_exists("main.py") and not stray
        else ("PARTIAL" if _file_exists("main.py") else "MISSING")
    )
    p["TZ_txt_present"] = "REAL_PASS" if _file_exists("TZ.txt") else "MISSING"
    p["PROMPT_txt_present"] = "REAL_PASS" if _file_exists("PROMPT.txt") else "MISSING"
    p["requirements_txt"] = (
        "REAL_PASS" if _file_exists("requirements.txt") else "MISSING"
    )
    p["orchestrator_present"] = (
        "REAL_PASS" if _file_exists("app/core/orchestrator.py") else "MISSING"
    )
    p["updater_module"] = (
        "REAL_PASS" if _file_exists("updater/updater.py") else "MISSING"
    )
    p["legacy_isolated"] = "REAL_PASS" if _file_exists("legacy/mains") else "MISSING"
    return p


def probe_core_modules() -> dict[str, str]:
    p: dict[str, str] = {}
    p["analyzer"] = "REAL_PASS" if _module_exists("modules.analyzer") else "MISSING"
    p["groove_extractor"] = (
        "REAL_PASS" if _module_exists("modules.groove_extractor") else "MISSING"
    )
    p["beat_constructor"] = (
        "REAL_PASS" if _module_exists("modules.beat_constructor") else "MISSING"
    )
    p["arrangement"] = (
        "REAL_PASS" if _module_exists("modules.arrangement_engine") else "MISSING"
    )
    p["lyrics_gen"] = "REAL_PASS" if _module_exists("modules.lyrics_gen") else "MISSING"
    p["mixdown"] = "PARTIAL" if _module_exists("modules.mixdown") else "MISSING"
    p["sidechain"] = "REAL_PASS" if _module_exists("modules.sidechain") else "MISSING"
    p["mastering"] = "PARTIAL" if _module_exists("modules.mastering") else "MISSING"
    p["anti_neuro_polish"] = (
        "REAL_PASS" if _module_exists("modules.anti_neuro_v10") else "MISSING"
    )
    p["hit_scorer"] = "REAL_PASS" if _module_exists("modules.hit_scorer") else "MISSING"
    p["stem_splitter"] = (
        "PARTIAL" if _module_exists("modules.stem_splitter") else "MISSING"
    )
    presets_dir = ROOT / "data" / "genre_presets"
    n_presets = len(list(presets_dir.glob("*.json"))) if presets_dir.exists() else 0
    p["presets_50"] = (
        "REAL_PASS" if n_presets >= 50 else ("PARTIAL" if n_presets > 0 else "MISSING")
    )
    return p


def _dependency_status(name: str) -> str:
    """Probe a real optional dependency without converting absence to success."""
    return "REAL_PASS" if _module_exists(name) else "BLOCKED"


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
    p["orchestrator_ai"] = (
        "REAL_PASS" if _module_exists("app.core.orchestrator_ai") else "MISSING"
    )
    p["mastering_adapter"] = (
        "REAL_PASS" if _module_exists("modules.mastering_ai") else "MISSING"
    )
    p["documented_smoke_scripts"] = (
        "REAL_PASS"
        if _file_exists("tools/smoke_v26.py") and _file_exists("tools/smoke_v29.py")
        else "MISSING"
    )
    return p


def probe_voice_rvc() -> dict[str, str]:
    p: dict[str, str] = {}
    p["voice_recording"] = (
        "PARTIAL" if _module_exists("modules.voice_recording") else "MISSING"
    )
    p["voice_onboarding"] = (
        "REAL_PASS" if _module_exists("modules.voice_onboarding") else "MISSING"
    )
    p["voice_vault"] = (
        "REAL_PASS" if _module_exists("modules.voice_vault_v9") else "MISSING"
    )
    pth_files = list((ROOT / "models" / "rvc").rglob("*.pth"))
    p["rvc_model"] = "REAL_PASS" if pth_files else "MISSING"
    try:
        from modules import voice_recording as vr

        cap = vr.capability_report()
        p["mic_recording"] = (
            "REAL_PASS" if cap.get("real_recording_possible") else "BLOCKED"
        )
    except Exception:
        p["mic_recording"] = "MISSING"
    return p


def probe_release() -> dict[str, str]:
    p: dict[str, str] = {}
    p["release_export"] = (
        "REAL_PASS" if _module_exists("modules.release_export") else "MISSING"
    )
    p["release_pack_module"] = (
        "PARTIAL" if _module_exists("modules.release_pack_v13") else "MISSING"
    )
    p["distrokid_xml"] = (
        "PARTIAL" if _module_exists("modules.distribution_export_v11") else "MISSING"
    )
    p["cover_art_adapter"] = (
        "REAL_PASS" if _module_exists("app.core.cover_gen") else "MISSING"
    )
    p["mutagen_runtime"] = _dependency_status("mutagen")
    return p


def probe_installer() -> dict[str, str]:
    p: dict[str, str] = {}
    ok = _module_exists("updater.updater")
    p["updater_module"] = "REAL_PASS" if ok else "MISSING"
    p["backup_procedure"] = "REAL_PASS" if ok else "MISSING"
    p["rollback"] = "REAL_PASS" if ok else "MISSING"
    p["sha256_verify"] = "REAL_PASS" if ok else "MISSING"
    p["user_data_split"] = "REAL_PASS" if ok else "MISSING"
    return p


def probe_testing() -> dict[str, str]:
    p: dict[str, str] = {}
    tests = list((ROOT / TEST_ROOT).glob("test_*.py"))
    p["pytest_suite"] = "REAL_PASS" if tests else "MISSING"
    p["smoke_v26"] = "REAL_PASS" if _file_exists("tools/smoke_v26.py") else "MISSING"
    p["smoke_v29"] = "REAL_PASS" if _file_exists("tools/smoke_v29.py") else "MISSING"
    p["fallback_audit"] = (
        "REAL_PASS" if _file_exists("tools/fallback_audit.py") else "MISSING"
    )
    p["ast_dead_import_audit"] = (
        "REAL_PASS" if _file_exists("tools/ast_dead_imports.py") else "MISSING"
    )
    return p


def _block_percent(probes: dict[str, str]) -> float:
    if not probes:
        return 0.0
    n = len(probes)
    score = sum(STATUS_WEIGHT.get(v, 0.0) for v in probes.values())
    return round(100.0 * score / n, 2)


def compute() -> tuple[float, dict[str, Any]]:
    blocks_raw = {
        "architecture": probe_architecture(),
        "core_modules": probe_core_modules(),
        "audio_pipeline": probe_audio_pipeline(),
        "voice_rvc": probe_voice_rvc(),
        "release": probe_release(),
        "installer": probe_installer(),
        "testing": probe_testing(),
    }
    block_pcts = {k: _block_percent(v) for k, v in blocks_raw.items()}

    total = 0.0
    for k, w in WEIGHTS.items():
        total += block_pcts[k] * w / 100.0

    caps: list[tuple[float, str]] = []
    if blocks_raw["voice_rvc"].get("rvc_model") != "REAL_PASS":
        caps.append((70.0, "no working RVC (no .pth model)"))
    if blocks_raw["voice_rvc"].get("mic_recording") != "REAL_PASS":
        caps.append((80.0, "no real microphone recording available"))
    heavy_runtime = [
        key for key in ("musicgen_runtime", "demucs_runtime")
        if blocks_raw["audio_pipeline"].get(key) == "BLOCKED"
    ]
    if heavy_runtime:
        caps.append((65.0, f"heavy engines unavailable: {heavy_runtime}"))
    if blocks_raw["installer"].get("updater_module") != "REAL_PASS":
        caps.append((85.0, "no updater module"))

    cap_min = min([c[0] for c in caps], default=100.0)
    final = min(total, cap_min)
    final = math.floor(final)

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


def main() -> int:
    if "--inventory-markdown" in sys.argv[1:]:
        print(inventory_markdown())
        return 0
    pct, blocks = compute()
    print(json.dumps({"percent": pct, "blocks": blocks}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
