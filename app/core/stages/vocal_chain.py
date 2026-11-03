# -*- coding: utf-8 -*-
"""
app/core/stages/vocal_chain.py — вокальная ветка пайплайна.

Порядок жёсткий: собственная запись пользователя → TTS-скаффолд → RVC →
вокальные эффекты. Синтетический скаффолд без RVC в мастер не попадает: это
пластмасса, убивающая «живость». Инструментальный режим честно помечает все
шаги BLOCKED.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.pipeline_runtime import _blocked, _output, _timed
from app.core.stages.vocal import _stage_rvc, _stage_vocal_fx, _stage_voice_synth
from app.pipeline import StageResult, StageStatus


def _run_vocal_chain(
    recipe: dict[str, Any],
    lyrics_text: str,
    out_root: Path,
    bpm: float | None = None,
    key: str | None = None,
) -> tuple[list[StageResult], str | None, list[str]]:
    """Вокальная ветка: запись пользователя → TTS → RVC → эффекты.

    Инструментальный режим (`voice_mode=off`) честно помечает все вокальные
    стадии BLOCKED. Синтетический скаффолд без RVC в мастер не попадает —
    это пластмасса, которая убивает «живость» трека.
    """
    warnings: list[str] = []
    if recipe["voice_mode"] == "off":
        reason = "voice_mode='off' (instrumental) — vocal pipeline skipped by user choice"
        stages = [
            _blocked("_stage_voice_synth", reason),
            _blocked("_stage_rvc", "voice_mode='off' (instrumental)"),
            _blocked("_stage_vocal_fx", "voice_mode='off' (instrumental)"),
        ]
        return stages, None, warnings

    own_vocal = recipe.get("own_vocal_wav")
    if own_vocal:
        try:
            import soundfile as sf

            info = sf.info(str(own_vocal))
            if info.frames <= 0 or info.samplerate <= 0 or info.channels <= 0:
                raise ValueError("empty or invalid audio")
        except Exception as exc:  # noqa: BLE001 - explicit input must not silently become TTS
            reason = f"recording unavailable or unreadable: {type(exc).__name__}: {exc}"
            return [
                StageResult(name="_stage_voice_synth", status=StageStatus.FAILED, reason=reason),
                _blocked("_stage_rvc", "recording unavailable"),
                _blocked("_stage_vocal_fx", "recording unavailable"),
            ], None, [reason]
        synth = StageResult(
            name="_stage_voice_synth",
            status=StageStatus.OK,
            output={
                "ok": True,
                "path": str(own_vocal),
                "engine": "user_recording",
                "reason": "own microphone recording used as primary vocal path",
            },
        )
    else:
        synth = _timed("_stage_voice_synth", lambda: _stage_voice_synth(lyrics_text, out_root))
    stages = [synth]

    voice_wav = _output(synth).get("path")
    synthetic = bool(_output(synth).get("synthetic"))

    if voice_wav and not recipe.get("use_rvc", True):
        rvc = _blocked("_stage_rvc", "RVC disabled by user; original recording retained")
    elif voice_wav:
        rvc = _timed(
            "_stage_rvc",
            lambda: _stage_rvc(voice_wav, out_root, upstream_synthetic=synthetic,
                               pitch_shift=recipe.get("rvc_pitch_shift", 0),
                               model_path=recipe.get("rvc_model_path", ""),
                               index_path=recipe.get("rvc_index_path", "")),
        )
    else:
        rvc = _blocked("_stage_rvc", "no voice_wav upstream (voice_synth failed)")
    stages.append(rvc)

    rvc_path = _output(rvc).get("path") if rvc.ok else None
    vocal_final = rvc_path or voice_wav

    if vocal_final:
        fx = _timed(
            "_stage_vocal_fx",
            lambda: _stage_vocal_fx(
                vocal_final, out_root, bpm=bpm, key=key, tune=bool(recipe.get("tune", True))
            ),
        )
    else:
        fx = _blocked("_stage_vocal_fx", "no vocal")
    stages.append(fx)
    if fx.ok:
        vocal_final = _output(fx).get("path") or _output(fx).get("out_wav") or vocal_final

    if synthetic and not rvc_path:
        warnings.append(
            "vocal skipped: synthetic scaffold not mixed "
            "(instrumental master; record voice or install TTS)"
        )
        vocal_final = None
    return stages, vocal_final, warnings


