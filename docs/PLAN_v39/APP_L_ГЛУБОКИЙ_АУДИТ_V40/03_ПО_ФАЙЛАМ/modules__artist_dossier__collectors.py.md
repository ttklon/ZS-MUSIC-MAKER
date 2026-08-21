# АУДИТ ФАЙЛА: `modules/artist_dossier/collectors.py`

**LOC:** 96  |  **Размер:** 3763 байт  |  **Проблем:** 9  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 3 | `__future__.annotations` | from |
| 4 | `os` | import |
| 4 | `re` | import |
| 5 | `pathlib.Path` | from |
| 6 | `typing.Any` | from |
| 6 | `typing.Dict` | from |
| 6 | `typing.List` | from |
| 6 | `typing.Optional` | from |
| 55 | `lyricsgenius` | import |
| 77 | `yt_dlp` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 10 | `__init__` | 1 | 0 | ❌ |
| 13 | `collect` | 12 | 5 | ❌ |
| 29 | `__init__` | 1 | 0 | ❌ |
| 32 | `collect` | 11 | 3 | ❌ |
| 47 | `__init__` | 2 | 1 | ❌ |
| 51 | `collect` | 16 | 3 | ❌ |
| 71 | `__init__` | 2 | 0 | ❌ |
| 75 | `collect` | 21 | 5 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 9 | `LocalFolderCollector` | ❌ |
| 28 | `LyricVaultCollector` | ❌ |
| 46 | `GeniusCollector` | ❌ |
| 70 | `YouTubeCollector` | ❌ |

## Проблемы (детально, с цитатой кода)

### MISSING_CLASS_DOCSTRING — 4 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 9** — public class 'LocalFolderCollector' без docstring

  ```
          7 | 
          8 | 
  >>>     9 | class LocalFolderCollector:
         10 |     def __init__(self, folder: str):
         11 |         self.folder = Path(folder)
  ```

- **строка 28** — public class 'LyricVaultCollector' без docstring

  ```
         26 | 
         27 | 
  >>>    28 | class LyricVaultCollector:
         29 |     def __init__(self, vault_root: str):
         30 |         self.vault = Path(vault_root)
  ```

- **строка 46** — public class 'GeniusCollector' без docstring

  ```
         44 | 
         45 | 
  >>>    46 | class GeniusCollector:
         47 |     def __init__(self, token: Optional[str] = None, max_songs: int = 25):
         48 |         self.token = token or os.environ.get("GENIUS_TOKEN")
  ```

- **строка 70** — public class 'YouTubeCollector' без docstring

  ```
         68 | 
         69 | 
  >>>    70 | class YouTubeCollector:
         71 |     def __init__(self, out_dir: str, max_tracks: int = 10):
         72 |         self.out_dir = Path(out_dir)
  ```

### MISSING_DOCSTRING — 4 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 13** — public function 'collect' без docstring

  ```
         11 |         self.folder = Path(folder)
         12 | 
  >>>    13 |     def collect(self, artist: str) -> List[Dict[str, Any]]:
         14 |         if not self.folder.exists():
         15 |             return []
  ```

- **строка 32** — public function 'collect' без docstring

  ```
         30 |         self.vault = Path(vault_root)
         31 | 
  >>>    32 |     def collect(self, artist: str) -> List[Dict[str, Any]]:
         33 |         cand = [self.vault / "author_corpus" / artist,
         34 |                 self.vault / "author_corpus" / artist.lower(),
  ```

- **строка 51** — public function 'collect' без docstring

  ```
         49 |         self.max_songs = max_songs
         50 | 
  >>>    51 |     def collect(self, artist: str) -> List[Dict[str, Any]]:
         52 |         if not self.token:
         53 |             return []
  ```

- **строка 75** — public function 'collect' без docstring

  ```
         73 |         self.max_tracks = max_tracks
         74 | 
  >>>    75 |     def collect(self, artist: str, titles: Optional[List[str]] = None) -> List[Dict[str, Any]]:
         76 |         try:
         77 |             import yt_dlp
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 3** — import 'annotations' не используется в теле файла

  ```
          1 | # -*- coding: utf-8 -*-
          2 | """ZS Music Maker - modules/artist_dossier/collectors.py (v38)"""
  >>>     3 | from __future__ import annotations
          4 | import os, re
          5 | from pathlib import Path
  ```
