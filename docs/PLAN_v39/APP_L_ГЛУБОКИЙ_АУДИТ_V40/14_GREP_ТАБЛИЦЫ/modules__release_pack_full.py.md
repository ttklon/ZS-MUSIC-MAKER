# grep-таблицы `modules/release_pack_full.py`

## `import` — 21 совпадений
```
   50 | from __future__ import annotations
   52 | import json
   53 | import shutil
   54 | import time
   55 | import wave
   56 | from pathlib import Path
   57 | from typing import Any
   60 |     import numpy as np
   65 |     import soundfile as sf
   70 |     from pydub import AudioSegment
   77 |     from PIL import Image, ImageDraw, ImageFilter, ImageFont
  258 |         from scipy.signal import butter, sosfiltfilt
  396 |     from app.core.isrc import get_isrc
  475 |     from app.core.isrc import get_isrc
  491 |     from app.core.isrc import is_placeholder_isrc
  540 |         from app.core.isrc import generate_isrc
  859 |     from mutagen.id3 import (
  884 |     from app.core.isrc import get_isrc as _get_isrc
  904 |             import sys as _s
  913 |     import tempfile
  921 |     import numpy as _np
```

## `print` — 3 совпадений
```
  916 |         print("soundfile not available")
  945 |     print(
  952 |     print("Files:", len(result["files"]))
```

## `except` — 24 совпадений
```
   61 | except Exception:
   66 | except Exception:
   73 | except Exception:
   80 | except Exception:
  174 |     except Exception:
  281 |     except Exception:
  318 |     except Exception:
  377 |         except Exception:
  385 |     except Exception as e:
  605 |     except Exception as e:
  619 |     except Exception as e:
  635 |     except Exception as e:
  648 |     except Exception as e:
  663 |             except Exception as e:
  682 |             except Exception as e:
  717 |             except Exception as e:
  738 |     except Exception as e:
  819 |     except Exception as e:
  830 |     except Exception as e:
  836 |     except Exception as e:
  844 |     except Exception as e:
  875 |     except Exception:
  900 |     except Exception as e:
  906 |         except Exception:
```

## `try` — 24 совпадений
```
   59 | try:
   64 | try:
   69 | try:
   76 | try:
  171 |     try:
  257 |     try:
  300 |     try:
  365 |     try:
  375 |         try:
  600 |     try:
  609 |     try:
  623 |     try:
  639 |     try:
  654 |             try:
  672 |             try:
  708 |             try:
  724 |     try:
  742 |     try:
  826 |     try:
  832 |     try:
  840 |     try:
  873 |     try:
  888 |     try:
  903 |         try:
```

## `def` — 23 совпадений
```
   87 | def _read_wav(path: str):
  112 | def _write_wav(path: str, data, sr: int, subtype: str = "PCM_16") -> bool:
  119 | def _ensure_stereo(data):
  127 | def _hires_resample_48k(data, sr_in: int):
  149 | def _make_cover(
  203 | def _lyrics_to_lrc(lyrics_text: str, total_sec: float) -> str:
  217 | def _lyrics_to_srt(lyrics_text: str, total_sec: float) -> str:
  227 |         def fmt(t):
  240 | def _fake_stems(master_wav: str, out_dir: Path) -> dict[str, str]:
  260 |         def band(lo, hi):
  289 | def _instrumental_and_acapella(
  329 | def _find_hook(data, sr: int) -> float:
  353 | def _make_clip(
  392 | def _distrokid_xml(meta: dict[str, Any]) -> str:
  425 | def _spotify_description(meta: dict[str, Any]) -> str:
  436 | def _youtube_description_html(meta: dict[str, Any]) -> str:
  463 | def _vk_prefill(meta: dict[str, Any]) -> str:
  473 | def _shazam_jsonld(meta: dict[str, Any]) -> str:
  489 | def _is_placeholder_isrc(isrc: str) -> bool:
  495 | def _is_placeholder_upc(upc: str) -> bool:
  502 | def _production_notes(
  570 | def build_pack(
  858 | def _apply_id3(mp3_path: Path, meta: dict[str, Any], cover_path: Path):
```

## `raise` — 3 совпадений
```
  658 |                     raise ValueError("empty master path")
  676 |                     raise ValueError("empty stem path")
  917 |         raise SystemExit(1)
```

## `return` — 41 совпадений
```
   91 |         return data, sr
  101 |         return raw, sr
  109 |     return arr, sr
  115 |         return True
  116 |     return False
  121 |         return data
  123 |         return np.stack([data, data], axis=1)
  124 |     return data
  130 |         return data, 48000
  136 |         return out, 48000
  143 |     return np.stack([L, R], axis=1), 48000
  153 |         return False
  197 |     return True
  206 |         return "[00:00.00]ZS Music Maker\n"
  214 |     return "\n".join(out) + "\n"
  220 |         return "1\n00:00:00,000 --> 00:00:03,000\nZS Music Maker\n"
  231 |             return f"{h:02d}:{m:02d}:{int(t)%60:02d},{int((t-int(t))*1000):03d}"
  234 |     return "\n".join(out)
  252 |         return result
  265 |                 return data
  269 |             return np.stack([L, R], axis=1).astype(np.float32)
  286 |     return result
  296 |         return {
  323 |     return result
  333 |         return 30.0
  340 |         return 0.0
  348 |         return 0.0
  350 |     return float(idx)
  364 |         return {"path": None, "fallback_used": True, "reason": "pydub_missing"}
  384 |         return info
  386 |         return {"path": None, "fallback_used": True, "reason": str(e)}
  422 |     return xml
  427 |     return (
  440 |     return f"""<!doctype html>
  465 |     return (
  486 |     return json.dumps(payload, ensure_ascii=False, indent=2)
  492 |     return is_placeholder_isrc(isrc)
  497 |         return True
  499 |     return s == "0000000000000" or set(s) <= {"0"}
  550 |     return "\n".join(lines) + "\n"
  847 |     return {
```

## `if` — 53 совпадений
```
   89 |     if sf is not None:
  100 |     if np is None:
  103 |     if sw == 2:
  107 |     if nch == 2:
  113 |     if sf is not None:
  120 |     if np is None:
  122 |     if data.ndim == 1:
  129 |     if np is None or sr_in == 48000:
  131 |     if data.ndim == 1:
  152 |     if not HAS_PIL:
  193 |     if jpg:
  205 |     if not lines:
  219 |     if not lines:
  246 |     if sf is None or np is None:
  254 |     if data.ndim == 1:
  264 |             if lo_n >= hi_n:
  293 |     if sf is None or np is None:
  306 |             if x.ndim == 1:
  332 |     if np is None or sf is None:
  334 |     if data.ndim > 1:
  339 |     if len(mono) <= win:
  347 |     if len(energy) == 0:
  363 |     if not HAS_PYDUB:
  367 |         if start_sec is None:
  496 |     if not upc:
  519 |         if s.get("fallback_used"):
  521 |         if s.get("blocked"):
  523 |         if s.get("synthetic"):
  539 |     if _is_placeholder_isrc(meta.get("isrc", "")):
  546 |     if _is_placeholder_upc(meta.get("upc", "")):
  610 |         if sf is not None and np is not None:
  624 |         if sf is not None:
  627 |             if sr != 48000 and np is not None:
  640 |         if HAS_PYDUB:
  652 |     if masters_map:
  655 |                 if isinstance(src, dict):
  657 |                 if not src:
  668 |     if stems_map:
  673 |                 if isinstance(src, dict):
  675 |                 if not src:
  699 |     if HAS_PYDUB:
  710 |                 if info.get("path"):
  713 |                     if info.get("fallback_used"):
  772 |         if _tt:
  778 |         if _actions_h:
  783 |         if isinstance(_metr, dict) and _metr:
  786 |                 if isinstance(v, dict):
  827 |         if _make_cover(out / "cover.png", title, artist, genre, size=3000):
  833 |         if _make_cover(out / "cover.jpg", title, artist, genre, size=1400, jpg=True):
  842 |         if mp3_path.exists():
  889 |         if cover_path.exists():
  911 | if __name__ == "__main__":
  915 |     if sf is None:
```

## `for` — 17 совпадений
```
  158 |     for r in range(size // 6, 0, -20):
  209 |     for i, ln in enumerate(lines):
  223 |     for i, ln in enumerate(lines):
  248 |         for name in ("drums", "bass", "vocals", "other"):
  277 |         for name, d in stems_data.items():
  282 |         for name in ("drums", "bass", "vocals", "other"):
  305 |         for x in (drums, bass, other, voc):
  344 |             for i in range(0, len(mono) - win, sr)
  517 |     for s in stages or []:
  533 |     for k, v in (hit_metrics or {}).items():
  653 |         for name, src in masters_map.items():
  671 |         for name, src in stems_map.items():
  687 |         for p in used_stems.values():
  694 |     for p in inst_map.values():
  707 |         for fname, dur in clip_defs:
  780 |             for act in _actions_h[:10]:
  785 |             for k, v in _metr.items():
```

## `with` — 2 совпадений
```
   93 |     with wave.open(path, "rb") as w:
  890 |             with open(cover_path, "rb") as f:
```

## `todo` — 1 совпадений
```
  395 |     # v39.4 (ШАГ 003): реальный ISRC вместо заглушки XX-XXX-00-00000
```

## `open` — 2 совпадений
```
   93 |     with wave.open(path, "rb") as w:
  890 |             with open(cover_path, "rb") as f:
```

## `np` — 19 совпадений
```
   99 |     dtype = {1: np.int8, 2: np.int16, 4: np.int32}[sw] if np else None
  102 |     arr = np.frombuffer(raw, dtype=dtype).astype(np.float32)
  123 |         return np.stack([data, data], axis=1)
  133 |         x_in = np.linspace(0, 1, len(data), endpoint=False)
  134 |         x_out = np.linspace(0, 1, n_out, endpoint=False)
  135 |         out = np.interp(x_out, x_in, data).astype(np.float32)
  139 |     x_in = np.linspace(0, 1, data.shape[0], endpoint=False)
  140 |     x_out = np.linspace(0, 1, n_out, endpoint=False)
  141 |     L = np.interp(x_out, x_in, data[:, 0]).astype(np.float32)
  142 |     R = np.interp(x_out, x_in, data[:, 1]).astype(np.float32)
  143 |     return np.stack([L, R], axis=1), 48000
  269 |             return np.stack([L, R], axis=1).astype(np.float32)
  310 |         peak = max(1e-9, float(np.max(np.abs(inst))))
  311 |         inst = (inst / peak * 0.9).astype(np.float32)
  312 |         vocp = max(1e-9, float(np.max(np.abs(voc))))
  313 |         voc = (voc / vocp * 0.9).astype(np.float32)
  341 |     energy = np.array(
  343 |             float(np.sqrt(np.mean(mono[i : i + win] ** 2)))
  349 |     idx = int(np.argmax(energy))
```

## `sf` — 8 совпадений
```
   90 |         data, sr = sf.read(path, always_2d=False)
  114 |         sf.write(path, data, sr, subtype=subtype)
  279 |             sf.write(dst, d, sr, subtype="PCM_16")
  314 |         sf.write(out_dir / "instrumental.wav", inst, sr, subtype="PCM_16")
  315 |         sf.write(out_dir / "acapella.wav", voc, sr, subtype="PCM_16")
  614 |             sf.write(dst_hi, data_hi, sr_hi, subtype="PCM_24")
  630 |             sf.write(dst_flac, data_hi, sr_hi, subtype="PCM_24", format="FLAC")
  927 |     sf.write(src, data, sr, subtype="PCM_16")
```
