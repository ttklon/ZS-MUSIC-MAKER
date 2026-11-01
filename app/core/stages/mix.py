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
    beat_wav: str, voice_wav: str | None, out_dir: Path, reference_wav: str | None = None
) -> dict[str, Any]:
    """Собрать микс штатным микшером и вернуть измеренный отчёт."""
    try:
        from modules.mix.bus import prepare_mix

        result = prepare_mix(beat_wav, voice_wav, out_dir)
    except Exception as exc:  # noqa: BLE001 - стадия обязана вернуть причину, не падать
        return {"ok": False, "reason": f"{type(exc).__name__}: {exc}"}

    if not result.get("ok"):
        return {"ok": False, "reason": result.get("reason", "mix failed")}

    out_wav = result.get("out_wav")
    if not out_wav or not Path(out_wav).exists():
        return {"ok": False, "reason": "mix produced no output file"}

    reference_report: dict[str, Any] | None = None
    if reference_wav:
        # 4.5.4: референс-матчинг с отчётом отклонений. Ошибка матчинга не
        # ломает микс: остаётся честно помеченный отчёт с причиной.
        try:
            from modules.mix.reference import match_to_reference

            reference_report = match_to_reference(
                out_wav, reference_wav, str(Path(out_dir) / "mix_matched.wav")
            )
            if reference_report.get("ok"):
                out_wav = str(reference_report["out_wav"])
        except Exception as exc:  # noqa: BLE001 - стадия обязана вернуть причину
            reference_report = {"ok": False, "reason": f"{type(exc).__name__}: {exc}"}

    report = dict(result.get("report") or {})
    return {
        "ok": True,
        "out_wav": out_wav,
        "report_path": result.get("report_path"),
        "engine": "modules.mix.bus",
        "fallback_used": False,
        "vocal_used": bool(result.get("vocal_used")),
        "gates": result.get("gates", {}),
        "gates_passed": bool(result.get("gates_passed")),
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
