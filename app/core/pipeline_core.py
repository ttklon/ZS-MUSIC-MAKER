# -*- coding: utf-8 -*-
"""
ZS Music Maker — pipeline_core.py (GOD MODE)
========================================================================
Новое ядро пайплайна. Заменяет монструозный orchestrator.py.
Реализует паттерн "Цепочка задач" с типизацией и обработкой ошибок.
"""

import time
import logging
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, field

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
        logger.info(f"Starting stage: {self.name}")
        try:
            result_data = self.func(context)
            duration = time.time() - start_time
            res = StageResult(name=self.name, ok=True, output=result_data, duration_sec=duration)
            context.results[self.name] = res
            logger.info(f"Stage {self.name} completed in {duration:.2f}s")
            return res
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Error in stage {self.name}: {str(e)}"
            logger.error(error_msg)
            res = StageResult(name=self.name, ok=False, error=error_msg, duration_sec=duration)
            context.results[self.name] = res
            return res

class ZSPipeline:
    def __init__(self, project_id: str, config: Dict[str, Any]):
        self.context = PipelineContext(project_id=project_id, config=config)
        self.stages: List[PipelineStage] = []

    def add_stage(self, name: str, func: Callable[[PipelineContext], Any]):
        self.stages.append(PipelineStage(name, func))
        return self

    def run(self) -> Dict[str, Any]:
        logger.info(f"Launching pipeline for project: {self.context.project_id}")
        for stage in self.stages:
            res = stage.execute(self.context)
            if not res.ok:
                logger.error(f"Pipeline halted at stage {stage.name}")
                break
        
        return {
            "project_id": self.context.project_id,
            "status": "completed" if all(r.ok for r in self.context.results.values()) else "failed",
            "results": self.context.results
        }
