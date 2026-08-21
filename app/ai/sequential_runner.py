# -*- coding: utf-8 -*-
"""Последовательный AI runner: одна тяжёлая модель в VRAM и явные stage limits."""
from __future__ import annotations

import gc
import logging
import os
import signal
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterator, List, Optional

from app.ai.registry import MODEL_REGISTRY, registry

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


@contextmanager
def _stage_watchdog(timeout_sec: float, stage_name: str) -> Iterator[None]:
    """Остановить зависшую stage на POSIX и явно отметить timeout везде.

    Handle моделей остаётся в текущем process и не сериализуется в дочерний
    process. Поэтому на Linux применяется SIGALRM, который прерывает Python
    вызов; daemon watchdog-thread служит fallback-маркером там, где сигнал
    недоступен. Небезопасное принудительное убийство потока намеренно не
    используется: оно могло бы оставить CUDA/файловое состояние повреждённым.
    """
    if timeout_sec <= 0:
        raise ValueError("stage timeout_sec must be positive")
    fired = threading.Event()
    watchdog = threading.Timer(timeout_sec, fired.set)
    watchdog.daemon = True
    watchdog.start()

    can_interrupt = (
        os.name != "nt"
        and threading.current_thread() is threading.main_thread()
        and hasattr(signal, "SIGALRM")
        and hasattr(signal, "setitimer")
    )
    old_handler = None
    old_timer: tuple[float, float] | None = None

    def _timeout_handler(_signum: int, _frame: Any) -> None:
        fired.set()
        raise StageTimeoutError(f"stage '{stage_name}' timed out after {timeout_sec:.1f}s")

    try:
        if can_interrupt:
            old_handler = signal.getsignal(signal.SIGALRM)
            signal.signal(signal.SIGALRM, _timeout_handler)
            old_timer = signal.setitimer(signal.ITIMER_REAL, timeout_sec)
        yield
        if fired.is_set():
            raise StageTimeoutError(f"stage '{stage_name}' timed out after {timeout_sec:.1f}s")
    finally:
        watchdog.cancel()
        if can_interrupt:
            signal.setitimer(signal.ITIMER_REAL, 0.0)
            signal.signal(signal.SIGALRM, old_handler)
            if old_timer and old_timer[0] > 0:
                signal.setitimer(signal.ITIMER_REAL, old_timer[0], old_timer[1])


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
    def _invoke(stage: AIStage, handle: Any, context: Dict[str, Any], timeout_sec: float) -> Any:
        with _stage_watchdog(timeout_sec, stage.name):
            return stage.fn(handle, context)

    def run(self, context: Optional[Dict[str, Any]] = None) -> RunReport:
        context = context or {}
        context["sink"] = self._sink
        report = RunReport()
        t0 = time.time()
        for stage in self.stages:
            started_at = time.time()
            timeout_sec = self._timeout_for(stage)
            used_model, device = stage.model, None
            output: Any = None
            error: Optional[str] = None
            skipped_reason: Optional[str] = None
            ok = True
            vram_before = self._read_vram()
            vram_after = vram_before
            try:
                self._check_vram(stage.name, "before stage")
                if stage.model is None:
                    logger.info("-> stage '%s' (pure DSP, timeout=%.1fs, VRAM=%.3f GB)",
                                stage.name, timeout_sec, vram_before)
                    output = self._invoke(stage, None, context, timeout_sec)
                elif stage.model not in MODEL_REGISTRY:
                    raise KeyError(f"Model role '{stage.model}' not in registry")
                elif not registry.is_available(stage.model):
                    reason = f"{stage.model} unavailable (deps/weights missing)"
                    if stage.optional and stage.fallback_fn:
                        logger.warning("-> stage '%s' FALLBACK (%s)", stage.name, reason)
                        skipped_reason = reason + " -> fallback_fn ran"
                        output = self._invoke(stage, None, context, timeout_sec)
                    elif stage.optional:
                        skipped_reason = reason
                    else:
                        ok = False
                        error = reason
                else:
                    logger.info("-> stage '%s' loading '%s' (timeout=%.1fs)",
                                stage.name, stage.model, timeout_sec)
                    loaded = registry.load(stage.model)
                    device = loaded.device
                    self._check_vram(stage.name, "after model load")
                    output = self._invoke(stage, loaded.handle, context, timeout_sec)
            except StageTimeoutError as exc:
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
                if stage.unload_after:
                    registry.unload()
                    gc.collect()
                vram_after = self._read_vram()

            if output is not None:
                self._sink[stage.name] = output
            duration_sec = time.time() - started_at
            logger.info(
                "<- stage '%s' ok=%s duration=%.2fs VRAM %.3f->%.3f GB",
                stage.name, ok, duration_sec, vram_before, vram_after,
            )
            report.stages.append(StageReport(
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
            ))
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
