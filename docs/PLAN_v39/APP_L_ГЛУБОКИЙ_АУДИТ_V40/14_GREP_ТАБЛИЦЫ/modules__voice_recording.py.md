# grep-таблицы `modules/voice_recording.py`

## `import` — 15 совпадений
```
   19 | from __future__ import annotations
   21 | import json
   22 | import math
   23 | import time
   24 | import uuid
   25 | import wave
   26 | from collections.abc import Callable
   27 | from dataclasses import asdict, dataclass
   28 | from pathlib import Path
   29 | from typing import Any
   36 |     import numpy as _np
   37 |     import sounddevice as _sd  # type: ignore
  220 |             import soundfile as sf
  260 |         import numpy as np
  261 |         import soundfile as sf
```

## `print` — 1 совпадений
```
  395 |     print(json.dumps(capability_report(), indent=2))
```

## `except` — 12 совпадений
```
   40 | except Exception:
  105 |         except Exception:
  139 |         except Exception:
  170 |         except Exception as e:
  181 |         except Exception:
  199 |         except Exception as e:
  236 |         except Exception as e:
  262 |     except Exception:
  272 |     except Exception:
  325 |         except Exception:
  367 |     except Exception:
  383 |         except Exception:
```

## `try` — 12 совпадений
```
   35 | try:
  101 |         try:
  111 |         try:
  154 |         try:
  178 |         try:
  187 |         try:
  219 |         try:
  259 |     try:
  268 |     try:
  323 |         try:
  362 |     try:
  376 |         try:
```

## `def` — 12 совпадений
```
   70 |     def as_dict(self) -> dict[str, Any]:
   77 |     def __init__(
  100 |     def _callback(self, indata, frames, time_info, status):
  108 |     def _emit_metrics(self, chunk) -> None:
  142 |     def start(self) -> dict[str, Any]:
  174 |     def stop(self) -> dict[str, Any]:
  202 |     def _write_wav(self, path: str, samples, sr: int) -> None:
  213 |     def ingest_wav(
  239 |     def stop_and_split(
  253 | def split_wav_into_takes(
  295 |     def _finalize(a: int, b: int) -> TakeInfo | None:
  373 | def capability_report() -> dict[str, Any]:
```

## `class` — 3 совпадений
```
   47 | class RecorderMetrics:
   58 | class TakeInfo:
   74 | class RealMicRecorder:
```

## `return` — 24 совпадений
```
   71 |         return asdict(self)
  110 |             return
  147 |             return {
  164 |             return {
  172 |             return {"ok": False, "backend": self._backend, "reason": str(e)}
  177 |             return {"ok": False, "reason": "not recording"}
  186 |             return {"ok": False, "reason": "no audio captured"}
  192 |             return {
  200 |             return {"ok": False, "reason": f"save failed: {e}"}
  204 |             return
  218 |             return {"ok": False, "reason": f"file not found: {wav_path}"}
  226 |             return {
  237 |             return {"ok": False, "reason": str(e)}
  244 |             return []
  245 |         return split_wav_into_takes(
  263 |         return []
  267 |         return []
  273 |         return []
  277 |         return []
  300 |             return None
  326 |             return None
  328 |         return TakeInfo(
  370 |     return takes
  385 |     return {
```

## `if` — 24 совпадений
```
  109 |         if _np is None or self.on_metrics is None:
  119 |             if speaking:
  124 |                 if self._silence_frames > 10:
  145 |         if not SD_OK:
  176 |         if not self._active or self._stream is None:
  185 |         if not self._buf or _np is None:
  203 |         if _np is None:
  217 |         if not p.exists():
  243 |         if not info.get("ok"):
  266 |     if not p.exists():
  270 |         if y.ndim > 1:
  276 |     if win < 1:
  299 |         if dur_ms < min_take_ms:
  310 |         if seg_clip > 0.03:
  342 |         if not s:
  343 |             if not in_speech:
  348 |             if in_speech:
  350 |                 if sil_count >= silence_wins:
  352 |                     if ti:
  356 |     if in_speech:
  358 |         if ti:
  375 |     if SD_OK:
  381 |                 if d.get("max_input_channels", 0) > 0
  394 | if __name__ == "__main__":
```

## `for` — 3 совпадений
```
  282 |             for i in range(n_wins)
  341 |     for i, s in enumerate(silence):
  380 |                 for d in devs
```

## `with` — 1 совпадений
```
  207 |         with wave.open(path, "wb") as w:
```

## `open` — 1 совпадений
```
  207 |         with wave.open(path, "wb") as w:
```

## `np` — 6 совпадений
```
  279 |     rms = np.array(
  281 |             float(np.sqrt(np.mean(y[i * win : (i + 1) * win] ** 2)) + 1e-9)
  285 |     rms_db = 20 * np.log10(rms + 1e-9)
  304 |         seg_rms = float(np.sqrt(np.mean(seg**2)) + 1e-9)
  305 |         seg_peak = float(np.max(np.abs(seg)) + 1e-9)
  306 |         seg_clip = float(np.mean(np.abs(seg) > 0.98))
```

## `sf` — 4 совпадений
```
  222 |             y, sr = sf.read(str(p))
  225 |             sf.write(str(dst), y, sr)
  269 |         y, sr = sf.read(str(p))
  324 |             sf.write(str(tpath), seg, sr)
```
