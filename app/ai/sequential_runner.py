# -*- coding: utf-8 -*-
"""ZS Music Maker - app/ai/sequential_runner.py (v38)
Последовательный раннер: одна тяжёлая модель в VRAM за раз."""
from __future__ import annotations
import gc, time, logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from app.ai.registry import registry, MODEL_REGISTRY

logger = logging.getLogger("SequentialAIRunner")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [AI] %(levelname)s %(message)s")


@dataclass
class AIStage:
    name: str
    model: Optional[str]
    fn: Callable[[Any, Any], Any]
    optional: bool = False
    unload_after: bool = True
    fallback_fn: bool = True   # модели нет -> всё равно вызвать fn(None, ctx)


@dataclass
class StageReport:
    name: str
    ok: bool
    used_model: Optional[str]
    device: Optional[str]
    duration_sec: float
    output_summary: str = ""
    error: Optional[str] = None
    skipped_reason: Optional[str] = None


@dataclass
class RunReport:
    stages: List[StageReport] = field(default_factory=list)
    total_sec: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {"total_sec": round(self.total_sec, 2),
                "stages": [{"name": s.name, "ok": s.ok, "used_model": s.used_model,
                            "device": s.device, "duration_sec": round(s.duration_sec, 2),
                            "output_summary": s.output_summary, "error": s.error,
                            "skipped_reason": s.skipped_reason} for s in self.stages]}


class SequentialAIRunner:
    def __init__(self):
        self.stages: List[AIStage] = []
        self._sink: Dict[str, Any] = {}

    def add(self, stage: AIStage) -> "SequentialAIRunner":
        self.stages.append(stage)
        return self

    def sink(self) -> Dict[str, Any]:
        return self._sink

    def run(self, context: Optional[Dict[str, Any]] = None) -> RunReport:
        context = context or {}
        context["sink"] = self._sink
        report = RunReport()
        t0 = time.time()
        for st in self.stages:
            s0 = time.time()
            used, device = st.model, None
            try:
                if st.model is None:
                    logger.info(f"-> stage '{st.name}' (pure DSP)")
                    out = st.fn(None, context)
                    report.stages.append(StageReport(
                        name=st.name, ok=True, used_model=None, device=None,
                        duration_sec=time.time() - s0, output_summary=_summarize(out)))
                    self._sink[st.name] = out
                    continue
                if st.model not in MODEL_REGISTRY:
                    raise KeyError(f"Model role '{st.model}' not in registry")
                if not registry.is_available(st.model):
                    reason = f"{st.model} unavailable (deps/weights missing)"
                    if st.optional and st.fallback_fn:
                        logger.warning(f"-> stage '{st.name}' FALLBACK ({reason})")
                        out = st.fn(None, context)
                        report.stages.append(StageReport(
                            name=st.name, ok=True, used_model=st.model, device=None,
                            duration_sec=time.time() - s0, output_summary=_summarize(out),
                            skipped_reason=reason + " -> fallback_fn ran"))
                        self._sink[st.name] = out
                        continue
                    if st.optional:
                        report.stages.append(StageReport(
                            name=st.name, ok=True, used_model=st.model, device=None,
                            duration_sec=time.time() - s0, skipped_reason=reason))
                        continue
                    report.stages.append(StageReport(
                        name=st.name, ok=False, used_model=st.model, device=None,
                        duration_sec=time.time() - s0, error=reason))
                    continue
                logger.info(f"-> stage '{st.name}' loading '{st.model}'")
                loaded = registry.load(st.model)
                device = loaded.device
                out = st.fn(loaded.handle, context)
                report.stages.append(StageReport(
                    name=st.name, ok=True, used_model=st.model, device=device,
                    duration_sec=time.time() - s0, output_summary=_summarize(out)))
                self._sink[st.name] = out
            except Exception as e:
                logger.exception(f"x stage '{st.name}' crashed: {e}")
                report.stages.append(StageReport(
                    name=st.name, ok=False, used_model=used, device=device,
                    duration_sec=time.time() - s0, error=str(e)))
            finally:
                if st.unload_after:
                    registry.unload()
                    gc.collect()
        report.total_sec = time.time() - t0
        logger.info(f"pipeline done in {report.total_sec:.1f}s")
        return report


def _summarize(out: Any) -> str:
    if out is None:
        return ""
    if isinstance(out, (str, int, float, bool)):
        s = str(out)
        return s if len(s) < 200 else s[:200] + "..."
    if isinstance(out, dict):
        return f"dict(keys={list(out.keys())[:6]})"
    if isinstance(out, (list, tuple)):
        return f"{type(out).__name__}(len={len(out)})"
    return type(out).__name__
