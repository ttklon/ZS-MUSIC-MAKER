# -*- coding: utf-8 -*-
"""
modules.hit_factory.humanizer — дополнительный «нероншно» слой.

Даже если пайплайн уже применил anti_neuro на вокале и humanize на бите,
фабрика прогоняет финальный мастер через anti_neuro_track (лёгкий polish)
и проверяет, что humanize не был выключен.

Полностью numpy + soundfile, бесплатно.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

_LOG = logging.getLogger(__name__)


def ensure_human(
    master_wav: str | Path,
    out_wav: str | Path | None = None,
    preset: str = "standard",
    seed: int | None = None,
) -> dict[str, Any]:
    """
    Применяет anti_neuro_track polish к мастеру если он ещё не был применён.
    Возвращает {ok, out_wav, applied, reason, details}.
    Если файл не найден — {ok: False}.
    """
    src = Path(master_wav)
    if not src.exists():
        return {"ok": False, "reason": f"master not found: {src}", "applied": False}

    # если out не задан — перезаписываем в output/hits/*_human.wav рядом
    if out_wav is None:
        out_wav = src.with_name(src.stem + "_human.wav")
    out_wav = Path(out_wav)

    # лёгкий трек-полиш: добавляет энтропию второй половине, не меняет длину
    try:
        from modules.anti_neuro_track import polish_track

        # polish_track expects (in_wav, out_wav, preset, seed)
        result = polish_track(str(src), str(out_wav), preset=preset, seed=seed)
        if isinstance(result, dict):
            if result.get("ok"):
                return {"ok": True, "out_wav": str(out_wav), "applied": True, "details": result}
            # если polish вернул not ok — не считаем критичной ошибкой, возвращаем оригинал
            return {"ok": True, "out_wav": str(src), "applied": False, "reason": result.get("reason", "polish returned not ok"), "details": result}
        # если вернул путь строкой
        if isinstance(result, str) and Path(result).exists():
            return {"ok": True, "out_wav": result, "applied": True}
        return {"ok": True, "out_wav": str(src), "applied": False, "reason": "polish returned unexpected type"}
    except Exception as exc:  # noqa: BLE001
        _LOG.debug("humanizer ensure_human failed: %s", exc, exc_info=True)
        return {"ok": True, "out_wav": str(src), "applied": False, "reason": f"{type(exc).__name__}: {exc}"}


def vocal_human_report(vocal_stages: list[Any]) -> dict[str, Any]:
    """Анализирует stages на предмет humanize и anti_neuro применённости."""
    info: dict[str, Any] = {"vocal_human": None, "warnings": []}
    try:
        # ищем вокальные стадии
        for st in vocal_stages or []:
            name = getattr(st, "name", "") or (st.get("name") if isinstance(st, dict) else "")
            out = getattr(st, "output", None)
            if out is None and isinstance(st, dict):
                out = st.get("output") or st
            if not isinstance(out, dict):
                continue
            if name in ("_stage_voice_synth", "_stage_vocal_fx"):
                # scaffold помечен synthetic/blocked — это не человеческий вокал
                if out.get("synthetic") or out.get("blocked"):
                    info["warnings"].append(f"{name}: synthetic scaffold (not human voice, RVC blocked)")
                if out.get("engine"):
                    info["vocal_human"] = out.get("engine")
        if not info["vocal_human"]:
            info["warnings"].append("vocal engine unknown — check pyttsx3/Silero availability; scaffold is placeholder")
    except Exception as exc:  # noqa: BLE001
        info["warnings"].append(f"human report failed: {exc}")
    return info


def mix_human_gates(mix_report: dict | None) -> dict[str, Any]:
    """Возвращает краткий отчёт по humanize гейтам микса."""
    if not isinstance(mix_report, dict):
        return {"ok": False, "reason": "no mix report"}
    gates = mix_report.get("gates") or {}
    metrics = mix_report.get("metrics") or mix_report
    # ожидаемые гейты микса: bus_rms, correlation, crest и т.д.
    return {
        "gates": gates,
        "gates_passed": mix_report.get("gates_passed"),
        "metrics_keys": list(metrics.keys())[:8],
    }
