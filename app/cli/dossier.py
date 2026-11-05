# -*- coding: utf-8 -*-
"""
app/cli/dossier.py — команды работы с досье артиста.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.cli.env import ROOT, safe_print


def run_dossier_add(artist: str, source_dir: str) -> int:
    try:
        from modules.artist_dossier import DossierManager
        from modules.artist_dossier.collectors import (
            LocalFolderCollector,
            LyricVaultCollector,
        )

        tracks = []
        if Path(source_dir).is_dir():
            tracks = LocalFolderCollector(source_dir).collect(artist)
        tracks += LyricVaultCollector(str(ROOT / "lyric_vault")).collect(artist)
        DossierManager().add_artist(artist, tracks=tracks)
        safe_print(f"[dossier] artist={artist} tracks_added={len(tracks)}")
        return 0
    except Exception as e:
        safe_print(f"[main --dossier-add] failed: {e}")
        return 2


def run_dossier_build(artist: str) -> int:
    try:
        from modules.artist_dossier import DossierManager

        dossier = DossierManager().build_full_dossier(
            artist, progress_cb=lambda track_id, stage: safe_print(f"  [{track_id}] {stage}")
        )
        safe_print(json.dumps(dossier, ensure_ascii=False, indent=2)[:2000])
        return 0
    except Exception as e:
        safe_print(f"[main --dossier-build] failed: {e}")
        return 2
