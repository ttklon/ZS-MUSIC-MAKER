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
import os
from pathlib import Path
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
        logger.info(f"stage={self.name} event=start")
        try:
            result_data = self.func(context)
            duration = time.time() - start_time
            res = StageResult(name=self.name, ok=True, output=result_data, duration_sec=duration)
            context.results[self.name] = res
            logger.info(f"stage={self.name} event=ok duration_ms={int(duration*1000)}")
            return res
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"stage={self.name} event=failed error={type(e).__name__}: {e}"
            logger.error(error_msg)
            res = StageResult(name=self.name, ok=False, error=error_msg, duration_sec=duration)
            context.results[self.name] = res
            return res

class ZSPipeline:
    def __init__(
        self,
        project_id: str,
        config: Dict[str, Any],
        checkpoint_dir: Path | str | None = None,
    ):
        """Создать пайплайн с опциональным checkpoint-каталогом конкретного запуска.

        Старый путь ``output/<project_id>/checkpoints`` сохранён по умолчанию.
        Явный путь нужен изолированным запускам (например, smoke God Mode),
        где артефакты располагаются в отдельном ``out_root``.
        """
        self.context = PipelineContext(project_id=project_id, config=config)
        self.stages: List[PipelineStage] = []
        self.checkpoint_dir = (
            Path(checkpoint_dir)
            if checkpoint_dir is not None
            else Path("output") / project_id / "checkpoints"
        )
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def add_stage(self, name: str, func: Callable[[PipelineContext], Any]):
        self.stages.append(PipelineStage(name, func))
        return self

    def _save_checkpoint(self, stage_name: str, result: StageResult):
        """Сохраняет состояние стадии на диск (в безопасном JSON формате)."""
        cp_path = self.checkpoint_dir / f"{stage_name}.json"
        try:
            with open(cp_path, "w", encoding="utf-8") as f:
                json.dump({
                    "ok": result.ok,
                    "output": result.output,
                    "duration": result.duration_sec
                }, f, ensure_ascii=False, default=str)
        except Exception as e:
            logger.warning(f"Failed to save checkpoint for {stage_name}: {e}")

    # v30: чекпоинты живут максимум 24 часа — старый fail-чекпоинт не
    # должен вечно блокировать пайплайн после исправления кода.
    CHECKPOINT_TTL_SEC = 24 * 3600

    def run(self, use_checkpoints: bool = True) -> Dict[str, Any]:
        logger.info(f"Launching pipeline for project: {self.context.project_id}")

        # v30: ZSMM_NO_CHECKPOINTS=1 полностью отключает чтение чекпоинтов
        if os.environ.get("ZSMM_NO_CHECKPOINTS") == "1":
            use_checkpoints = False

        for stage in self.stages:
            # Проверка чекпоинта (JSON формат для безопасности)
            cp_path = self.checkpoint_dir / f"{stage.name}.json"
            if use_checkpoints and cp_path.exists():
                try:
                    age = time.time() - cp_path.stat().st_mtime
                except Exception:
                    age = 0.0
                if age > self.CHECKPOINT_TTL_SEC:
                    logger.info(f"Checkpoint for {stage.name} expired ({int(age/3600)}h), re-running stage")
                else:
                    logger.info(f"Loading checkpoint for stage: {stage.name}")
                    try:
                        with open(cp_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
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
