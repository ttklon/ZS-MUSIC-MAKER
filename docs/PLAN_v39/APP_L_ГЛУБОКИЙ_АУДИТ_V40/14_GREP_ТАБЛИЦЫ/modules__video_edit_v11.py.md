# grep-таблицы `modules/video_edit_v11.py`

## `import` — 11 совпадений
```
   15 | from __future__ import annotations
   17 | import json
   18 | import math
   19 | import os
   20 | import struct
   21 | import sys
   22 | import wave
   23 | from dataclasses import asdict, dataclass
  207 |         import moviepy.editor as mpy
  217 |         from PIL import Image, ImageDraw, ImageFilter, ImageFont
  256 |     from app.core.font_utils import load_pil_font
```

## `print` — 2 совпадений
```
   28 |         print(msg)
  464 |     print("video_edit_v11 self-test:", "OK" if _self_test() else "FAIL")
```

## `except` — 12 совпадений
```
   29 |     except UnicodeEncodeError:
  135 |     except Exception as e:
  194 |                             except Exception:
  199 |     except Exception as e:
  210 |     except Exception as e:
  220 |     except Exception:
  233 |         except Exception:
  281 |         except Exception as e:
  333 |             except Exception as e:
  352 |         except Exception:
  385 |     except Exception as e:
  410 |     except Exception as e:
```

## `try` — 13 совпадений
```
   27 |     try:
  133 |     try:
  172 |     try:
  190 |                             try:
  206 |     try:
  216 |     try:
  231 |         try:
  279 |         try:
  318 |             try:
  337 |     try:
  349 |         try:
  369 |     try:
  389 |     try:
```

## `def` — 16 совпадений
```
   26 | def _safe_print(msg: str) -> None:
   48 |     def resolution(self) -> tuple[int, int]:
   66 |     def to_dict(self) -> dict:
   72 | def _read_wav_mono(path: str) -> tuple[list[float], int]:
  119 | def _rms_windows(samples: list[float], sr: int, win_sec: float = 1.0) -> list[float]:
  131 | def detect_hook(master_wav: str, target_sec: int = 20) -> tuple[float, float]:
  170 | def _parse_lrc(lrc_path: str) -> list[tuple[float, str]]:
  205 | def _try_moviepy():
  215 | def _try_pil():
  224 | def _make_static_bg(cover_path: str | None, size: tuple[int, int]):
  248 | def _draw_title(bg_img, title: str, artist: str, size: tuple[int, int]):
  268 | def build_video(req: VideoEditRequest) -> VideoEditResult:
  286 | def _build_with_moviepy(req, hook_start, hook_end, tmp_dir, mpy) -> VideoEditResult:
  365 | def _build_fallback(req, hook_start, hook_end) -> VideoEditResult:
  423 | def build_release_edits(
  452 | def _self_test() -> bool:
```

## `class` — 2 совпадений
```
   34 | class VideoEditRequest:
   57 | class VideoEditResult:
```

## `raise` — 1 совпадений
```
  115 |         raise ValueError(f"Unsupported sample width: {sw}")
```

## `return` — 25 совпадений
```
   50 |             return (1080, 1920)
   52 |             return (1920, 1080)
   53 |         return (1080, 1080)
   69 |         return d
  116 |     return mono, sr
  128 |     return out
  137 |         return (0.0, float(target_sec))
  140 |         return (0.0, total)
  144 |         return (0.0, float(target_sec))
  167 |     return (float(best_start), float(best_start + w))
  202 |     return out
  209 |         return mpy
  212 |         return None
  219 |         return (Image, ImageDraw, ImageFont, ImageFilter)
  221 |         return None
  227 |         return None
  245 |     return bg
  251 |         return bg_img
  265 |     return bg_img
  280 |             return _build_with_moviepy(req, hook_start, hook_end, tmp_dir, mpy)
  283 |     return _build_fallback(req, hook_start, hook_end)
  354 |     return VideoEditResult(
  412 |     return VideoEditResult(
  449 |     return manifest
  460 |     return ok
```

## `if` — 32 совпадений
```
   49 |         if self.orientation == "vertical":
   51 |         if self.orientation == "horizontal":
   79 |     if sw == 2:
   82 |         if n_ch == 1:
   97 |                 if len(b) < 3:
  107 |         if n_ch == 1:
  124 |         if not chunk:
  139 |     if total <= target_sec + 1:
  143 |     if w >= len(rms):
  148 |     if running > best_sum:
  152 |         if running > best_sum:
  155 |     if best_start < 0.25 * len(rms):
  157 |         if half + w <= len(rms):
  163 |                 if running > alt_best:
  165 |             if alt_best >= 0.85 * best_sum:
  176 |                 if not line or not line.startswith("["):
  179 |                 if end < 0:
  184 |                     if head[i] == "[":
  186 |                         if j < 0:
  189 |                         if ":" in tag and any(c.isdigit() for c in tag):
  226 |     if not pil:
  230 |     if cover_path and os.path.exists(cover_path):
  250 |     if not pil or bg_img is None:
  259 |     if artist:
  263 |     if title:
  278 |     if mpy is not None:
  293 |     if bg_img is not None:
  296 |     if bg_png:
  301 |     if req.beat_glow and req.bpm > 40:
  313 |     if req.lyrics_overlay and req.lyrics_lrc and os.path.exists(req.lyrics_lrc):
  315 |             if not text.strip() or t < hook_start or t > hook_end:
  463 | if __name__ == "__main__":
```

## `for` — 11 совпадений
```
   86 |             for i in range(0, count, n_ch):
   92 |         for i in range(0, len(frames), step):
   94 |             for c in range(n_ch):
  111 |             for i in range(0, count, n_ch):
  122 |     for i in range(0, len(samples), win):
  150 |     for i in range(1, len(rms) - w + 1):
  161 |             for i in range(half + 1, len(rms) - w + 1):
  174 |             for line in f:
  314 |         for t, text in _parse_lrc(req.lyrics_lrc):
  381 |                     for x in cut
  428 |     for name, orient, dur in [
```

## `while` — 2 совпадений
```
  183 |                 while i < len(head):
  304 |         while t < duration:
```

## `with` — 6 совпадений
```
   73 |     with wave.open(path, "rb") as wf:
  173 |         with open(lrc_path, "r", encoding="utf-8", errors="ignore") as f:
  374 |         with wave.open(wav_out, "wb") as wf:
  390 |         with open(txt_path, "w", encoding="utf-8") as f:
  445 |     with open(
  454 |     with open(tmp, "w", encoding="utf-8") as f:
```

## `path_home` — 1 совпадений
```
  453 |     tmp = "/tmp/_v11_lrc_test.lrc"
```

## `open` — 7 совпадений
```
   73 |     with wave.open(path, "rb") as wf:
  173 |         with open(lrc_path, "r", encoding="utf-8", errors="ignore") as f:
  232 |             cover = Image.open(cover_path).convert("RGB")
  374 |         with wave.open(wav_out, "wb") as wf:
  390 |         with open(txt_path, "w", encoding="utf-8") as f:
  445 |     with open(
  454 |     with open(tmp, "w", encoding="utf-8") as f:
```
