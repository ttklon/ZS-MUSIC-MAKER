# -*- coding: utf-8 -*-
"""
modules/artist_dossier/models.py — персистентные записи досье.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TrackEntry:
    track_id: str
    title: str
    artist: str
    audio_path: Optional[str] = None
    external_url: Optional[str] = None
    lyrics: Optional[str] = None
    audio_copy: Dict[str, Any] = field(default_factory=dict)
    features: Dict[str, Any] = field(default_factory=dict)
    dossier: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    added_at: float = 0.0


@dataclass
class ArtistEntry:
    artist: str
    slug: str
    tracks: List[str] = field(default_factory=list)
    dossier: Dict[str, Any] = field(default_factory=dict)
    added_at: float = 0.0
    updated_at: float = 0.0
