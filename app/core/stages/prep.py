# -*- coding: utf-8 -*-
"""
app/core/stages/prep.py — Подготовка: анализ референсов, извлечение грува, план аранжировки.
"""

from __future__ import annotations

from typing import Any


_GENRE_STYLE_DEFAULTS = {
    "drift_phonk": {
        "bpm": 130,
        "mode": "minor",
        "aggression": 0.85,
        "hihat_density": 0.7,
        "swing": 0.18,
    },
    "phonk": {
        "bpm": 130,
        "mode": "minor",
        "aggression": 0.8,
        "hihat_density": 0.65,
        "swing": 0.15,
    },
    "trap": {
        "bpm": 75,
        "mode": "minor",
        "aggression": 0.7,
        "hihat_density": 0.75,
        "swing": 0.08,
    },
    "hip_hop": {
        "bpm": 90,
        "mode": "minor",
        "aggression": 0.6,
        "hihat_density": 0.55,
        "swing": 0.12,
    },
    "pop": {
        "bpm": 118,
        "mode": "major",
        "aggression": 0.5,
        "hihat_density": 0.5,
        "swing": 0.05,
    },
    "dnb": {
        "bpm": 174,
        "mode": "minor",
        "aggression": 0.9,
        "hihat_density": 0.85,
        "swing": 0.0,
    },
    "house": {
        "bpm": 126,
        "mode": "minor",
        "aggression": 0.6,
        "hihat_density": 0.6,
        "swing": 0.0,
    },
    "techno": {
        "bpm": 130,
        "mode": "minor",
        "aggression": 0.75,
        "hihat_density": 0.55,
        "swing": 0.0,
    },
    "lo_fi": {
        "bpm": 80,
        "mode": "minor",
        "aggression": 0.35,
        "hihat_density": 0.45,
        "swing": 0.22,
    },
    "rnb": {
        "bpm": 95,
        "mode": "minor",
        "aggression": 0.45,
        "hihat_density": 0.55,
        "swing": 0.15,
    },
}


def _default_style_for_genre(genre: str) -> dict[str, Any]:
    g = (genre or "").lower().strip().replace("-", "_").replace(" ", "_")
    return dict(_GENRE_STYLE_DEFAULTS.get(g, _GENRE_STYLE_DEFAULTS["drift_phonk"]))


def _stage_analyze(
    refs: list[str], dry_run: bool, genre: str = "drift_phonk"
) -> dict[str, Any]:
    """v22: no refs — это НЕ fallback, а нормальный generate-from-scratch.
    Отдаём default style-vector по жанру, чтобы downstream (beat/mix) собирал
    целостный трек, а не sine-кашу, но не притворяемся что делали реальный анализ.
    """
    try:
        from modules import analyzer

        if not refs:
            gs = _default_style_for_genre(genre)
            synthetic_analysis = {
                "bpm": gs["bpm"],
                "mode": gs["mode"],
                "aggression": gs["aggression"],
                "source": "genre_default",
                "n_refs": 0,
            }
            return {
                "ok": True,
                "analysis": synthetic_analysis,
                "reason": f"generate-from-scratch mode; genre_default={genre}",
            }
        if len(refs) == 1:
            res = analyzer.analyze_single(refs[0])
        else:
            res = analyzer.analyze_multi(refs)
        return {"ok": True, "analysis": res}
    except Exception as e:
        return {"ok": False, "reason": str(e), "fallback_used": True}


def _stage_groove(refs: list[str], genre: str = "drift_phonk") -> dict[str, Any]:
    """v22: no refs — не fallback, а generate-from-scratch. Отдаём default
    groove-template по жанру, чтобы beat_constructor получил нормальный ритм,
    а не голый kick-каждые-полсекунды.
    """
    try:
        from modules import groove_extractor

        if not refs:
            gs = _default_style_for_genre(genre)
            groove = {
                "kick_pattern": [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0],
                "snare_pattern": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
                "hihat_density": gs["hihat_density"],
                "swing": gs["swing"],
                "triplet_rolls": True,
                "drop_intensity": gs["aggression"],
                "source": "genre_default",
            }
            return {
                "ok": True,
                "groove": groove,
                "reason": f"generate-from-scratch groove; genre_default={genre}",
            }
        if hasattr(groove_extractor, "extract_groove"):
            g = groove_extractor.extract_groove(refs[0])
        elif hasattr(groove_extractor, "extract"):
            g = groove_extractor.extract(refs[0])
        else:
            g = None
        return {"ok": True, "groove": g}
    except Exception as e:
        return {"ok": False, "reason": str(e)}


def _stage_arrangement(analysis: Any) -> dict[str, Any]:
    try:
        from modules import arrangement_engine as ae

        plan = ae.plan(analysis) if hasattr(ae, "plan") else {"sections": []}
        return {"ok": True, "plan": plan}
    except Exception as e:
        return {"ok": False, "reason": str(e)}
