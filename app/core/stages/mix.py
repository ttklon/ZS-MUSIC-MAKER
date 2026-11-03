# -*- coding: utf-8 -*-
"""app/core/stages/mix.py — стадия микса: бит + вокал → шина с отчётом.

Раньше DSP жил прямо в этой стадии (HP на вокале, «дак всего микса», ручной
пик-трим) и расходился с мастерингом. Теперь вся работа — в `modules.mix.bus`:
gain staging −18 dBFS, канальный EQ вокала, сайдчейн kick → низ, mid/side
ширина и гейты §7.2. Стадия только готовит пути и переводит отчёт в контракт
пайплайна.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _stage_mix_and_sidechain(
    beat_wav: str, voice_wav: str | None, out_dir: Path, reference_wav: str | list[str] | None = None,
    vocal_offset_ms: int = 0,
) -> dict[str, Any]:
    """Собрать микс штатным микшером и вернуть измеренный отчёт."""
    try:
        from modules.mix.bus import prepare_mix

        result = prepare_mix(beat_wav, voice_wav, out_dir, vocal_offset_ms=vocal_offset_ms)
    except Exception as exc:  # noqa: BLE001 - стадия обязана вернуть причину, не падать
        return {"ok": False, "reason": f"{type(exc).__name__}: {exc}"}

    if not result.get("ok"):
        return {"ok": False, "reason": result.get("reason", "mix failed")}

    out_wav = result.get("out_wav")
    if not out_wav or not Path(out_wav).exists():
        return {"ok": False, "reason": "mix produced no output file"}

    reference_report: dict[str, Any] | None = None
    report = dict(result.get("report") or {})
    gates = dict(result.get("gates") or {})
    pre_reference = None
    fallback_used = False
    fallback_reason = None
    if reference_wav:
        # Try the full correction, then smaller bounded corrections. Never
        # accept a candidate that breaks a previously passing mix gate or
        # worsens the measured worst reference-band deviation.
        attempts = []
        for strength in (1.0, 0.5, 0.25, 0.125):
            try:
                from modules.mix.reference import match_to_reference

                reference_report = match_to_reference(
                    out_wav, reference_wav, str(Path(out_dir) / "mix_matched.wav"), strength=strength
                )
            except Exception as exc:  # noqa: BLE001 - expose matching failure
                reference_report = {"ok": False, "reason": f"{type(exc).__name__}: {exc}"}
            if not isinstance(reference_report, dict):
                reference_report = {"ok": False, "reason": "reference matcher returned an invalid result"}
            if reference_report.get("ok"):
                import math
                ref_gates = reference_report.get("gates") or {}
                ref_bands = reference_report.get("bands") or {}
                if not isinstance(ref_bands, dict):
                    ref_bands = {}
                required_gates = {"profile_deviation", "bandwidth_coverage", "true_peak", "no_clipping"}
                deviations = (ref_bands.get("max_deviation_before_db"), ref_bands.get("max_deviation_after_db"))
                if (not isinstance(ref_gates, dict) or not required_gates.issubset(ref_gates)
                        or not all(isinstance(ref_gates[key], bool) for key in required_gates)
                        or not all(isinstance(value, (int, float)) and math.isfinite(value) for value in deviations)):
                    reference_report = {"ok": False, "reason": "reference matcher returned an incomplete report"}
            if not reference_report.get("ok"):
                reference_report["applied"] = False
                reference_report["gates"] = {"reference_available": False}
                reference_report["gates_passed"] = False
                fallback_used = True
                fallback_reason = reference_report.get("reason") or "reference matching unavailable"
                break
            import soundfile as sf
            from modules.mix.bus import evaluate_mix

            try:
                candidate = str(reference_report["out_wav"])
                matched, sr = sf.read(candidate, always_2d=True, dtype="float64")
                import numpy as np
                if (not matched.size or matched.shape[1] != 2 or not np.isfinite(matched).all()
                        or sr != sf.info(str(out_wav)).samplerate):
                    raise ValueError("invalid candidate audio or changed sample rate")
                candidate_metrics, candidate_gates = evaluate_mix(matched, sr)
            except Exception as exc:  # noqa: BLE001
                return {"ok": False, "reason": f"cannot measure matched mix: {type(exc).__name__}: {exc}"}
            pre_reference = {"metrics": report, "gates": gates}
            deteriorated = [key for key, passed in gates.items()
                            if passed and (key not in candidate_gates or not bool(candidate_gates[key]))]
            bands = reference_report.get("bands") or {}
            before = bands.get("max_deviation_before_db")
            after = bands.get("max_deviation_after_db")
            if isinstance(before, (int, float)) and isinstance(after, (int, float)) and after > before + 0.01:
                deteriorated.append("reference_deviation")
            attempts.append({"strength": strength, "candidate_mix_gates": candidate_gates,
                             "deviation_after_db": after, "rejected": deteriorated})
            reference_report["candidate_mix_metrics"] = candidate_metrics
            reference_report["candidate_mix_gates"] = candidate_gates
            reference_report["candidate_out_wav"] = candidate
            reference_report["applied"] = not deteriorated
            reference_report["gates"] = {**(reference_report.get("gates") or {}), "mix_safety": not deteriorated}
            reference_report["gates_passed"] = all(reference_report["gates"].values())
            if not deteriorated:
                out_wav, report, gates = candidate, candidate_metrics, candidate_gates
                fallback_used = bool(reference_report.get("fallback_used")) or strength < 1.0
                if fallback_used:
                    fallback_reason = reference_report.get("reason") or f"reference EQ reduced to {strength:.3f} to protect mix"
                break
            reference_report["rejection_reason"] = "candidate worsened: " + ", ".join(deteriorated)
            reference_report["out_wav"] = str(out_wav)
            fallback_used = True
            fallback_reason = reference_report["rejection_reason"]
        reference_report["attempts"] = attempts
    import json
    stage_report = Path(out_dir) / "mix_stage_report.json"
    payload = {
        "ok": True,
        "out_wav": out_wav,
        "report_path": str(stage_report),
        "pre_mix_report_path": result.get("report_path"),
        "engine": "modules.mix.bus",
        "fallback_used": fallback_used,
        "reason": fallback_reason,
        "vocal_used": bool(result.get("vocal_used")),
        "vocal_offset_ms": vocal_offset_ms,
        "gates": gates,
        "gates_passed": bool(gates) and all(gates.values()),
        "pre_reference": pre_reference,
        "metrics": report,
        "staging": {
            "beat": result.get("beat_staging"),
            "bus": result.get("bus_staging"),
            "vocal": result.get("vocal_staging"),
        },
        "sidechain": result.get("sidechain"),
        "width": result.get("width"),
        "reference": reference_report,
    }
    try:
        stage_report.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except (OSError, TypeError, ValueError) as exc:
        return {"ok": False, "reason": f"cannot write mix stage report: {type(exc).__name__}: {exc}"}
    return payload
