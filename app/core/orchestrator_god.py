# -*- coding: utf-8 -*-
"""
ZS Music Maker — orchestrator_god.py (GOD MODE)
========================================================================
Самый продвинутый пайплайн в истории проекта.
Реализован на базе PipelineCore для максимальной надежности.
"""

import os
import time
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.pipeline_core import ZSPipeline, PipelineContext
from app.core.logger import app_logger
from modules import (
    mastering_pro,
    voice_cleaner,
    phonk_engine,
    beat_constructor,
    phonk_engine_v2,
    genre_engine,
    ai_arranger,
    midi_generator,
)

def _save_project_meta(project_id: str, data: dict, out_root: Path):
    meta_path = out_root / "project_meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

def run_god_pipeline(
    project_id: str,
    wizard_state: dict,
    dry_run: bool = False,
    out_root: Optional[Path] = None,
) -> dict:
    """
    Запускает God Mode пайплайн через новое ядро.
    """
    if not out_root:
        out_root = Path(__file__).resolve().parents[2] / "output" / project_id
    out_root.mkdir(parents=True, exist_ok=True)
    
    pipe = ZSPipeline(project_id, wizard_state)
    
    # 1. AI Arrangement
    def stage_arr(ctx: PipelineContext):
        reg = genre_engine.StyleRegistry()
        factory = genre_engine.GenreFactory(reg)
        genre_name = ctx.config.get("genre", "drift_phonk")
        state = factory.create_wizard_state(genre_name, override=ctx.config)
        ctx.shared_data["state"] = state
        arranger = ai_arranger.AIArranger()
        return arranger.get_structure(state["tags"])
    
    pipe.add_stage("ai_arrangement", stage_arr)

    # 2. MIDI Generation
    def stage_midi(ctx: PipelineContext):
        midi_gen = midi_generator.MIDIGenerator()
        state = ctx.shared_data["state"]
        return {
            "ok": True,
            "drums": midi_gen.generate_drum_pattern(state["genre"], state["bpm_override"]),
            "melody": midi_gen.generate_melody_pattern(state["genre"], "A", "minor", state["bpm_override"])
        }
    
    pipe.add_stage("midi_generation", stage_midi)

    # 3. Pro Audio Generation using CyberSynth Engine for Cyberpunk & Modern Genres
    def stage_audio(ctx: PipelineContext):
        state = ctx.shared_data["state"]
        genre_name = state["genre"]
        bpm = state["bpm_override"]
        
        out_name = str(out_root / "multi_beat.wav")
        try:
            if "chanson" in genre_name.lower() or "шансон" in genre_name.lower():
                from modules.chanson_engine import ChansonEngine
                engine = ChansonEngine(sample_rate=44100)
                res = engine.synthesize_chanson_track(bpm=max(80, min(bpm, 110)), duration_sec=120, out_path=out_name)
            else:
                from modules.cyber_synth import CyberSynth
                synth = CyberSynth(sample_rate=44100)
                res = synth.synthesize_track(bpm=bpm, duration_sec=120, out_path=out_name)
            
            if res.get("ok"):
                ctx.shared_data["beat_wav"] = out_name
                return out_name
        except Exception as e:
            print(f"[orchestrator_god] Engine fallback due to: {e}")

        # Fallback to beat_constructor if needed
        res = beat_constructor.construct_beat(
            groove={}, samples=[], 
            style_vector={"target_bpm": bpm, "target_mode": "minor"},
            out_name=out_name
        )
        ctx.shared_data["beat_wav"] = res.get("beat_path")
        return res
            
    pipe.add_stage("audio_generation", stage_audio)

    # 4. Vocal Synthesis & Cleaning (Generates speech/singing if no input vocal)
    def stage_vocal(ctx: PipelineContext):
        state = ctx.shared_data["state"]
        vocal_wav = ctx.config.get("vocal_input_path")
        
        if vocal_wav and os.path.exists(vocal_wav):
            clean_vocal_wav = str(out_root / "vocal_cleaned.wav")
            voice_cleaner.clean_vocal(vocal_wav, clean_vocal_wav)
            ctx.shared_data["vocal_wav"] = clean_vocal_wav
            return clean_vocal_wav
        else:
            # v26: Автоматически генерируем текст и озвучиваем его через gTTS для настоящего вокала в миксе!
            try:
                from modules import lyrics_gen, voice_synth
                lyric_res = lyrics_gen.generate_lyrics(theme=state.get("theme", "Владимирский централ"), style_vector={"target_bpm": state.get("bpm_override", 96)})
                text_content = lyric_res.get("lyrics", "Владимирский централ, ветер северный")
                
                vocal_draft = str(out_root / "vocal_draft.wav")
                os.makedirs(os.path.dirname(vocal_draft), exist_ok=True)
                
                # Используем voice_synth.synth для генерации аудио с русского текста
                synth_path = voice_synth.synth(text_content[:200], out_name=str(vocal_draft))
                if synth_path and os.path.exists(synth_path):
                    vocal_draft = synth_path
                    ctx.shared_data["vocal_wav"] = vocal_draft
                    return vocal_draft
            except Exception as e:
                print(f"[orchestrator_god] Auto-vocal synthesis error: {e}")
                
        return None

    pipe.add_stage("vocal_cleaning", stage_vocal)

    # 5. Professional Mastering
    def stage_master(ctx: PipelineContext):
        beat_wav = ctx.shared_data.get("beat_wav")
        vocal_wav = ctx.shared_data.get("vocal_wav")
        master_wav = str(out_root / "masters" / "master_god.wav")
        os.makedirs(os.path.dirname(master_wav), exist_ok=True)
        # Вызываем профессиональный мастеринг
        return mastering_pro.process_mastering(beat_wav, master_wav, vocal_path=vocal_wav, target_lufs=-12.0)

    pipe.add_stage("god_mastering_pro", stage_master)

    # Запуск (с поддержкой чекпоинтов для стабильности)
    final_out = pipe.run(use_checkpoints=True)
    
    # Формируем итоговый отчет для совместимости
    stages_list = []
    total_elapsed = 0.0
    for name, sres in final_out["results"].items():
        stages_list.append({
            "name": name,
            "ok": sres.ok,
            "duration_sec": sres.duration_sec,
            "output": sres.output,
            "reason": sres.error
        })
        total_elapsed += sres.duration_sec
        
    res = {
        "project_id": project_id,
        "status": final_out["status"],
        "god_mode": True,
        "elapsed_sec": round(total_elapsed, 2),
        "stages": stages_list,
        "master_path": str(out_root / "masters" / "master_god.wav") if final_out["status"] == "completed" else None
    }
    
    _save_project_meta(project_id, res, out_root)
    return res
