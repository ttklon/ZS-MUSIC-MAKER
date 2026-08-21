# -*- coding: utf-8 -*-
"""
ZS Music Maker — orchestrator_god.py (GOD MODE)
========================================================================
Самый продвинутый пайплайн в истории проекта.
Реализован на базе PipelineCore для максимальной надежности.
"""

import os
import json
from pathlib import Path
from typing import Any, Optional

from app.core.pipeline_core import ZSPipeline, PipelineContext
from modules import (
    mastering_pro,
    voice_cleaner,
    beat_constructor,
    genre_engine,
    ai_arranger,
    midi_generator,
)

def _json_safe(obj: Any) -> Any:
    """v34 FIX (P2.29): честная JSON-сериализация вместо default=str.

    default=str молча превращал numpy-скаляры и прочие не-JSON объекты в
    строки вида 'np.float32(0.95)' — метрики в project_meta.json переставали
    быть числами и ломали downstream-анализ. Теперь рекурсивно приводим:
    numpy-скаляры → python float/int, Path → str, set/tuple → list,
    остальное неизвестное → str (как и раньше, но только как последний шанс).
    """
    try:
        import numpy as _np
        if isinstance(obj, _np.generic):
            return obj.item()
    except ImportError:
        pass
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, Path):
        return str(obj)
    return obj


def _save_project_meta(project_id: str, data: dict, out_root: Path):
    meta_path = out_root / "project_meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(_json_safe(data), f, ensure_ascii=False, indent=2, default=str)

def run_god_pipeline(
    project_id: str,
    wizard_state: Optional[dict] = None,
    dry_run: bool = False,
    out_root: Optional[Path] = None,
) -> dict:
    """
    Запускает God Mode пайплайн через новое ядро.

    v28 (P1): wizard_state теперь Optional — раньше вызов
    run_god_pipeline(pid, None) (например, из GUI без wizard или из
    smoke-теста) мгновенно падал на стадии ai_arrangement с
    "'NoneType' object has no attribute 'get'". Теперь None/пустой
    dict заменяется на безопасный дефолт {genre: drift_phonk} —
    пайплайн доезжает до мастеринга вместо краха на первой стадии.
    """
    if not isinstance(wizard_state, dict):
        wizard_state = {}
    wizard_state.setdefault("genre", "drift_phonk")
    isolated_output = out_root is not None
    if out_root is None:
        out_root = Path(__file__).resolve().parents[2] / "output" / project_id
    out_root.mkdir(parents=True, exist_ok=True)
    
    # Checkpoints принадлежат текущему out_root. Это предотвращает загрузку
    # старых результатов из output/<project_id>, когда smoke предварительно
    # удалил свой каталог артефактов и запускается повторно.
    checkpoint_dir = out_root / "checkpoints"
    pipe = ZSPipeline(project_id, wizard_state, checkpoint_dir=checkpoint_dir)
    
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
                # v30 FIX: после фикса честности voice_synth.synth возвращает
                # "" когда ни один TTS-движок недоступен — обрабатываем это
                # явно и кладём honest reason в отчёт (раньше стадия молча
                # возвращала None без объяснения).
                # v33 FIX (P0, SESSION_LOG v32.3): раньше текст насильно
                # обрезался до 200 символов (text_content[:200]) — на
                # 120-секундный трек синтезировалась одна фраза ≈2-3 строки.
                # Теперь передаём полный текст лирики. Если движок слабый
                # (pyttsx3/gtts) — он сам прочитает длинный текст; ограничение
                # оставляем только как мягкий safety-cap на случай мусора.
                vocal_text = text_content if len(text_content) <= 4000 else text_content[:4000]
                synth_path = voice_synth.synth(vocal_text, out_name=str(vocal_draft))
                if synth_path and os.path.exists(synth_path):
                    vocal_draft = synth_path
                    ctx.shared_data["vocal_wav"] = vocal_draft
                    return vocal_draft
                ctx.shared_data["vocal_status"] = "BLOCKED"
                ctx.shared_data["vocal_reason"] = "no_vocal_engine (silero/xtts/bark/pyttsx3/gtts недоступны)"
                print("[orchestrator_god] vocal synth BLOCKED: no TTS engine available — pipeline продолжает без вокала")
            except Exception as e:
                print(f"[orchestrator_god] Auto-vocal synthesis error: {e}")
                ctx.shared_data["vocal_status"] = "FAILED"
                ctx.shared_data["vocal_reason"] = str(e)

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

    # Интерактивные проекты могут переиспользовать checkpoints. Для явного
    # out_root (smoke/изолированный запуск) этапы всегда пересчитываются: их
    # аудиоартефакты являются частью этого же временного каталога.
    final_out = pipe.run(use_checkpoints=not isolated_output)
    
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
        # v30: честный статус вокала в отчёте (раньше информация терялась)
        "vocal_status": pipe.context.shared_data.get("vocal_status", "OK" if pipe.context.shared_data.get("vocal_wav") else "SKIPPED"),
        "vocal_reason": pipe.context.shared_data.get("vocal_reason"),
        "master_path": str(out_root / "masters" / "master_god.wav") if final_out["status"] == "completed" else None
    }
    
    _save_project_meta(project_id, res, out_root)
    return res
