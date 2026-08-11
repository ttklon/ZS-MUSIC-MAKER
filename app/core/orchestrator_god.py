# -*- coding: utf-8 -*-
"""
ZS Music Maker — orchestrator_god.py (GOD MODE)
========================================================================
Самый продвинутый пайплайн в истории проекта.
Включает:
  - Интеллектуальную очистку вокала (noisereduce)
  - Синтез Phonk Cowbells
  - Профессиональный мастеринг на Pedalboard
  - Улучшенную стерео-панораму
"""

import os
import time
import shutil
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.orchestrator import _timed
from modules import (
    mastering_pro,
    voice_cleaner,
    phonk_engine,
    beat_constructor,
    phonk_engine_v2,
    genre_engine,
    ai_arranger,
    midi_generator,
    musical_intelligence,
)
from app.plugins.base import PluginChain
from app.plugins.advanced import PhonkDistortion, AntiAINeuroObfuscator

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
    Запуск God Mode пайплайна.
    """
    t_start = time.time()
    if not out_root:
        out_root = Path(__file__).resolve().parents[2] / "output" / project_id
    out_root.mkdir(parents=True, exist_ok=True)

    stages = []
    import json

    # 1. Инициализация систем (GOD MODE)
    reg = genre_engine.StyleRegistry()
    factory = genre_engine.GenreFactory(reg)
    arranger = ai_arranger.AIArranger()
    midi_gen = midi_generator.MIDIGenerator()
    
    # Получаем профиль жанра и структуру
    genre_name = wizard_state.get("genre", "drift_phonk")
    state = factory.create_wizard_state(genre_name, override=wizard_state)
    bpm = state["bpm_override"]
    genre_tags = state["tags"]
    
    s0 = _timed("ai_arrangement", lambda: arranger.get_structure(genre_tags))
    stages.append(s0.__dict__ if hasattr(s0, "__dict__") else s0)
    structure = s0.output

    # 2. Генерация MIDI (GOD MODE)
    s1 = _timed("midi_generation", lambda: {
        "ok": True,
        "drums": midi_gen.generate_drum_pattern(genre_name, bpm),
        "melody": midi_gen.generate_melody_pattern(genre_name, "A", "minor", bpm)
    })
    stages.append(s1.__dict__ if hasattr(s1, "__dict__") else s1)

    # 3. Генерация аудио (GOD MODE)
    if "phonk" in genre_name.lower():
        phonk_wav = str(out_root / "phonk_v2_master.wav")
        engine_v2 = phonk_engine_v2.PhonkEngineV2()
        s2 = _timed("phonk_engine_v2", lambda: engine_v2.create_drift_track(
            project_id, bpm, "A", "minor", phonk_wav
        ))
        stages.append(s2.__dict__ if hasattr(s2, "__dict__") else s2)
        beat_wav = phonk_wav
    else:
        # Fallback на базовый конструктор для 100+ жанров
        s2 = _timed("multi_genre_beat", lambda: beat_constructor.construct_beat(
            groove={}, samples=[], 
            style_vector={"target_bpm": bpm, "target_mode": "minor"},
            out_name="multi_beat.wav"
        ))
        stages.append(s2.__dict__ if hasattr(s2, "__dict__") else s2)
        beat_wav = (s2.output or {}).get("beat_path")

    # 4. Очистка вокала (если есть)
    vocal_wav = wizard_state.get("vocal_input_path")
    if vocal_wav and os.path.exists(vocal_wav):
        clean_vocal_wav = str(out_root / "vocal_cleaned.wav")
        s3 = _timed(
            "god_vocal_clean",
            lambda: voice_cleaner.clean_vocal(vocal_wav, clean_vocal_wav),
        )
        stages.append(s3.__dict__ if hasattr(s3, "__dict__") else s3)
        vocal_wav = clean_vocal_wav

    # 5. Финальный мастеринг (GOD MODE)
    master_wav = str(out_root / "masters" / "master_god.wav")
    if beat_wav and os.path.exists(beat_wav):
        mix_wav = beat_wav  # Для теста используем бит как микс
        s4 = _timed(
            "god_mastering_pro",
            lambda: mastering_pro.process_mastering(
                mix_wav, master_wav, target_lufs=-12.0
            ),
        )
        stages.append(s4.__dict__ if hasattr(s4, "__dict__") else s4)
    else:
        s4 = {
            "name": "god_mastering_pro",
            "ok": False,
            "reason": "no beat_wav for mastering",
        }
        stages.append(s4)

    all_ok = all(s.get("ok") for s in stages)
    res = {
        "project_id": project_id,
        "status": "completed" if all_ok else "failed",
        "god_mode": True,
        "elapsed_sec": round(time.time() - t_start, 2),
        "stages": stages,
        "master_path": master_wav if all_ok else None,
    }

    _save_project_meta(project_id, res, out_root)
    return res
