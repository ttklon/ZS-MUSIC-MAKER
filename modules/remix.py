"""Безопасный remix renderer для user-owned или явно авторизованных vocal stems."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def render_remix(new_beat_path: str, vocal_stem_path: str, out_path: str, *,
                 source_authorized: bool = False, vocal_gain_db: float = -4.0) -> dict[str, Any]:
    """Собрать remix из нового бита и разрешённого vocal stem без looping source vocal."""
    if not source_authorized:
        return {"ok": False, "reason": "source vocal stem authorization is required"}
    try:
        import librosa
        import numpy as np
        import soundfile as sf

        beat, beat_sr = sf.read(new_beat_path, always_2d=True)
        vocal, vocal_sr = sf.read(vocal_stem_path, always_2d=True)
        if vocal_sr != beat_sr:
            vocal = librosa.resample(vocal.T, orig_sr=vocal_sr, target_sr=beat_sr).T
        if vocal.shape[1] == 1:
            vocal = np.repeat(vocal, 2, axis=1)
        if beat.shape[1] == 1:
            beat = np.repeat(beat, 2, axis=1)
        frames = min(len(beat), len(vocal))
        mix = beat.copy()
        gain = 10.0 ** (vocal_gain_db / 20.0)
        mix[:frames] = mix[:frames] + vocal[:frames] * gain
        peak = float(np.max(np.abs(mix)) + 1e-9)
        if peak > 0.99:
            mix *= 0.98 / peak
        target = Path(out_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        sf.write(target, mix, beat_sr, subtype="PCM_16")
        return {
            "ok": True, "path": str(target), "sample_rate": int(beat_sr),
            "vocal_frames_used": int(frames), "source_authorized": True,
            "engine": "remix_mixdown",
        }
    except Exception as exc:
        return {"ok": False, "reason": f"remix render failed: {exc}"}
