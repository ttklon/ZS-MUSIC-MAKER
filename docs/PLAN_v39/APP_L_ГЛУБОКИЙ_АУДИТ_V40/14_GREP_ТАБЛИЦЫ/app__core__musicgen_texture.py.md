# grep-таблицы `app/core/musicgen_texture.py`

## `import` — 9 совпадений
```
   16 | from __future__ import annotations
   18 | import hashlib
   19 | from pathlib import Path
   20 | from typing import Any
   54 |         from audiocraft.models import MusicGen
   68 |         import torch
   89 |         import torch  # noqa: F401
   98 |         import audiocraft  # noqa: F401
  176 |             import torchaudio
```

## `print` — 4 совпадений
```
   60 |         print(f"[musicgen_texture] audiocraft недоступен: {e}")
  165 |         print(f"[musicgen_texture] BLOCKED: {avail['reason']} | {avail['install_hint']}")
  187 |             print(f"[musicgen_texture] generation failed: {e}")
  261 |     print(r)
```

## `except` — 5 совпадений
```
   59 |     except Exception as e:
   71 |     except Exception:
   90 |     except Exception as e:
   99 |     except Exception:
  186 |         except Exception as e:
```

## `try` — 5 совпадений
```
   53 |     try:
   67 |     try:
   88 |     try:
   97 |     try:
  167 |         try:
```

## `def` — 11 совпадений
```
   30 | def choose_size(vram_gb: float, quality_mode: str = "quality") -> str:
   49 | def _load_musicgen(size: str):
   64 | def unload_all() -> None:
   76 | def detect_availability() -> dict:
  114 | def get_status() -> dict:
  129 | def _cache_key(prompt: str, size: str, duration: int) -> str:
  135 | def generate_texture(
  200 | def generate_batch(
  214 | def _pink_noise_fallback(prompt: str, duration_sec: int, out_path: str) -> str:
  225 | def generate_atmosphere(vibe: str, duration_sec: int = 30, vram_gb: float = 4.0) -> str:
  246 | def generate_fx_hits(count: int = 5, vram_gb: float = 4.0) -> list[str]:
```

## `raise` — 1 совпадений
```
  218 |     raise RuntimeError(
```

## `return` — 17 совпадений
```
   37 |         return "large" if quality_mode != "fast" else "medium"
   40 |         return "medium" if quality_mode != "fast" else "small"
   42 |     return "small"
   52 |         return _MODEL_CACHE[size]
   58 |         return model
   61 |         return None
   91 |         return {
  100 |         return {
  106 |     return {
  117 |     return {
  131 |     return h
  152 |         return {
  179 |             return {
  190 |     return {
  210 |     return results
  243 |     return r.get("path", "")
  256 |     return [r["path"] for r in results if r.get("ok")]
```

## `if` — 7 совпадений
```
   35 |     if vram_gb >= 12:
   38 |     if vram_gb >= 6:
   51 |     if size in _MODEL_CACHE:
  151 |     if cached.exists() and cached.stat().st_size > 1000:
  162 |     if model is None:
  166 |     if model is not None:
  259 | if __name__ == "__main__":
```

## `for` — 2 совпадений
```
   25 | for d in (OUT_DIR, CACHE):
  208 |     for p in prompts:
```
