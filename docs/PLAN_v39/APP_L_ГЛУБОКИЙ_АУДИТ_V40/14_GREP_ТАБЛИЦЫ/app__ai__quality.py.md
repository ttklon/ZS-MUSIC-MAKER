# grep-таблицы `app/ai/quality.py`

## `import` — 7 совпадений
```
    9 | from __future__ import annotations
   11 | import re
   12 | from collections import Counter
   13 | from pathlib import Path
   14 | from typing import Any
   90 |         import numpy as np
   91 |         import soundfile as sf
```

## `except` — 1 совпадений
```
   94 |     except Exception as exc:
```

## `try` — 1 совпадений
```
   89 |     try:
```

## `def` — 11 совпадений
```
   20 | def lyrics_metrics(text: str) -> dict[str, float | int]:
   40 | def validate_lyrics(text: str, *, min_characters: int = 60) -> dict[str, Any]:
   61 | def validate_metadata_json(payload: Any) -> dict[str, Any]:
   87 | def audio_metrics(path: str | Path) -> dict[str, Any]:
  118 | def validate_audio_artifact(path: str | Path, *, min_duration_sec: float = 1.0) -> dict[str, Any]:
  135 | def validate_vocal_artifact(path: str | Path, text: str) -> dict[str, Any]:
  145 | def validate_rvc_artifact(input_path: str | Path, output_path: str | Path) -> dict[str, Any]:
  163 | def validate_asr_transcript(text: str) -> dict[str, Any]:
  181 | def validate_stem_artifact(input_path: str | Path, output_path: str | Path) -> dict[str, Any]:
  198 | def validate_stereo_texture(path: str | Path, *, min_duration_sec: float = 1.0) -> dict[str, Any]:
  213 | def validate_analysis_json(payload: Any, *, track_level: bool = False) -> dict[str, Any]:
```

## `return` — 39 совпадений
```
   31 |     return {
   44 |         return {"ok": False, "reason": "empty lyrics", "metrics": metrics}
   46 |         return {
   52 |         return {"ok": False, "reason": "too few lyric tokens", "metrics": metrics}
   55 |         return {"ok": False, "reason": "line repetition exceeds hook limit", "metrics": metrics}
   57 |         return {"ok": False, "reason": "token diversity too low", "metrics": metrics}
   58 |     return {"ok": True, "reason": None, "metrics": metrics}
   64 |         return {"ok": False, "reason": "metadata response is not an object", "metrics": {}}
   79 |         return {
   84 |     return {"ok": True, "reason": None, "metrics": {"keys": len(payload), "tags": tag_count}}
   95 |         return {"readable": False, "reason": f"audio read failed: {exc}"}
   97 |         return {"readable": False, "reason": "audio is empty"}
  115 |     return metrics
  122 |         return {"ok": False, "reason": "audio file missing", "metrics": {"path": str(target)}}
  125 |         return {"ok": False, "reason": metrics.get("reason"), "metrics": metrics}
  127 |         return {"ok": False, "reason": "audio duration below minimum", "metrics": metrics}
  129 |         return {"ok": False, "reason": "audio is silent", "metrics": metrics}
  131 |         return {"ok": False, "reason": "audio clips", "metrics": metrics}
  132 |     return {"ok": True, "reason": None, "metrics": metrics}
  142 |     return result
  149 |         return {"ok": False, "reason": "RVC input audio is unreadable", "metrics": {"input": source}}
  153 |         return result
  159 |         return {"ok": False, "reason": "RVC output duration diverges from input", "metrics": result["metrics"]}
  160 |     return {"ok": True, "reason": None, "metrics": result["metrics"]}
  175 |         return {"ok": False, "reason": "ASR transcript is empty or too short", "metrics": metrics}
  177 |         return {"ok": False, "reason": "ASR transcript is excessively repetitive", "metrics": metrics}
  178 |     return {"ok": True, "reason": None, "metrics": metrics}
  185 |         return {"ok": False, "reason": "stem input audio is unreadable", "metrics": {"input": source}}
  189 |         return result
  194 |         return {"ok": False, "reason": "stem duration diverges from input", "metrics": result["metrics"]}
  195 |     return {"ok": True, "reason": None, "metrics": result["metrics"]}
  202 |         return base
  205 |         return {"ok": False, "reason": "texture is not stereo", "metrics": metrics}
  207 |         return {"ok": False, "reason": "stereo side energy too low", "metrics": metrics}
  209 |         return {"ok": False, "reason": "stereo channels are over-correlated", "metrics": metrics}
  210 |     return {"ok": True, "reason": None, "metrics": metrics}
  216 |         return {"ok": False, "reason": "analysis response is not an object", "metrics": {}}
  225 |         return {
  230 |     return {
```

## `if` — 33 совпадений
```
   25 |         if line.strip() and not line.lstrip().startswith("[")
   43 |     if not (text or "").strip():
   45 |     if metrics["characters"] < min_characters:
   51 |     if metrics["tokens"] < 12:
   54 |     if metrics["max_repeated_line"] > 4:
   56 |     if metrics["unique_token_ratio"] < 0.12:
   63 |     if not isinstance(payload, dict):
   68 |     if not 2 <= len(title) <= 120:
   70 |     if not any(descriptions):
   74 |         if key.startswith("tags_") and isinstance(value, list)
   76 |     if tag_count == 0:
   78 |     if missing:
   96 |     if samples.size == 0:
  109 |     if samples.shape[1] >= 2:
  121 |     if not target.exists():
  124 |     if not metrics.get("readable"):
  126 |     if metrics["duration_sec"] < min_duration_sec:
  128 |     if metrics["rms"] < 1e-5:
  130 |     if metrics["peak"] > 1.0001:
  148 |     if not source.get("readable"):
  152 |     if not result["ok"]:
  158 |     if not 0.85 <= ratio <= 1.15:
  174 |     if len(normalized) < 3 or not tokens:
  176 |     if len(tokens) >= 4 and metrics["unique_ratio"] <= 0.25:
  184 |     if not source.get("readable"):
  188 |     if not result["ok"]:
  193 |     if not 0.95 <= ratio <= 1.05:
  201 |     if not base["ok"]:
  204 |     if metrics.get("channels") != 2:
  206 |     if metrics.get("stereo_side_rms", 0.0) < 5e-4:
  208 |     if abs(metrics.get("stereo_correlation", 1.0)) > 0.995:
  215 |     if not isinstance(payload, dict):
  224 |     if missing:
```

## `for` — 1 совпадений
```
   24 |         for line in (text or "").splitlines()
```

## `np` — 5 совпадений
```
   98 |     peak = float(np.max(np.abs(samples)))
   99 |     rms = float(np.sqrt(np.mean(samples ** 2)))
  111 |         denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
  112 |         correlation = float(np.dot(left, right) / denominator) if denominator > 1e-12 else 1.0
  114 |         metrics["stereo_side_rms"] = round(float(np.sqrt(np.mean(((left - right) * 0.5) ** 2))), 6)
```

## `sf` — 1 совпадений
```
   93 |         samples, sample_rate = sf.read(str(path), always_2d=True)
```
