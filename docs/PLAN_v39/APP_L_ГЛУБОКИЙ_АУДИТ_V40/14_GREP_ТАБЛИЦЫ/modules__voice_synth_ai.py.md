# grep-таблицы `modules/voice_synth_ai.py`

## `import` — 4 совпадений
```
    3 | from __future__ import annotations
    4 | from pathlib import Path
    5 | from typing import Any, Dict, Optional
    6 | from app.ai.registry import registry
```

## `except` — 2 совпадений
```
   32 |                 except Exception:
   38 |         except Exception as e:
```

## `try` — 2 совпадений
```
   25 |         try:
   29 |                 try:
```

## `def` — 1 совпадений
```
    9 | def synth_vocal_ai(text: str, out_path: str, speaker_wav: Optional[str] = None,
```

## `return` — 3 совпадений
```
   12 |         return {"ok": False, "reason": "empty text"}
   15 |         return {"ok": False, "reason": "tts_vocal unavailable - install TTS (Coqui)"}
   40 |     return result
```

## `if` — 5 совпадений
```
   11 |     if not text or not text.strip():
   14 |     if not registry.is_available("tts_vocal"):
   19 |         if speaker_wav and Path(speaker_wav).exists():
   24 |     if rvc_model and registry.is_available("vocal_rvc"):
   34 |                 if ok and Path(conv).exists():
```

## `with` — 2 совпадений
```
   16 |     with registry.use("tts_vocal") as m:
   26 |             with registry.use("vocal_rvc") as m:
```
