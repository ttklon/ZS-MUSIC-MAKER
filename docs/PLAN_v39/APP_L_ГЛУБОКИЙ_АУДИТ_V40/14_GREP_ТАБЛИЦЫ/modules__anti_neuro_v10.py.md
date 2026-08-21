# grep-таблицы `modules/anti_neuro_v10.py`

## `import` — 18 совпадений
```
   17 | from __future__ import annotations
   19 | import json
   20 | import logging
   21 | import random
   22 | from pathlib import Path
   23 | from typing import Any
   28 |     from pydub import AudioSegment
   29 |     from pydub.generators import WhiteNoise
   38 |     import numpy as _np
   39 |     import soundfile as _sf
  134 |             import shutil
  204 |                         from scipy.signal import butter, sosfilt
  217 |                         from scipy.signal import butter, sosfilt
  246 |                         from scipy.signal import butter, sosfilt
  304 |             import numpy as np
  308 |             from scipy.signal import butter, sosfilt
  346 |             import librosa
  347 |             import numpy as np
```

## `print` — 1 совпадений
```
  401 |     print(json.dumps(capability_report(), ensure_ascii=False, indent=2))
```

## `except` — 11 совпадений
```
   32 | except Exception:
   42 | except Exception:
   91 |         except Exception as e:
  145 |         except Exception as e:
  212 |                     except Exception as e:
  224 |                     except Exception as e:
  256 |                     except Exception as e:
  260 |             except Exception as e:
  279 |     except Exception as e:
  321 |         except Exception:
  381 |         except Exception as e:
```

## `try` — 11 совпадений
```
   27 | try:
   37 | try:
   87 |         try:
  133 |         try:
  149 |     try:
  178 |             try:
  203 |                     try:
  216 |                     try:
  245 |                     try:
  303 |         try:
  345 |         try:
```

## `def` — 5 совпадений
```
   48 | def polish_vocal(
  107 | def apply_polish(
  128 | def _polish_numpy(
  283 | def _apply_stage(seg, name: str, rng: random.Random):
  391 | def capability_report() -> dict[str, Any]:
```

## `return` — 19 совпадений
```
   56 |         return _polish_numpy(vocal_wav, out_wav, preset=preset, seed=seed)
   96 |     return {
  125 |     return r
  137 |             return {
  146 |             return {"ok": False, "reason": str(e)}
  268 |         return {
  280 |         return {"ok": False, "reason": str(e)}
  287 |         return seg, {"breath_ms": 180}
  300 |         return out, {"shifted_chunks": shifts, "total_chunks": len(chunks)}
  315 |             return AudioSegment(
  323 |             return seg.overlay(boosted.apply_gain(-6)), {
  329 |         return seg, {"low_pass_hz": 14000}
  332 |         return seg.fade_out(fade_ms), {"fade_out_ms": fade_ms}
  343 |         return out, {"micro_dips": dips}
  380 |             return out, {"formant_steps": steps, "method": "librosa_resample_trick"}
  382 |             return seg, {"error": f"formant shift failed: {e}"}
  387 |         return first + second, {"mid_hp_hz": 120}
  388 |     return seg, {}
  392 |     return {
```

## `if` — 23 совпадений
```
   55 |     if not LIBS_OK:
  115 |     if preset is None:
  116 |         if intensity < 0.35:
  123 |     if isinstance(r, dict):
  132 |     if not NP_OK:
  179 |                 if stage == "breath":
  194 |                     if envin.shape[0] > dur:
  229 |                     if fade_len > 8:
  238 |                         if rng.random() < 0.03:
  264 |         if peak > 0.98:
  284 |     if name == "breath":
  288 |     if name == "timing_jitter":
  294 |             if rng.random() < 0.15:
  296 |                 if shift > 0:
  301 |     if name == "consonant_boost":
  327 |     if name == "ghost_remove":
  330 |     if name == "ending":
  333 |     if name == "human_error":
  339 |             if rng.random() < 0.03:
  344 |     if name == "formant_shift":
  370 |             if len(y_final) > len(y):
  383 |     if name == "entropy_boost":
  400 | if __name__ == "__main__":
```

## `for` — 5 совпадений
```
   86 |     for stage in plan:
  177 |         for stage in plan:
  237 |                     for i in range(0, y.shape[0] - chunk, chunk):
  293 |         for c in chunks:
  338 |         for c in chunks:
```

## `np` — 5 совпадений
```
  306 |             y = np.array(seg.get_array_of_samples(), dtype=np.float32)
  314 |             y_int = np.clip(y, -32768, 32767).astype(np.int16)
  350 |             y = np.array(seg.get_array_of_samples(), dtype=np.float32) / (2**15)
  373 |                 y_final = np.pad(y_final, (0, len(y) - len(y_final)))
  376 |             y_int = (y_final * (2**15)).astype(np.int16)
```
