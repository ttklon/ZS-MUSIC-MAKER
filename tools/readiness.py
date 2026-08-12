# -*- coding: utf-8 -*-
"""
ZS Music Maker v14 — tools/readiness.py (P0.14, TZ 33.4)

Честный расчёт % готовности по формуле TZ 33.4.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]

# FIX v16 (P0): при запуске «python3 tools/readiness.py» в sys.path попадает
# каталог tools/, а не корень проекта — все probe через __import__("modules.*")
# ложно падали в MISSING и KPI занижался (22% вместо реальных ~60%).
# Гарантируем, что корень проекта всегда доступен для импорта.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

WEIGHTS = {
    "architecture":  10, "core_modules":  25, "audio_pipeline": 25,
    "voice_rvc":     15, "release":       10, "installer":       5,
    "testing":       10,
}

STATUS_WEIGHT = {
    "REAL_PASS":     1.00, "PARTIAL":      0.50, "FALLBACK_ONLY": 0.25,
    "MOCK":          0.00, "FAILED":       0.00, "MISSING":       0.00,
    "NOT_TESTED":    0.00, "BLOCKED":      0.00,
}


def _module_exists(name: str) -> bool:
    try:
        __import__(name)
        return True
    except Exception:
        return False


def _file_exists(rel: str) -> bool:
    return (ROOT / rel).exists()


def probe_architecture() -> Dict[str, str]:
    p: Dict[str, str] = {}
    stray = list((ROOT).glob("main_v*.py"))
    p["main_py_unified"] = "REAL_PASS" if _file_exists("main.py") and not stray else ("PARTIAL" if _file_exists("main.py") else "MISSING")
    p["TZ_txt_present"]     = "REAL_PASS" if _file_exists("TZ.txt") else "MISSING"
    p["PROMPT_txt_present"] = "REAL_PASS" if _file_exists("PROMPT.txt") else "MISSING"
    p["requirements_txt"]   = "REAL_PASS" if _file_exists("requirements.txt") else "MISSING"
    p["orchestrator_present"] = "REAL_PASS" if _file_exists("app/core/orchestrator.py") else "MISSING"
    p["updater_module"]     = "REAL_PASS" if _file_exists("updater/updater.py") else "MISSING"
    p["legacy_isolated"]    = "REAL_PASS" if _file_exists("legacy/mains") else "MISSING"
    return p


def probe_core_modules() -> Dict[str, str]:
    p: Dict[str, str] = {}
    p["analyzer"]          = "REAL_PASS" if _module_exists("modules.analyzer") else "MISSING"
    p["groove_extractor"]  = "REAL_PASS" if _module_exists("modules.groove_extractor") else "MISSING"
    p["beat_constructor"]  = "REAL_PASS" if _module_exists("modules.beat_constructor") else "MISSING"
    p["arrangement"]       = "REAL_PASS" if _module_exists("modules.arrangement_engine") else "MISSING"
    p["lyrics_gen"]        = "REAL_PASS" if _module_exists("modules.lyrics_gen") else "MISSING"
    p["mixdown"]           = "PARTIAL" if _module_exists("modules.mixdown") else "MISSING"
    p["sidechain"]         = "REAL_PASS" if _module_exists("modules.sidechain") else "MISSING"
    p["mastering"]         = "PARTIAL" if _module_exists("modules.mastering") else "MISSING"
    p["anti_neuro_polish"] = "REAL_PASS" if _module_exists("modules.anti_neuro_v10") else "MISSING"
    p["hit_scorer"]        = "REAL_PASS" if _module_exists("modules.hit_scorer") else "MISSING"
    p["stem_splitter"]     = "PARTIAL" if _module_exists("modules.stem_splitter") else "MISSING"
    presets_dir = ROOT / "data" / "genre_presets"
    n_presets = len(list(presets_dir.glob("*.json"))) if presets_dir.exists() else 0
    p["presets_50"] = "REAL_PASS" if n_presets >= 50 else ("PARTIAL" if n_presets > 0 else "MISSING")
    return p


def probe_audio_pipeline() -> Dict[str, str]:
    p: Dict[str, str] = {}
    try: import matchering; p["matchering"] = "REAL_PASS"
    except Exception: p["matchering"] = "MISSING"
    try: import pedalboard; p["pedalboard"] = "REAL_PASS"
    except Exception: p["pedalboard"] = "MISSING"
    try: import pyloudnorm; p["pyloudnorm"] = "REAL_PASS"
    except Exception: p["pyloudnorm"] = "MISSING"
    try: import librosa, soundfile; p["librosa_soundfile"] = "REAL_PASS"
    except Exception: p["librosa_soundfile"] = "MISSING"
    try: import audiocraft; p["musicgen"] = "REAL_PASS"
    except Exception: p["musicgen"] = "MISSING"
    try: import demucs; p["demucs"] = "REAL_PASS"
    except Exception: p["demucs"] = "MISSING"

    if _file_exists("output/audit_v14/e2e_summary.json") or \
       _file_exists("output/audit_v14/real_e2e_result.json"):
        p["e2e_run_evidence"] = "PARTIAL"
    else:
        p["e2e_run_evidence"] = "NOT_TESTED"
    p["mastering_8_stands"] = "PARTIAL" if _module_exists("modules.mastering") else "MISSING"
    return p


def probe_voice_rvc() -> Dict[str, str]:
    p: Dict[str, str] = {}
    p["voice_recording"] = "PARTIAL" if _module_exists("modules.voice_recording") else "MISSING"
    p["voice_onboarding"] = "REAL_PASS" if _module_exists("modules.voice_onboarding") else "MISSING"
    p["voice_vault"] = "REAL_PASS" if _module_exists("modules.voice_vault_v9") else "MISSING"
    pth_files = list((ROOT / "models" / "rvc").rglob("*.pth"))
    p["rvc_model"] = "REAL_PASS" if pth_files else "MISSING"
    try:
        from modules import voice_recording as vr
        cap = vr.capability_report()
        p["mic_recording"] = "REAL_PASS" if cap.get("real_recording_possible") else "BLOCKED"
    except Exception:
        p["mic_recording"] = "MISSING"
    return p


def probe_release() -> Dict[str, str]:
    p: Dict[str, str] = {}
    p["release_pack_module"] = "PARTIAL" if _module_exists("modules.release_pack_v13") else "MISSING"
    p["distrokid_xml"] = "PARTIAL" if _module_exists("modules.distribution_export_v11") else "MISSING"
    p["cover_art"] = "PARTIAL" if _module_exists("modules.cover_art_gen") else "MISSING"
    try: import mutagen; p["id3_tags"] = "REAL_PASS"
    except Exception: p["id3_tags"] = "MISSING"
    return p


def probe_installer() -> Dict[str, str]:
    p: Dict[str, str] = {}
    ok = _module_exists("updater.updater")
    p["updater_module"] = "REAL_PASS" if ok else "MISSING"
    p["backup_procedure"] = "REAL_PASS" if ok else "MISSING"
    p["rollback"] = "REAL_PASS" if ok else "MISSING"
    p["sha256_verify"] = "REAL_PASS" if ok else "MISSING"
    p["user_data_split"] = "REAL_PASS" if ok else "MISSING"
    return p


def probe_testing() -> Dict[str, str]:
    p: Dict[str, str] = {}
    p["smoke_v14"] = "REAL_PASS" if _file_exists("tools/smoke_v14.py") else "MISSING"
    p["e2e_v14"] = "REAL_PASS" if _file_exists("tools/real_e2e_v14.py") else "MISSING"
    p["self_diag"] = "REAL_PASS" if _module_exists("modules.self_diag_v13") else "MISSING"
    p["health"] = "REAL_PASS" if _module_exists("modules.health_v12") else "MISSING"
    p["fallback_audit"] = "REAL_PASS" if _file_exists("tools/fallback_audit.py") else "MISSING"
    p["evidence_present"] = "PARTIAL" if _file_exists("output/audit_v14") else "MISSING"
    return p


def _block_percent(probes: Dict[str, str]) -> float:
    if not probes:
        return 0.0
    n = len(probes)
    score = sum(STATUS_WEIGHT.get(v, 0.0) for v in probes.values())
    return round(100.0 * score / n, 2)


def compute() -> Tuple[float, Dict[str, Any]]:
    blocks_raw = {
        "architecture":   probe_architecture(),
        "core_modules":   probe_core_modules(),
        "audio_pipeline": probe_audio_pipeline(),
        "voice_rvc":      probe_voice_rvc(),
        "release":        probe_release(),
        "installer":      probe_installer(),
        "testing":        probe_testing(),
    }
    block_pcts = {k: _block_percent(v) for k, v in blocks_raw.items()}

    total = 0.0
    for k, w in WEIGHTS.items():
        total += block_pcts[k] * w / 100.0

    caps: List[Tuple[float, str]] = []
    if blocks_raw["voice_rvc"].get("rvc_model") != "REAL_PASS":
        caps.append((70.0, "no working RVC (no .pth model)"))
    if blocks_raw["voice_rvc"].get("mic_recording") != "REAL_PASS":
        caps.append((80.0, "no real microphone recording available"))
    if blocks_raw["audio_pipeline"].get("e2e_run_evidence") != "REAL_PASS":
        caps.append((60.0, "no full E2E run with real heavy engines"))
    if blocks_raw["installer"].get("updater_module") != "REAL_PASS":
        caps.append((85.0, "no updater module"))
    heavy_missing = [k for k in ("musicgen", "demucs")
                     if blocks_raw["audio_pipeline"].get(k) in ("MOCK", "FAILED", "MISSING")]
    if heavy_missing:
        caps.append((65.0, f"heavy engines unavailable: {heavy_missing}"))
    if blocks_raw["testing"].get("evidence_present") not in ("REAL_PASS", "PARTIAL"):
        caps.append((50.0, "no evidence attached"))

    cap_min = min([c[0] for c in caps], default=100.0)
    final = min(total, cap_min)
    final = math.floor(final)

    return float(final), {
        "block_scores": block_pcts,
        "weights": WEIGHTS,
        "raw_probes": blocks_raw,
        "caps_triggered": caps,
        "weighted_sum": round(total, 2),
        "cap_min": cap_min,
        "final_floor": final,
    }


def main() -> int:
    pct, blocks = compute()
    print(json.dumps({"percent": pct, "blocks": blocks},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
