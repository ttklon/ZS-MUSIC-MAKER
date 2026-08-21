# grep-таблицы `modules/distribution_export_v11.py`

## `import` — 10 совпадений
```
    9 | from __future__ import annotations
   11 | import csv
   12 | import json
   13 | import os
   14 | import shutil
   15 | import sys
   16 | from dataclasses import asdict, dataclass, field
   17 | from datetime import datetime, timezone
   62 |             from app.core.isrc import is_valid_isrc, generate_isrc
  435 |     import tempfile
```

## `print` — 2 совпадений
```
   22 |         print(msg)
  474 |     print("distribution_export_v11 self-test:", "OK" if _self_test() else "FAIL")
```

## `except` — 3 совпадений
```
   23 |     except UnicodeEncodeError:
   70 |         except ImportError:
  100 |     except Exception as e:
```

## `try` — 3 совпадений
```
   21 |     try:
   61 |         try:
   94 |     try:
```

## `def` — 11 совпадений
```
   20 | def _safe_print(msg):
   50 |     def ensure(self):
   89 |     def existing(self) -> dict[str, str]:
   93 | def _copy_safe(src, dst) -> bool:
  105 | def build_spotify_package(meta, files, out_dir):
  170 | def build_yandex_vk_package(meta, files, out_dir):
  234 | def build_tiktok_package(meta, files, out_dir):
  309 | def build_youtube_package(meta, files, out_dir):
  382 | def build_shazam_package(meta, out_dir):
  405 | def build_all_distribution_packages(meta, files, out_dir):
  434 | def _self_test():
```

## `class` — 2 совпадений
```
   28 | class TrackMetadata:
   75 | class ReleaseFiles:
```

## `return` — 11 совпадений
```
   90 |         return {k: v for k, v in asdict(self).items() if v and os.path.exists(v)}
   96 |             return False
   99 |         return True
  102 |         return False
  167 |     return {"dir": d, "csv": csv_path, "json": json_path, "instructions": inst}
  231 |     return {"dir": d, "csv": csv_path, "instructions": inst}
  306 |     return {"dir": d, "caption": caption_path, "json": json_path, "instructions": inst}
  379 |     return {"dir": d, "instructions": inst, "json": ytj}
  402 |     return {"dir": d, "json": p}
  431 |     return result
  470 |         return ok
```

## `if` — 16 совпадений
```
   51 |         if not self.release_date:
   54 |         if not self.copyright:
   56 |         if not self.p_line:
   58 |         if not self.album:
   63 |             if not is_valid_isrc(self.isrc):
   68 |                 if gen:
   95 |         if not src or not os.path.exists(src):
  109 |     if _copy_safe(files.master_wav, os.path.join(d, "audio_master.wav")):
  113 |     if _copy_safe(files.cover_png, os.path.join(d, "cover.png")):
  173 |     if not _copy_safe(files.mp3_320, os.path.join(d, "track.mp3")):
  176 |     if files.lyrics_txt:
  237 |     if not _copy_safe(files.tiktok_mp4, os.path.join(d, "tiktok_edit.mp4")):
  257 |         if t.lower() not in seen:
  263 |         if meta.lyrics_en_hook:
  315 |     if files.lyrics_txt:
  473 | if __name__ == "__main__":
```

## `for` — 4 совпадений
```
  119 |         for row in [
  256 |     for t in all_tags:
  447 |         for p in ["m.wav", "m.mp3", "c.png", "l.txt", "t.mp4"]:
  460 |             for k in [
```

## `with` — 15 совпадений
```
  116 |     with open(csv_path, "w", encoding="utf-8", newline="") as f:
  141 |     with open(json_path, "w", encoding="utf-8") as f:
  146 |     with open(inst, "w", encoding="utf-8") as f:
  179 |     with open(csv_path, "w", encoding="utf-8", newline="") as f:
  214 |     with open(inst, "w", encoding="utf-8") as f:
  261 |     with open(caption_path, "w", encoding="utf-8") as f:
  267 |     with open(json_path, "w", encoding="utf-8") as f:
  284 |     with open(inst, "w", encoding="utf-8") as f:
  318 |     with open(desc_path, "w", encoding="utf-8") as f:
  339 |     with open(ytj, "w", encoding="utf-8") as f:
  361 |     with open(inst, "w", encoding="utf-8") as f:
  386 |     with open(p, "w", encoding="utf-8") as f:
  416 |     with open(manifest_path, "w", encoding="utf-8") as f:
  437 |     with tempfile.TemporaryDirectory() as tmp:
  448 |             with open(os.path.join(tmp, p), "wb") as f:
```

## `open` — 16 совпадений
```
  116 |     with open(csv_path, "w", encoding="utf-8", newline="") as f:
  141 |     with open(json_path, "w", encoding="utf-8") as f:
  146 |     with open(inst, "w", encoding="utf-8") as f:
  179 |     with open(csv_path, "w", encoding="utf-8", newline="") as f:
  214 |     with open(inst, "w", encoding="utf-8") as f:
  261 |     with open(caption_path, "w", encoding="utf-8") as f:
  267 |     with open(json_path, "w", encoding="utf-8") as f:
  271 |                 "description": open(caption_path, encoding="utf-8").read(),
  284 |     with open(inst, "w", encoding="utf-8") as f:
  318 |     with open(desc_path, "w", encoding="utf-8") as f:
  339 |     with open(ytj, "w", encoding="utf-8") as f:
  344 |                     "description": open(desc_path, encoding="utf-8").read(),
  361 |     with open(inst, "w", encoding="utf-8") as f:
  386 |     with open(p, "w", encoding="utf-8") as f:
  416 |     with open(manifest_path, "w", encoding="utf-8") as f:
  448 |             with open(os.path.join(tmp, p), "wb") as f:
```
