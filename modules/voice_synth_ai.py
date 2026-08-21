# -*- coding: utf-8 -*-
"""XTTS-v2 vocal adapter с опциональной RVC-конверсией через public infer API."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Dict, Optional

from app.ai.quality import validate_rvc_artifact, validate_vocal_artifact
from app.ai.registry import registry


def _synthesize_with_handle(handle: Any, text: str, out_path: str,
                            speaker_wav: Optional[str], language: str) -> Dict[str, Any]:
    try:
        target = Path(out_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        kwargs = {"text": text, "file_path": str(target), "language": language}
        if speaker_wav and Path(speaker_wav).is_file():
            kwargs["speaker_wav"] = speaker_wav
        handle.tts_to_file(**kwargs)
        quality = validate_vocal_artifact(target, text)
        return {
            "ok": bool(quality["ok"]),
            "engine": "xtts_v2",
            "vocal_path": str(target),
            "speaker_wav_used": "speaker_wav" in kwargs,
            "quality": quality,
            "reason": quality["reason"],
        }
    except Exception as exc:
        return {"ok": False, "reason": f"XTTS synthesis failed: {exc}", "engine": "xtts_v2"}


def _convert_with_handle(handle: Any, input_wav: str, out_path: str,
                         voice_name: str, pitch_shift: int) -> Dict[str, Any]:
    try:
        safe_voice_name = Path(voice_name).name
        if not safe_voice_name:
            return {"ok": False, "reason": "RVC voice name is missing"}
        produced = handle.infer(
            input_wav=input_wav,
            voice_name=safe_voice_name,
            pitch_shift=int(pitch_shift),
            out_name=Path(out_path).name,
        )
        source = Path(produced) if produced else None
        if source is None or not source.is_file() or source.stat().st_size <= 100:
            return {"ok": False, "reason": "RVC did not produce an audio file"}
        target = Path(out_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.resolve() != target.resolve():
            shutil.copy2(source, target)
        quality = validate_rvc_artifact(input_wav, target)
        return {
            "ok": bool(quality["ok"]),
            "vocal_path": str(target),
            "engine": "rvc",
            "voice_name": safe_voice_name,
            "pitch_shift": int(pitch_shift),
            "quality": quality,
            "reason": quality["reason"],
        }
    except Exception as exc:
        return {"ok": False, "reason": f"RVC inference failed: {exc}", "engine": "rvc"}


def synth_vocal_ai(text: str, out_path: str, speaker_wav: Optional[str] = None,
                   language: str = "ru", rvc_model: Optional[str] = None,
                   rvc_voice_name: Optional[str] = None, pitch_shift: int = 0,
                   tts_handle: Any = None, rvc_handle: Any = None) -> Dict[str, Any]:
    """Синтезировать XTTS vocal и, только при явном voice name, применить RVC.

    ``rvc_model`` сохраняется только как provenance for backward-compatible
    callers. `rvc_manager.infer` фактически адресует user-trained model по
    `rvc_voice_name`, поэтому путь к произвольному `.pth` не выдаётся за
    применённую конверсию.
    """
    if not text or not text.strip():
        return {"ok": False, "reason": "empty text"}
    if tts_handle is None and not registry.is_available("tts_vocal"):
        return {"ok": False, "reason": "tts_vocal unavailable - install TTS (Coqui)"}
    if tts_handle is None:
        with registry.use("tts_vocal") as loaded:
            result = _synthesize_with_handle(loaded.handle, text, out_path, speaker_wav, language)
    else:
        result = _synthesize_with_handle(tts_handle, text, out_path, speaker_wav, language)
    result["rvc_applied"] = False
    result["rvc_model"] = rvc_model
    if not result.get("ok"):
        return result

    voice_name = rvc_voice_name or (Path(rvc_model).stem if rvc_model else "")
    if not voice_name:
        result["rvc_skipped"] = "no rvc_voice_name"
        return result
    rvc_out = str(Path(out_path).with_name(f"{Path(out_path).stem}_rvc.wav"))
    if rvc_handle is not None:
        conversion = _convert_with_handle(rvc_handle, out_path, rvc_out, voice_name, pitch_shift)
    elif registry.is_available("vocal_rvc"):
        with registry.use("vocal_rvc") as loaded:
            conversion = _convert_with_handle(loaded.handle, out_path, rvc_out, voice_name, pitch_shift)
    else:
        result["rvc_skipped"] = "vocal_rvc unavailable"
        return result
    result["rvc"] = conversion
    if conversion.get("ok"):
        result["vocal_path"] = conversion["vocal_path"]
        result["rvc_applied"] = True
        result["rvc_voice_name"] = conversion["voice_name"]
    else:
        result["rvc_error"] = conversion.get("reason")
    return result
