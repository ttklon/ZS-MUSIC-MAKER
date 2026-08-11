# -*- coding: utf-8 -*-
"""
ZS Music Maker — pipeline_core.py (GOD MODE)
========================================================================
Новое ядро пайплайна. Заменяет монструозный orchestrator.py.
Реализует паттерн "Цепочка задач" с типизацией и обработкой ошибок.
"""

import time
import logging
import gc
import json
import pickle
import os
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, field
from app.core.i18n import i18n
from app.core.audio_utils import AudioSanitizer

# Настройка профессионального логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PipelineCore")

@dataclass
class StageResult:
    name: str
    ok: bool
    output: Any = None
    duration_sec: float = 0.0
    error: Optional[str] = None

@dataclass
class PipelineContext:
    project_id: str
    config: Dict[str, Any]
    results: Dict[str, StageResult] = field(default_factory=dict)
    shared_data: Dict[str, Any] = field(default_factory=dict)

class PipelineStage:
    def __init__(self, name: str, func: Callable[[PipelineContext], Any]):
        self.name = name
        self.func = func

    def execute(self, context: PipelineContext) -> StageResult:
        start_time = time.time()
        logger.info(i18n.t("start_pipeline", f"{context.project_id} -> {self.name}"))
        try:
            result_data = self.func(context)
            
            # Автоматическая санитизация, если результат - аудио-массив
            if isinstance(result_data, np.ndarray):
                result_data = AudioSanitizer.sanitize(result_data)
            
            duration = time.time() - start_time
            res = StageResult(name=self.name, ok=True, output=result_data, duration_sec=duration)
            context.results[self.name] = res
            logger.info(i18n.t("stage_done", self.name, duration))
            return res
        except Exception as e:
            duration = time.time() - start_time
            error_msg = i18n.t("error_stage", self.name, str(e))
            logger.error(error_msg)
            res = StageResult(name=self.name, ok=False, error=error_msg, duration_sec=duration)
            context.results[self.name] = res
            return res

class ZSPipeline:
    def __init__(self, project_id: str, config: Dict[str, Any]):
        self.context = PipelineContext(project_id=project_id, config=config)
        self.stages: List[PipelineStage] = []
        self.checkpoint_dir = Path("output") / project_id / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def add_stage(self, name: str, func: Callable[[PipelineContext], Any]):
        self.stages.append(PipelineStage(name, func))
        return self

    def _save_checkpoint(self, stage_name: str, result: StageResult):
        """Сохраняет состояние стадии на диск (в бинарном формате)."""
        cp_path = self.checkpoint_dir / f"{stage_name}.pkl"
        try:
            with open(cp_path, "wb") as f:
                pickle.dump({
                    "ok": result.ok,
                    "output": result.output,
                    "duration": result.duration_sec
                }, f)
        except Exception as e:
            logger.warning(f"Failed to save checkpoint for {stage_name}: {e}")

    def run(self, use_checkpoints: bool = True) -> Dict[str, Any]:
        logger.info(i18n.t("start_pipeline", self.context.project_id))
        
        for stage in self.stages:
            # Проверка чекпоинта (бинарный формат быстрее)
            cp_path = self.checkpoint_dir / f"{stage.name}.pkl"
            if use_checkpoints and cp_path.exists():
                logger.info(i18n.t("loading_checkpoint", stage.name))
                try:
                    with open(cp_path, "rb") as f:
                        data = pickle.load(f)
                        res = StageResult(name=stage.name, ok=data["ok"], output=data["output"], duration_sec=data["duration"])
                        self.context.results[stage.name] = res
                        if not res.ok: break
                        continue
                except Exception as e:
                    logger.warning(f"Checkpoint corrupted for {stage.name}, re-running. Error: {e}")

            res = stage.execute(self.context)
            self._save_checkpoint(stage.name, res)
            
            # Принудительная очистка памяти после каждой стадии
            gc.collect()
            
            if not res.ok:
                logger.error(f"Pipeline halted at stage {stage.name}")
                break
        
        return {
            "project_id": self.context.project_id,
            "status": "completed" if all(r.ok for r in self.context.results.values()) else "failed",
            "results": self.context.results
        }
