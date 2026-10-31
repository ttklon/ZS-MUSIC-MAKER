# -*- coding: utf-8 -*-
"""
modules/artist_dossier — досье артистов и треков.

Пайплайн на трек: demucs → whisper (ASR) → librosa/DSP → CLAP → analysis_llm.
Схема досье версионируется в `data/artist_dossier/schema.json`.
"""

from modules.artist_dossier.manager import DossierManager  # noqa: F401
from modules.artist_dossier.models import ArtistEntry, TrackEntry  # noqa: F401
from modules.artist_dossier.schema import (  # noqa: F401
    artist_dossier_schema,
    normalize_artist_dossier,
    validate_artist_dossier,
)

__all__ = [
    "ArtistEntry",
    "DossierManager",
    "TrackEntry",
    "artist_dossier_schema",
    "normalize_artist_dossier",
    "validate_artist_dossier",
]
