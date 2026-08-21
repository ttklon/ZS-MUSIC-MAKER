# -*- coding: utf-8 -*-
"""ZS Music Maker - modules/mastering_ai.py (v38): matchering -> mastering_pro."""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional
from app.ai.registry import registry


def master_with_matchering(handle: Any, input_wav: str, out_wav: str,
                           reference_wav: str, target_lufs: float = -14.0) -> Dict[str, Any]:
    """Выполнить matchering через уже загруженный registry handle."""
    try:
        handle.process(
            target=input_wav,
            reference=reference_wav,
            results=[handle.pcm16(out_wav)],
        )
        if not Path(out_wav).exists():
            return {"ok": False, "reason": "matchering completed without output", "engine": "matchering"}
        from modules.mastering_pro import normalize_master_loudness

        loudness = normalize_master_loudness(out_wav, out_wav, target_lufs=target_lufs, ceiling_db=-1.2)
        if not loudness.get("ok"):
            return {"ok": False, "reason": loudness.get("reason", "post-matchering normalization failed"), "engine": "matchering"}
        return {
            "ok": True, "engine": "matchering", "reference": reference_wav,
            "path": out_wav, "loudness": loudness,
        }
    except Exception as exc:
        return {"ok": False, "reason": f"matchering failed: {exc}", "engine": "matchering"}


def master_ai(input_wav: str, out_wav: str, reference_wav: Optional[str] = None,
              target_lufs: float = -14.0, handle: Any = None) -> Dict[str, Any]:
    Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
    fallback_reason = ""
    if reference_wav and handle is not None:
        result = master_with_matchering(handle, input_wav, out_wav, reference_wav, target_lufs)
        if result.get("ok"):
            return result
        fallback_reason = result.get("reason", "matchering failed")
    elif reference_wav and registry.is_available("mastering_ai"):
        try:
            with registry.use("mastering_ai") as loaded:
                result = master_with_matchering(loaded.handle, input_wav, out_wav, reference_wav, target_lufs)
            if result.get("ok"):
                return result
            fallback_reason = result.get("reason", "matchering failed")
        except Exception as exc:
            fallback_reason = f"matchering load failed: {exc}"
    else:
        fallback_reason = "no reference" if not reference_wav else "matchering unavailable"
    try:
        from modules import mastering_pro
        res = mastering_pro.process_mastering(input_wav, out_wav,
                                              vocal_path=None, target_lufs=target_lufs)
        res = res if isinstance(res, dict) else {"ok": True, "path": out_wav}
        loudness = mastering_pro.normalize_master_loudness(
            out_wav, out_wav, target_lufs=target_lufs, ceiling_db=-1.2
        )
        if not loudness.get("ok"):
            return {"ok": False, "reason": loudness.get("reason", "fallback normalization failed")}
        res["engine"] = "mastering_pro"
        res["fallback_reason"] = fallback_reason
        res["loudness"] = loudness
        return res
    except Exception as e:
        return {"ok": False, "reason": f"mastering failed: {e}"}
