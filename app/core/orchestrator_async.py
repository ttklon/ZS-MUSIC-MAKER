# -*- coding: utf-8 -*-
"""
ZS Music Maker — orchestrator_async.py (GOD MODE)
========================================================================
Асинхронный оркестратор для параллельной обработки стадий.
Позволяет одновременно генерировать бит, чистить вокал и анализировать гармонию.
"""

import asyncio
import time
import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, asdict

@dataclass
class AsyncStage:
    name: str
    ok: bool = False
    duration_sec: float = 0.0
    output: Any = None
    reason: Optional[str] = None
    
async def run_stage_async(name: str, coro: Callable) -> AsyncStage:
    t0 = time.time()
    stage = AsyncStage(name=name)
    try:
        # Если это корутина - ждем, если обычная функция - запускаем в треде
        if asyncio.iscoroutinefunction(coro):
            res = await coro()
        else:
            res = await asyncio.to_thread(coro)
            
        stage.ok = True
        stage.output = res
    except Exception as e:
        stage.ok = False
        stage.reason = f"{type(e).__name__}: {e}"
    stage.duration_sec = round(time.time() - t0, 3)
    return stage

class AsyncOrchestrator:
    def __init__(self, project_id: str, out_root: Path):
        self.project_id = project_id
        self.out_root = out_root
        self.out_root.mkdir(parents=True, exist_ok=True)
        self.stages: List[AsyncStage] = []

    async def run_pipeline(self, wizard_state: dict):
        t_start = time.time()
        
        from modules import beat_constructor, phonk_engine, voice_cleaner, mastering_pro
        
        bpm = int(wizard_state.get("bpm_override") or 130)
        genre = wizard_state.get("genre", "drift_phonk")
        
        # 1. Параллельный запуск генерации бита и колокольчиков
        tasks = [
            run_stage_async("beat_gen", lambda: beat_constructor.construct_beat(
                groove={}, samples=[], 
                style_vector={"target_bpm": bpm, "target_mode": "minor"},
                out_name="beat.wav"
            )),
            run_stage_async("cowbell_gen", lambda: phonk_engine.create_cowbell_melody(
                [440, 523, 392, 440], bpm, str(self.out_root / "cowbells.wav")
            ))
        ]
        
        # Если есть вокал - добавляем очистку в параллель
        vocal_in = wizard_state.get("vocal_input_path")
        if vocal_in and os.path.exists(vocal_in):
            tasks.append(run_stage_async("vocal_clean", lambda: voice_cleaner.clean_vocal(
                vocal_in, str(self.out_root / "vocal_cleaned.wav")
            )))
            
        results = await asyncio.gather(*tasks)
        self.stages.extend(results)
        
        # 2. Финальный мастеринг (зависит от результатов)
        beat_stage = next((s for s in results if s.name == "beat_gen"), None)
        if beat_stage and beat_stage.ok:
            beat_path = beat_stage.output.get("beat_path")
            master_wav = str(self.out_root / "masters" / "master_async.wav")
            
            master_stage = await run_stage_async("mastering", lambda: mastering_pro.process_mastering(
                beat_path, master_wav, target_lufs=-12.0
            ))
            self.stages.append(master_stage)
            
        total_duration = round(time.time() - t_start, 2)
        
        final_res = {
            "project_id": self.project_id,
            "status": "completed" if all(s.ok for s in self.stages) else "partial",
            "duration_sec": total_duration,
            "stages": [asdict(s) for s in self.stages]
        }
        
        with open(self.out_root / "async_meta.json", "w") as f:
            json.dump(final_res, f, indent=2, default=str)
            
        return final_res

async def main_async():
    orch = AsyncOrchestrator("async_test", Path("./output/async_test"))
    res = await orch.run_pipeline({"genre": "phonk", "bpm_override": 140})
    print(f"Async Pipeline Done in {res['duration_sec']}s")

if __name__ == "__main__":
    asyncio.run(main_async())
