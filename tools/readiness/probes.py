# -*- coding: utf-8 -*-
"""
tools/readiness/probes.py — пробы подсистем.

Каждая проба возвращает статус из фиксированного словаря
(`REAL_PASS` / `PARTIAL` / `BLOCKED` / `MISSING`). Отсутствие зависимости —
это `BLOCKED`/`MISSING`, а не «наверное, работает».
"""

from __future__ import annotations

from tools.readiness.paths import ROOT, TEST_ROOT


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
        ("lyrics", "modules.lyrics"),
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
        "REAL_PASS" if _module_exists("modules.mastering_reference") else "MISSING"
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
        "REAL_PASS" if _module_exists("modules.release.export") else "MISSING"
    )
    p["release_pack"] = (
        "REAL_PASS" if _module_exists("modules.release.pack") else "MISSING"
    )
    p["distribution"] = (
        "REAL_PASS" if _module_exists("modules.release.channels") else "MISSING"
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
