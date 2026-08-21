# grep-таблицы `modules/release_export.py`

## `import` — 12 совпадений
```
   20 | import csv
   21 | import json
   22 | import os
   23 | import shutil
   24 | import time
   25 | from pathlib import Path
   45 |         from pydub import AudioSegment
   76 |         from mutagen.easyid3 import EasyID3
   77 |         from mutagen.mp3 import MP3
  107 |         from mutagen.flac import FLAC
  142 |             from modules.user_profile import get_artist_name
  223 |     from app.core.isrc import get_isrc
```

## `print` — 3 совпадений
```
   58 |         print(f"[release_export._copy_or_convert] {e}")
   95 |         print(f"[release_export._write_id3] {e}")
  267 |     print("release_export v7 ready")
```

## `except` — 7 совпадений
```
   42 |         except Exception:
   57 |     except Exception as e:
   62 |         except Exception:
   81 |         except Exception:
   94 |     except Exception as e:
  116 |     except Exception:
  145 |         except Exception:
```

## `try` — 7 совпадений
```
   39 |         try:
   44 |     try:
   59 |         try:
   75 |     try:
   79 |         try:
  106 |     try:
  141 |         try:
```

## `def` — 4 совпадений
```
   32 | def _copy_or_convert(src: str, dst: str) -> bool:
   66 | def _write_id3(
   99 | def _write_flac_tags(
  120 | def export_release(
```

## `return` — 11 совпадений
```
   35 |         return False
   41 |             return True
   43 |             return False
   56 |         return True
   61 |             return True
   63 |             return False
   93 |         return True
   96 |         return False
  115 |         return True
  117 |         return False
  257 |     return {
```

## `if` — 20 совпадений
```
   34 |     if not os.path.exists(src):
   38 |     if ext_src == ext_dst:
   48 |         if ext_dst == ".mp3":
   90 |         if year:
  140 |     if not artist_name:
  155 |     if master_path and os.path.exists(master_path):
  158 |             if _copy_or_convert(master_path, str(p)):
  160 |         if "master.mp3" in files:
  164 |         if "master.flac" in files:
  168 |     if beat_path and os.path.exists(beat_path):
  171 |             if _copy_or_convert(beat_path, str(p)):
  173 |         if "instrumental.mp3" in files:
  182 |     if vocal_path and os.path.exists(vocal_path):
  185 |             if _copy_or_convert(vocal_path, str(p)):
  190 |         if stands and stands.get(stand_name):
  192 |             if os.path.exists(src):
  194 |                 if _copy_or_convert(src, str(p)):
  198 |     if lyrics:
  203 |     if recipe:
  266 | if __name__ == "__main__":
```

## `for` — 4 совпадений
```
  156 |         for ext in ("wav", "mp3", "flac"):
  169 |         for ext in ("wav", "mp3"):
  183 |         for ext in ("wav", "mp3"):
  189 |     for stand_name in ("car", "club", "streaming"):
```

## `with` — 1 совпадений
```
  237 |     with open(rel_dir / "metadata.csv", "w", encoding="utf-8", newline="") as f:
```

## `open` — 1 совпадений
```
  237 |     with open(rel_dir / "metadata.csv", "w", encoding="utf-8", newline="") as f:
```
