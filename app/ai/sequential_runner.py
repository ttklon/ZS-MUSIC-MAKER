# -*- coding: utf-8 -*-
"""Последовательный AI runner: одна тяжёлая модель в VRAM и явные stage limits."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from app.ai.registry import MODEL_REGISTRY, registry
from app.pipeline import StageStatus

logger = logging.getLogger("SequentialAIRunner")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [AI] %(levelname)s %(message)s",
    )

DEFAULT_STAGE_TIMEOUT_SEC = 600.0
MUSIC_STAGE_TIMEOUT_SEC = 1800.0


class StageTimeoutError(TimeoutError):
    """Стадия превысила индивидуальный time limit."""


class StageOOMError(RuntimeError):
    """Измеренное потребление VRAM вышло за budget runner."""


@dataclass
class AIStage:
    name: str
    model: Optional[str]
    fn: Callable[[Any, Any], Any]
    optional: bool = False
    unload_after: bool = True
    fallback_fn: bool = True  # модели нет -> всё равно вызвать fn(None, ctx)
    timeout_sec: Optional[float] = None


@dataclass
class StageReport:
    name: str
    ok: bool
    used_model: Optional[str]
    device: Optional[str]
    duration_sec: float
    timeout_sec: float
    vram_before_gb: float
    vram_after_gb: float
    output_summary: str = ""
    error: Optional[str] = None
    skipped_reason: Optional[str] = None
    status: StageStatus = StageStatus.OK

    def __post_init__(self) -> None:
        """Статус выводится из факта запуска: ошибка → FAILED, пропуск → BLOCKED."""
        if self.error:
            self.status = StageStatus.FAILED
        elif self.skipped_reason:
            self.status = StageStatus.BLOCKED
        else:
            self.status = StageStatus.OK


@dataclass
class RunReport:
    stages: List[StageReport] = field(default_factory=list)
    total_sec: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_sec": round(self.total_sec, 2),
            "stages": [
                {
                    "name": stage.name,
                    "ok": stage.ok,
                    "status": stage.status.value,
                    "used_model": stage.used_model,
                    "device": stage.device,
                    "duration_sec": round(stage.duration_sec, 2),
                    "timeout_sec": round(stage.timeout_sec, 2),
                    "vram_before_gb": round(stage.vram_before_gb, 3),
                    "vram_after_gb": round(stage.vram_after_gb, 3),
                    "output_summary": stage.output_summary,
                    "error": stage.error,
                    "skipped_reason": stage.skipped_reason,
                }
                for stage in self.stages
            ],
        }


def _default_vram_probe() -> float:
    """Вернуть текущий VRAM allocation/reservation, либо 0 на CPU-only host."""
    try:
        import torch

        if not torch.cuda.is_available():
            return 0.0
        allocated = float(torch.cuda.memory_allocated())
        reserved = float(torch.cuda.memory_reserved())
        return max(allocated, reserved) / (1024 ** 3)
    except Exception:
        return 0.0


class SequentialAIRunner:
    def __init__(self, *, vram_budget_gb: Optional[float] = None,
                 vram_probe: Optional[Callable[[], float]] = None):
        self.stages: List[AIStage] = []
        self._sink: Dict[str, Any] = {}
        self.vram_budget_gb = float(
            registry.hw.vram_gb if vram_budget_gb is None else vram_budget_gb
        )
        self._vram_probe = vram_probe or _default_vram_probe

    def add(self, stage: AIStage) -> "SequentialAIRunner":
        self.stages.append(stage)
        return self

    def sink(self) -> Dict[str, Any]:
        return self._sink

    @staticmethod
    def _timeout_for(stage: AIStage) -> float:
        if stage.timeout_sec is not None:
            return float(stage.timeout_sec)
        if stage.model in {"music_generation", "music_stereo"}:
            return MUSIC_STAGE_TIMEOUT_SEC
        return DEFAULT_STAGE_TIMEOUT_SEC

    def _read_vram(self) -> float:
        try:
            return max(0.0, float(self._vram_probe()))
        except Exception as exc:
            logger.warning("VRAM probe failed: %s", exc)
            return 0.0

    def _check_vram(self, stage_name: str, phase: str) -> float:
        used_gb = self._read_vram()
        if used_gb > self.vram_budget_gb:
            raise StageOOMError(
                f"oom: {used_gb:.3f} GB exceeds {self.vram_budget_gb:.3f} GB "
                f"budget ({phase}, stage '{stage_name}')"
            )
        return used_gb

    @staticmethod
    def _notify_progress(progress: Any, method: str, *args: Any) -> None:
        """Display is optional; a terminal write must never break a render."""
        if progress is None:
            return
        try:
            callback = getattr(progress, method, None)
            if callable(callback):
                callback(*args)
        except Exception as exc:
            logger.warning("terminal progress callback failed: %s", exc)

    def run(self, context: Optional[Dict[str, Any]] = None, progress: Any = None) -> RunReport:
        if context is None:
            context = {}
        context["sink"] = self._sink
        report = RunReport()
        t0 = time.time()
        for index, stage in enumerate(self.stages, start=1):
            started_at = time.time()
            timeout_sec = self._timeout_for(stage)
            used_model, device = stage.model, None
            output: Any = None
            error: Optional[str] = None
            skipped_reason: Optional[str] = None
            ok = True
            vram_before = self._read_vram()
            vram_after = vram_before
            self._notify_progress(progress, "stage_start", index, stage.name, vram_before)
            try:
                self._check_vram(stage.name, "before stage")
                from app.ai.stage_process import execute
                result = execute(stage, context, timeout_sec, self.vram_budget_gb)
                self._sink = context['sink']
                output, device = result['output'], result['device']
                skipped_reason = result['skipped']
            except TimeoutError as exc:
                ok = False
                error = str(exc)
                logger.error("x %s", error)
            except StageOOMError as exc:
                ok = False
                error = str(exc)
                logger.error("x %s", error)
            except Exception as exc:
                ok = False
                error = str(exc)
                logger.exception("x stage '%s' crashed: %s", stage.name, exc)
            finally:
                vram_after = self._read_vram()

            if output is not None:
                self._sink[stage.name] = output
            duration_sec = time.time() - started_at
            logger.info(
                "<- stage '%s' ok=%s duration=%.2fs VRAM %.3f->%.3f GB",
                stage.name, ok, duration_sec, vram_before, vram_after,
            )
            stage_report = StageReport(
                name=stage.name,
                ok=ok,
                used_model=used_model,
                device=device,
                duration_sec=duration_sec,
                timeout_sec=timeout_sec,
                vram_before_gb=vram_before,
                vram_after_gb=vram_after,
                output_summary=_summarize(output),
                error=error,
                skipped_reason=skipped_reason,
            )
            report.stages.append(stage_report)
            self._notify_progress(progress, "stage_finish", index, stage_report)
        report.total_sec = time.time() - t0
        logger.info("pipeline done in %.1fs", report.total_sec)
        return report


def _summarize(out: Any) -> str:
    if out is None:
        return ""
    if isinstance(out, (str, int, float, bool)):
        rendered = str(out)
        return rendered if len(rendered) < 200 else rendered[:200] + "..."
    if isinstance(out, dict):
        return f"dict(keys={list(out.keys())[:6]})"
    if isinstance(out, (list, tuple)):
        return f"{type(out).__name__}(len={len(out)})"
    return type(out).__name__
