# -*- coding: utf-8 -*-
"""
ZS Music Maker v10 — Orchestrator Patch
=========================================
Подключает новые модули v10 к существующему оркестратору,
не удаляя ничего из v7/v8/v9.

Порядок применения патчей: v7 base → v8 patch → v9 patch → v10 patch.
"""
from __future__ import annotations
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional

log = logging.getLogger("zsmm.orchestrator_v10")

VERSION = "v10.0.0-chart-killer-pro"


def apply_v10_patch(orchestrator: Any) -> Dict[str, Any]:
    """
    Регистрирует новые стадии v10 в оркестраторе.
    """
    added = []

    # 1. Essentia advanced analyzer
    try:
        from modules import essentia_analyzer
        orchestrator.essentia = essentia_analyzer
        added.append("essentia_analyzer")
    except Exception as e:
        log.warning("essentia_analyzer patch skipped: %s", e)

    # 2. Freesound client
    try:
        from modules import freesound_client
        orchestrator.freesound = freesound_client
        added.append("freesound_client")
    except Exception as e:
        log.warning("freesound_client patch skipped: %s", e)

    # 3. Matchering wrapper
    try:
        from modules import matchering_master
        orchestrator.matchering = matchering_master
        added.append("matchering_master")
    except Exception as e:
        log.warning("matchering_master patch skipped: %s", e)

    # 4. Cover art
    try:
        from modules import cover_art_gen
        orchestrator.cover_gen = cover_art_gen
        added.append("cover_art_gen")
    except Exception as e:
        log.warning("cover_art_gen patch skipped: %s", e)

    # 5. Phoneme coverage
    try:
        from modules import phoneme_coverage
        orchestrator.phoneme_cov = phoneme_coverage
        added.append("phoneme_coverage")
    except Exception as e:
        log.warning("phoneme_coverage patch skipped: %s", e)

    # 6. DirectML detector
    try:
        from modules import hw_directml
        orchestrator.hw_directml = hw_directml
        prof = hw_directml.save_profile()
        orchestrator.hw_v10 = prof
        added.append(f"hw_directml({prof.get('backend')})")
    except Exception as e:
        log.warning("hw_directml patch skipped: %s", e)

    # 7. Anti-neuro polish v10
    try:
        from modules import anti_neuro_v10
        orchestrator.anti_neuro_v10 = anti_neuro_v10
        added.append("anti_neuro_v10")
    except Exception as e:
        log.warning("anti_neuro_v10 patch skipped: %s", e)

    # 8. Lyric Vault v10
    try:
        from modules import lyric_vault_v10
        orchestrator.lyric_vault_v10 = lyric_vault_v10
        added.append("lyric_vault_v10")
    except Exception as e:
        log.warning("lyric_vault_v10 patch skipped: %s", e)

    # 9. Karaoke engine
    try:
        from modules import karaoke_engine
        orchestrator.karaoke_v10 = karaoke_engine
        added.append("karaoke_engine")
    except Exception as e:
        log.warning("karaoke_engine patch skipped: %s", e)

    # 10. Onboarding tour
    try:
        from modules import onboarding_tour
        orchestrator.tour = onboarding_tour
        added.append("onboarding_tour")
    except Exception as e:
        log.warning("onboarding_tour patch skipped: %s", e)

    log.info("v10 patch applied: %s", added)
    return {"ok": True, "version": VERSION, "added": added, "count": len(added)}


def full_v10_pipeline(orchestrator: Any, project_id: str,
                       vocal_wav: str, beat_wav: str,
                       reference_wav: Optional[str] = None,
                       polish_preset: str = "standard",
                       track_title: str = "Untitled",
                       artist: str = "ZS") -> Dict[str, Any]:
    """
    Оркестрирует полный v10 pipeline после v9-стадий.
      → anti_neuro_v10 → matchering (car/club/streaming/tiktok) →
        cover_art_gen → phoneme_cov update
    """
    project_dir = Path("output/projects") / project_id / "release"
    project_dir.mkdir(parents=True, exist_ok=True)
    steps = {}

    # 1. Anti-neuro polish v10
    polished = str(project_dir / "vocal_polished_v10.wav")
    try:
        r = orchestrator.anti_neuro_v10.polish_vocal(vocal_wav, polished,
                                                     preset=polish_preset)
        steps["anti_neuro_v10"] = r
    except Exception as e:
        steps["anti_neuro_v10"] = {"ok": False, "reason": str(e)}

    # 2. Mixdown (использует существующий mixdown.py)
    try:
        from modules import mixdown
        mix_out = str(project_dir / "master.wav")
        mixdown.mix(beat_wav, polished if Path(polished).exists() else vocal_wav,
                    mix_out)
        steps["mixdown"] = {"ok": True, "out": mix_out}
    except Exception as e:
        steps["mixdown"] = {"ok": False, "reason": str(e)}
        mix_out = beat_wav

    # 3. Matchering stands
    stands_dir = str(project_dir / "stands")
    try:
        if reference_wav and Path(reference_wav).exists():
            r_ref = orchestrator.matchering.match_to_reference(
                mix_out, reference_wav, str(project_dir / "master_matched.wav"))
            steps["matchering_ref"] = r_ref
        r_stands = orchestrator.matchering.master_all_stands(mix_out, stands_dir)
        steps["stands"] = r_stands
    except Exception as e:
        steps["stands"] = {"ok": False, "reason": str(e)}

    # 4. Cover art
    try:
        cover_out = str(project_dir / "cover.png")
        r_cov = orchestrator.cover_gen.generate(
            track_title, artist, cover_out, style="neon"
        )
        steps["cover"] = r_cov
    except Exception as e:
        steps["cover"] = {"ok": False, "reason": str(e)}

    # 5. Phoneme coverage refresh
    try:
        steps["phoneme_coverage"] = orchestrator.phoneme_cov.compute_coverage()
    except Exception as e:
        steps["phoneme_coverage"] = {"ok": False, "reason": str(e)}

    # 6. Release-manifest v10
    manifest = {
        "version": VERSION,
        "project_id": project_id,
        "artist": artist,
        "title": track_title,
        "generated_at": int(time.time()),
        "polish_preset": polish_preset,
        "steps": {k: v.get("ok", False) for k, v in steps.items()},
    }
    (project_dir / "manifest_v10.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    steps["manifest"] = {"ok": True, "path": str(project_dir / "manifest_v10.json")}

    return {"ok": True, "version": VERSION, "project_dir": str(project_dir),
            "steps": steps}


if __name__ == "__main__":
    class Dummy:
        pass
    d = Dummy()
    r = apply_v10_patch(d)
    print(json.dumps(r, ensure_ascii=False, indent=2))
