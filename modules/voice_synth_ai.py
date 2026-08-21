# -*- coding: utf-8 -*-
"""ZS Music Maker - modules/voice_synth_ai.py (v38): XTTS-v2 -> RVC."""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional
from app.ai.registry import registry


def synth_vocal_ai(text: str, out_path: str, speaker_wav: Optional[str] = None,
                   language: str = "ru", rvc_model: Optional[str] = None) -> Dict[str, Any]:
    if not text or not text.strip():
        return {"ok": False, "reason": "empty text"}
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    if not registry.is_available("tts_vocal"):
        return {"ok": False, "reason": "tts_vocal unavailable - install TTS (Coqui)"}
    with registry.use("tts_vocal") as m:
        tts = m.handle
        kwargs = dict(text=text, file_path=out_path, language=language)
        if speaker_wav and Path(speaker_wav).exists():
            kwargs["speaker_wav"] = speaker_wav
        tts.tts_to_file(**kwargs)
    result = {"ok": True, "engine": "xtts_v2", "vocal_path": out_path,
              "sample_rate": 24000, "rvc_applied": False}
    if rvc_model and registry.is_available("vocal_rvc"):
        try:
            with registry.use("vocal_rvc") as m:
                conv = out_path.replace(".wav", f"_rvc_{Path(rvc_model).stem}.wav")
                ok = False
                try:
                    ok = m.handle.convert(input_path=out_path, output_path=conv,
                                          model_path=rvc_model)
                except Exception:
                    ok = False
                if ok and Path(conv).exists():
                    result["vocal_path"] = conv
                    result["rvc_applied"] = True
                    result["rvc_model"] = rvc_model
        except Exception as e:
            result["rvc_error"] = str(e)
    return result
