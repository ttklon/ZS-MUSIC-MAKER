# -*- coding: utf-8 -*-
"""
agents/sample_hunter/config.py — пути, расширения и жанровые ключевые слова
для поиска сэмплов. Только данные, никакой сети.
"""

from __future__ import annotations

from pathlib import Path

try:  # сеть опциональна: без requests работает только локальная библиотека
    import requests

    HAS_REQ = True
except Exception:  # pragma: no cover - окружение без requests
    requests = None
    HAS_REQ = False

ROOT = Path(__file__).resolve().parents[2]
LOCAL_LIB = ROOT / "samples_cache"
CACHE = LOCAL_LIB
MANIFEST_DIR = ROOT / "data" / "sample_manifests"

AUDIO_EXT = (".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aiff")

GENRE_KEYWORDS: dict[str, list[str]] = {
    "phonk / drift": [
        "808 kick", "cowbell phonk", "vinyl hiss", "memphis vocal chop",
        "drift phonk sample", "japanese vocal chop", "808 slide", "phonk snare",
        "phonk hihat roll", "supra engine",
    ],
    "dance / edm": [
        "big room synth", "future bass chord", "dance kick", "edm riser",
        "reverse cymbal", "dance clap", "vocal chop edm", "sidechain pad",
    ],
    "trap / hip-hop": [
        "trap 808", "hip-hop snare", "hip-hop kick", "trap hihat",
        "sample trap loop", "vocal chop trap", "trap riser", "trap open hat",
    ],
    "pop / r&b": [
        "rnb chord loop", "pop drum loop", "pop clap", "vocal chop rnb",
        "smooth piano loop", "airy pad", "pop snare",
    ],
    "hardstyle / techno": [
        "hardstyle kick", "reverse kick", "techno hat", "techno bass",
        "acid loop", "techno stab",
    ],
    "generic hit": [
        "kick drum", "snare drum", "hihat loop", "bass loop", "vocal chop",
        "riser fx", "impact fx",
    ],
}


# --------------------------------------------------------------------------- #
