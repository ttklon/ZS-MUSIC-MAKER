# -*- coding: utf-8 -*-
"""ZS Music Maker - modules/artist_dossier/collectors.py (v38)"""
from __future__ import annotations
import os, re
from pathlib import Path
from typing import Any, Dict, List, Optional


class LocalFolderCollector:
    def __init__(self, folder: str):
        self.folder = Path(folder)

    def collect(self, artist: str) -> List[Dict[str, Any]]:
        if not self.folder.exists():
            return []
        audio_suffixes = {".mp3", ".wav", ".flac", ".m4a", ".ogg"}
        tracks: Dict[str, Dict[str, Any]] = {}
        for path in sorted(self.folder.rglob("*")):
            suffix = path.suffix.lower()
            if suffix not in audio_suffixes | {".txt"}:
                continue
            title = path.stem
            match = re.match(r"^(.+?)\s*-\s*(.+)$", title)
            if match and match.group(1).strip().lower() == artist.lower():
                title = match.group(2).strip()
            key = title.casefold()
            entry = tracks.setdefault(key, {"title": title})
            if suffix in audio_suffixes:
                entry["audio_path"] = str(path)
            else:
                lyrics = path.read_text(encoding="utf-8", errors="ignore").strip()
                if lyrics:
                    entry["lyrics"] = lyrics
        return [tracks[key] for key in sorted(tracks)]


class LyricVaultCollector:
    def __init__(self, vault_root: str):
        self.vault = Path(vault_root)

    def collect(self, artist: str) -> List[Dict[str, Any]]:
        cand = [self.vault / "author_corpus" / artist,
                self.vault / "author_corpus" / artist.lower(),
                self.vault / "author_corpus" / artist.replace(" ", "_")]
        out = []
        for base in cand:
            if not base.exists():
                continue
            for p in sorted(base.glob("*.txt")):
                out.append({"title": p.stem,
                            "lyrics": p.read_text(encoding="utf-8", errors="ignore")})
        return out


class GeniusCollector:
    def __init__(self, token: Optional[str] = None, max_songs: int = 25):
        self.token = token or os.environ.get("GENIUS_TOKEN")
        self.max_songs = max_songs

    def collect(self, artist: str) -> List[Dict[str, Any]]:
        if not self.token:
            return []
        try:
            import lyricsgenius
            g = lyricsgenius.Genius(self.token, timeout=30, retries=2,
                                    remove_section_headers=False)
            g.verbose = False
            g.skip_non_songs = True
            a = g.search_artist(artist, max_songs=self.max_songs,
                                sort="popularity", get_full_info=False)
            if not a:
                return []
            return [{"title": s.title, "lyrics": s.lyrics,
                     "external_url": s.url} for s in a.songs if s.lyrics]
        except Exception:
            return []


class YouTubeCollector:
    def __init__(self, out_dir: str, max_tracks: int = 10):
        self.out_dir = Path(out_dir)
        self.max_tracks = max_tracks

    def collect(self, artist: str, titles: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        try:
            import yt_dlp
        except Exception:
            return []
        self.out_dir.mkdir(parents=True, exist_ok=True)
        results = []
        for title in (titles or [artist])[: self.max_tracks]:
            opts = {"format": "bestaudio/best", "quiet": True,
                    "outtmpl": str(self.out_dir / f"{artist}_{title}.%(ext)s"),
                    "postprocessors": [{"key": "FFmpegExtractAudio",
                                        "preferredcodec": "wav"}]}
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(f"ytsearch1:{artist} {title}", download=True)
                    entry = info["entries"][0] if "entries" in info else info
                    results.append({"title": title,
                                    "audio_path": str(self.out_dir / f"{artist}_{title}.wav"),
                                    "external_url": entry.get("webpage_url")})
            except Exception:
                continue
        return results
