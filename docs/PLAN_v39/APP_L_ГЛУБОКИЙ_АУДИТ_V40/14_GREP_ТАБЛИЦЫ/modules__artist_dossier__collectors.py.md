# grep-таблицы `modules/artist_dossier/collectors.py`

## `import` — 6 совпадений
```
    3 | from __future__ import annotations
    4 | import os, re
    5 | from pathlib import Path
    6 | from typing import Any, Dict, List, Optional
   55 |             import lyricsgenius
   77 |             import yt_dlp
```

## `except` — 3 совпадений
```
   66 |         except Exception:
   78 |         except Exception:
   94 |             except Exception:
```

## `try` — 3 совпадений
```
   54 |         try:
   76 |         try:
   87 |             try:
```

## `def` — 8 совпадений
```
   10 |     def __init__(self, folder: str):
   13 |     def collect(self, artist: str) -> List[Dict[str, Any]]:
   29 |     def __init__(self, vault_root: str):
   32 |     def collect(self, artist: str) -> List[Dict[str, Any]]:
   47 |     def __init__(self, token: Optional[str] = None, max_songs: int = 25):
   51 |     def collect(self, artist: str) -> List[Dict[str, Any]]:
   71 |     def __init__(self, out_dir: str, max_tracks: int = 10):
   75 |     def collect(self, artist: str, titles: Optional[List[str]] = None) -> List[Dict[str, Any]]:
```

## `class` — 4 совпадений
```
    9 | class LocalFolderCollector:
   28 | class LyricVaultCollector:
   46 | class GeniusCollector:
   70 | class YouTubeCollector:
```

## `return` — 9 совпадений
```
   15 |             return []
   25 |         return out
   43 |         return out
   53 |             return []
   63 |                 return []
   64 |             return [{"title": s.title, "lyrics": s.lyrics,
   67 |             return []
   79 |             return []
   96 |         return results
```

## `if` — 6 совпадений
```
   14 |         if not self.folder.exists():
   18 |             if p.suffix.lower() not in (".mp3", ".wav", ".flac", ".m4a", ".ogg"):
   22 |             if m and m.group(1).strip().lower() == artist.lower():
   38 |             if not base.exists():
   52 |         if not self.token:
   62 |             if not a:
```

## `for` — 4 совпадений
```
   17 |         for p in sorted(self.folder.rglob("*")):
   37 |         for base in cand:
   40 |             for p in sorted(base.glob("*.txt")):
   82 |         for title in (titles or [artist])[: self.max_tracks]:
```

## `with` — 1 совпадений
```
   88 |                 with yt_dlp.YoutubeDL(opts) as ydl:
```
