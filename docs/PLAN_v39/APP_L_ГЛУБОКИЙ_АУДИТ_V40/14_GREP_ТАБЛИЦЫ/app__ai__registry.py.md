# grep-таблицы `app/ai/registry.py`

## `import` — 27 совпадений
```
    5 | from __future__ import annotations
    6 | import gc, os, time, threading
    7 | from dataclasses import dataclass
    8 | from pathlib import Path
    9 | from typing import Any, Callable, Dict, Optional
  138 |                 import llama_cpp  # noqa
  141 |                 import audiocraft  # noqa
  144 |                 from TTS.api import TTS  # noqa
  150 |                 import demucs  # noqa
  153 |                 from faster_whisper import WhisperModel  # noqa
  156 |                 import transformers  # noqa
  159 |                 import librosa  # noqa
  162 |                 import diffusers  # noqa
  165 |                 import matchering  # noqa
  201 |                 import torch
  231 |             import torch
  238 |             import torch_directml  # noqa
  248 |                 from llama_cpp import Llama
  269 |                 from audiocraft.models import MusicGen
  281 |             from TTS.api import TTS
  294 |             from modules import rvc_manager
  300 |             from demucs.pretrained import get_model
  313 |             from faster_whisper import WhisperModel
  323 |             from transformers import ClapModel, ClapProcessor
  339 |             from diffusers import DiffusionPipeline
  340 |             import torch
  360 |             import matchering  # noqa
```

## `except` — 9 совпадений
```
  167 |         except Exception:
  196 |             except Exception:
  205 |             except Exception:
  235 |         except Exception:
  241 |         except Exception:
  288 |                 except Exception:
  307 |                 except Exception:
  331 |                 except Exception:
  354 |                 except Exception:
```

## `try` — 9 совпадений
```
  136 |         try:
  194 |             try:
  200 |             try:
  230 |         try:
  237 |         try:
  286 |                 try:
  305 |                 try:
  329 |                 try:
  350 |                 try:
```

## `def` — 23 совпадений
```
   25 |     def from_env(cls) -> "HardwareBudget":
  114 |     def __init__(self, hw: Optional[HardwareBudget] = None):
  121 |     def status(self) -> Dict[str, Any]:
  131 |     def is_available(self, key: str) -> bool:
  171 |     def load(self, key: str) -> LoadedModel:
  190 |     def unload(self) -> None:
  209 |         def __init__(self, reg, key, unload_after):
  213 |         def __enter__(self):
  217 |         def __exit__(self, et, ex, tb):
  222 |     def use(self, key: str, unload_after: bool = True):
  225 |     def pick_device(self, spec: Dict[str, Any]) -> str:
  245 |     def _register_default_loaders(self) -> None:
  246 |         def _llama(key):
  247 |             def _do():
  267 |         def _musicgen(key):
  268 |             def _do():
  280 |         def _xtts():
  293 |         def _rvc():
  299 |         def _demucs():
  312 |         def _wh():
  322 |         def _clap():
  338 |         def _sdxl():
  359 |         def _match():
```

## `class` — 4 совпадений
```
   17 | class HardwareBudget:
  104 | class LoadedModel:
  113 | class ModelRegistry:
  208 |     class _UseCtx:
```

## `raise` — 3 совпадений
```
  179 |                 raise KeyError(f"Unknown model role: {key}")
  182 |                 raise RuntimeError(f"No loader registered for {key}")
  253 |                     raise FileNotFoundError(
```

## `return` — 36 совпадений
```
   26 |         return cls(
  123 |         return {"current": cur.key if cur else None,
  134 |             return False
  139 |                 return (MODELS_DIR / "llm" / spec["file"]).exists()
  142 |                 return True
  145 |                 return True
  148 |                 return d.exists() and any(d.glob("*.pth"))
  151 |                 return True
  154 |                 return True
  157 |                 return True
  160 |                 return True
  163 |                 return True
  166 |                 return True
  168 |             return False
  169 |         return False
  174 |                 return self._current
  188 |             return self._current
  193 |                 return
  215 |             return self.model
  220 |             return False
  223 |         return ModelRegistry._UseCtx(self, key, unload_after)
  229 |             return "cpu"
  234 |                     return "cuda"
  240 |                 return "dml"
  243 |         return "cpu"
  262 |                 return llm, device
  263 |             return _do
  275 |                 return (MusicGen.get_pretrained(repo, device=device if device != "dml" else "cpu"), device)
  276 |             return _do
  290 |             return t, device
  296 |             return rvc_manager, self.pick_device(spec)
  309 |             return m, device
  318 |             return WhisperModel(size, device=device if device != "dml" else "cpu",
  333 |             return (m, p), device
  356 |             return pipe, device
  361 |             return matchering, "cpu"
```

## `if` — 29 совпадений
```
  133 |         if not spec:
  137 |             if eng == "llama_cpp":
  140 |             if eng == "audiocraft_musicgen":
  143 |             if eng == "xtts_v2":
  146 |             if eng == "rvc":
  149 |             if eng == "demucs":
  152 |             if eng == "faster_whisper":
  155 |             if eng == "clap":
  158 |             if eng == "essentia_or_librosa":
  161 |             if eng == "diffusers":
  164 |             if eng == "matchering_plus":
  173 |             if self._current and self._current.key == key:
  175 |             if self._current is not None:
  178 |             if not spec:
  181 |             if not loader:
  192 |             if self._current is None:
  202 |                 if torch.cuda.is_available():
  218 |             if self.unload_after:
  228 |         if pref == "cpu":
  232 |             if pref in ("cuda", "auto") and torch.cuda.is_available():
  233 |                 if need <= self.hw.vram_gb:
  239 |             if pref in ("dml", "auto") and need <= self.hw.vram_gb:
  252 |                 if not mp.exists():
  273 |                 if device == "cpu" and spec.get("cpu_fallback"):
  285 |             if device == "cuda":
  304 |             if device == "cuda":
  328 |             if device == "cuda":
  344 |             if device == "cpu" and spec.get("cpu_fallback"):
  349 |             if device == "cuda":
```

## `for` — 1 совпадений
```
  264 |         for k in ("lyrics_llm", "analysis_llm", "metadata_llm"):
```

## `with` — 2 совпадений
```
  172 |         with self._lock:
  191 |         with self._lock:
```
