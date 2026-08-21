# -*- coding: utf-8 -*-
"""ZS Music Maker - modules/mastering_ai.py (v38): matchering -> mastering_pro."""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional
from app.ai.registry import registry


def master_ai(input_wav: str, out_wav: str, reference_wav: Optional[str] = None,
              target_lufs: float = -9.0) -> Dict[str, Any]:
    Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
    fallback_reason = ""
    if reference_wav and registry.is_available("mastering_ai"):
        try:
            with registry.use("mastering_ai") as m:
                mg = m.handle
                mg.process(target=input_wav, reference=reference_wav,
                           results=[mg.pcm16(out_wav)])
            return {"ok": True, "engine": "matchering",
                    "reference": reference_wav, "path": out_wav}
        except Exception as e:
            fallback_reason = str(e)
    else:
        fallback_reason = "no reference" if not reference_wav else "matchering unavailable"
    try:
        from modules import mastering_pro
        res = mastering_pro.process_mastering(input_wav, out_wav,
                                              vocal_path=None, target_lufs=target_lufs)
        res = res if isinstance(res, dict) else {"ok": True, "path": out_wav}
        res["engine"] = "mastering_pro"
        res["fallback_reason"] = fallback_reason
        return res
    except Exception as e:
        return {"ok": False, "reason": f"mastering failed: {e}"}
