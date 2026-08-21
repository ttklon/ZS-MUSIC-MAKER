# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/artist_dossier/collectors.py`

**Всего строк:** 96

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 38 | 39.6 |
| blank | 12 | 12.5 |
| return | 9 | 9.4 |
| def | 8 | 8.3 |
| import | 6 | 6.2 |
| branch | 6 | 6.2 |
| try_block | 6 | 6.2 |
| class | 4 | 4.2 |
| loop | 4 | 4.2 |
| comment | 1 | 1.0 |
| docstring | 1 | 1.0 |
| stmt | 1 | 1.0 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """ZS Music Maker - modules/artist_dossier/collectors.py (v38)"""
    3 [import    ] from __future__ import annotations
    4 [import    ] import os, re
    5 [import    ] from pathlib import Path
    6 [import    ] from typing import Any, Dict, List, Optional
    7 [blank     ] 
    8 [blank     ] 
    9 [class     ] class LocalFolderCollector:
   10 [def       ]     def __init__(self, folder: str):
   11 [code      ]         self.folder = Path(folder)
   12 [blank     ] 
   13 [def       ]     def collect(self, artist: str) -> List[Dict[str, Any]]:
   14 [branch    ]         if not self.folder.exists():
   15 [return    ]             return []
   16 [code      ]         out = []
   17 [loop      ]         for p in sorted(self.folder.rglob("*")):
   18 [branch    ]             if p.suffix.lower() not in (".mp3", ".wav", ".flac", ".m4a", ".ogg"):
   19 [code      ]                 continue
   20 [code      ]             title = p.stem
   21 [code      ]             m = re.match(r"^(.+?)\s*-\s*(.+)$", title)
   22 [branch    ]             if m and m.group(1).strip().lower() == artist.lower():
   23 [code      ]                 title = m.group(2).strip()
   24 [code      ]             out.append({"title": title, "audio_path": str(p)})
   25 [return    ]         return out
   26 [blank     ] 
   27 [blank     ] 
   28 [class     ] class LyricVaultCollector:
   29 [def       ]     def __init__(self, vault_root: str):
   30 [code      ]         self.vault = Path(vault_root)
   31 [blank     ] 
   32 [def       ]     def collect(self, artist: str) -> List[Dict[str, Any]]:
   33 [code      ]         cand = [self.vault / "author_corpus" / artist,
   34 [code      ]                 self.vault / "author_corpus" / artist.lower(),
   35 [code      ]                 self.vault / "author_corpus" / artist.replace(" ", "_")]
   36 [code      ]         out = []
   37 [loop      ]         for base in cand:
   38 [branch    ]             if not base.exists():
   39 [code      ]                 continue
   40 [loop      ]             for p in sorted(base.glob("*.txt")):
   41 [code      ]                 out.append({"title": p.stem,
   42 [code      ]                             "lyrics": p.read_text(encoding="utf-8", errors="ignore")})
   43 [return    ]         return out
   44 [blank     ] 
   45 [blank     ] 
   46 [class     ] class GeniusCollector:
   47 [def       ]     def __init__(self, token: Optional[str] = None, max_songs: int = 25):
   48 [code      ]         self.token = token or os.environ.get("GENIUS_TOKEN")
   49 [code      ]         self.max_songs = max_songs
   50 [blank     ] 
   51 [def       ]     def collect(self, artist: str) -> List[Dict[str, Any]]:
   52 [branch    ]         if not self.token:
   53 [return    ]             return []
   54 [try_block ]         try:
   55 [import    ]             import lyricsgenius
   56 [code      ]             g = lyricsgenius.Genius(self.token, timeout=30, retries=2,
   57 [code      ]                                     remove_section_headers=False)
   58 [code      ]             g.verbose = False
   59 [code      ]             g.skip_non_songs = True
   60 [code      ]             a = g.search_artist(artist, max_songs=self.max_songs,
   61 [code      ]                                 sort="popularity", get_full_info=False)
   62 [branch    ]             if not a:
   63 [return    ]                 return []
   64 [return    ]             return [{"title": s.title, "lyrics": s.lyrics,
   65 [code      ]                      "external_url": s.url} for s in a.songs if s.lyrics]
   66 [try_block ]         except Exception:
   67 [return    ]             return []
   68 [blank     ] 
   69 [blank     ] 
   70 [class     ] class YouTubeCollector:
   71 [def       ]     def __init__(self, out_dir: str, max_tracks: int = 10):
   72 [code      ]         self.out_dir = Path(out_dir)
   73 [code      ]         self.max_tracks = max_tracks
   74 [blank     ] 
   75 [def       ]     def collect(self, artist: str, titles: Optional[List[str]] = None) -> List[Dict[str, Any]]:
   76 [try_block ]         try:
   77 [import    ]             import yt_dlp
   78 [try_block ]         except Exception:
   79 [return    ]             return []
   80 [code      ]         self.out_dir.mkdir(parents=True, exist_ok=True)
   81 [code      ]         results = []
   82 [loop      ]         for title in (titles or [artist])[: self.max_tracks]:
   83 [code      ]             opts = {"format": "bestaudio/best", "quiet": True,
   84 [code      ]                     "outtmpl": str(self.out_dir / f"{artist}_{title}.%(ext)s"),
   85 [code      ]                     "postprocessors": [{"key": "FFmpegExtractAudio",
   86 [code      ]                                         "preferredcodec": "wav"}]}
   87 [try_block ]             try:
   88 [stmt      ]                 with yt_dlp.YoutubeDL(opts) as ydl:
   89 [code      ]                     info = ydl.extract_info(f"ytsearch1:{artist} {title}", download=True)
   90 [code      ]                     entry = info["entries"][0] if "entries" in info else info
   91 [code      ]                     results.append({"title": title,
   92 [code      ]                                     "audio_path": str(self.out_dir / f"{artist}_{title}.wav"),
   93 [code      ]                                     "external_url": entry.get("webpage_url")})
   94 [try_block ]             except Exception:
   95 [code      ]                 continue
   96 [return    ]         return results
```