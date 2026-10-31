# -*- coding: utf-8 -*-
"""
app/core/orchestrator_ai.py — AI-пайплайн (локальные модели в VRAM).

Единственная ответственность файла — склейка стадий AI-слоя через
`SequentialAIRunner`: каждая стадия живёт в `app/core/ai/stages_*.py`,
рендер-хелперы — в `app/core/ai/render.py`, состояние — в `AIContext`.

Порядок: hw → dossier → lyrics → metadata → music → music_stereo → vocal →
rvc → mix → master → cover → tag. Тяжёлые роли опциональны: если модели нет,
стадия честно помечается skip/fallback в отчёте раннера.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.ai.quality import validate_cover_artifact  # noqa: F401 - публичный реэкспорт
from app.ai.quality import validate_master_artifact  # noqa: F401 - публичный реэкспорт
from app.ai.sequential_runner import AIStage, SequentialAIRunner
from app.core.ai.context import AIContext
from app.core.ai.render import (  # noqa: F401 - публичный реэкспорт
    _slug,
    extend_beat_with_stereo_sections,
    render_rvc_vocal,
    render_stereo_texture,
    render_voice_synth_fallback,
    render_xtts_vocal,
)
from app.core.ai.stages_final import stage_cover, stage_master, stage_tag
from app.core.ai.stages_meta import (
    stage_dossier_load,
    stage_hw,
    stage_lyrics,
    stage_metadata,
)
from app.core.ai.stages_music import stage_music, stage_music_stereo
from app.core.ai.stages_vocal import stage_mix, stage_rvc, stage_vocal
from app.core.logger import TerminalStageProgress, app_logger


def run_ai_pipeline(
    project_id, wizard_state=None, out_root=None, dry_run=False, terminal_progress: bool = False
):
    ws = dict(wizard_state or {})
    try:
        from config.settings import get_settings
        cfg = get_settings()
        app_logger.info(f"[orchestrator_ai] config_path={cfg.config_path} vram_gb={cfg.vram_gb}")
    except Exception:  # noqa: BLE001
        cfg = None
    ws.setdefault("genre", "drift_phonk")
    ws.setdefault("theme", "движ, ночь, город")
    ws.setdefault("bpm", 140)
    ws.setdefault("key", "A minor")
    ws.setdefault("mood", "dark, hypnotic, energetic")
    ws.setdefault("n_verses", 2)
    ws.setdefault("bilingual", True)
    ws.setdefault("duration_sec", 120)
    if not out_root:
        out_root = Path(__file__).resolve().parents[2] / "output" / project_id
    out_root = Path(out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "masters").mkdir(exist_ok=True)
    artist_slug = _slug(ws["artist_slug"]) if ws.get("artist_slug") else None
    ref_track_id = ws.get("track_id")
    ai = AIContext(
        ws=ws,
        out_root=out_root,
        dry_run=dry_run,
        artist_slug=artist_slug,
        ref_track_id=ref_track_id,
    )

    runner = SequentialAIRunner()
    runner.add(AIStage("hw_check",     None,               stage_hw))
    runner.add(AIStage("dossier_load", None,               stage_dossier_load))
    runner.add(AIStage("lyrics",       "lyrics_llm",       stage_lyrics,   optional=True))
    runner.add(AIStage("metadata",     "metadata_llm",     stage_metadata, optional=True))
    runner.add(AIStage("music",        "music_generation", stage_music,    optional=True))
    runner.add(AIStage("music_stereo", "music_stereo",     stage_music_stereo, optional=True))
    runner.add(AIStage("vocal_synth",  "tts_vocal",        stage_vocal,    optional=True))
    runner.add(AIStage("rvc",          "vocal_rvc",        stage_rvc,      optional=True))
    runner.add(AIStage("mix",          None,               stage_mix))
    runner.add(AIStage(
        "master",
        "mastering_ai" if ws.get("reference_master_wav") else None,
        stage_master,
        optional=True,
    ))
    runner.add(AIStage("cover",        "cover_art",        stage_cover,    optional=True))
    runner.add(AIStage("tag",          "audio_tagger",     stage_tag,      optional=True))
    progress = TerminalStageProgress(len(runner.stages)) if terminal_progress else None
    report = runner.run(
        {"project_id": project_id, "wizard_state": ws, "ai": ai}, progress=progress
    )
    result = {"project_id": project_id, "god_mode": "4.0-AI", "wizard_state": ws,
              "report": report.to_dict(),
              "config": cfg.dump() if cfg is not None else None,
              "artefacts": {"lyrics": str(out_root / "lyrics.txt"),
                            "metadata": str(out_root / "metadata.json"),
                            "beat": str(out_root / "beat.wav"),
                            "texture_stereo": str(out_root / "texture_stereo.wav"),
                            "vocal": str(out_root / "vocal_xtts.wav"),
                            "mix": str(out_root / "mix.wav"),
                            "master": str(out_root / "masters" / "master_ai.wav"),
                            "cover": str(out_root / "cover.png")}}
    (out_root / "project_meta.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    from app.ai.registry import MODEL_REGISTRY
    manifest = {
        "schema_version": 1,
        "project_id": project_id,
        "generator": "ZS Music Maker AI pipeline",
        "wizard_state": ws,
        "stages": result["report"].get("stages", []),
        "model_roles": {
            key: {"engine": spec["engine"], "file": spec.get("file", ""),
                  "hf_repo": spec.get("hf_repo", "")}
            for key, spec in MODEL_REGISTRY.items()
        },
        "artefacts": result["artefacts"],
    }
    manifest_path = out_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    result["manifest_path"] = str(manifest_path)
    app_logger.info(f"[orchestrator_ai] finished project={project_id}")
    return result
