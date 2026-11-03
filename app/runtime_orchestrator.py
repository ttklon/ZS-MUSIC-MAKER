from __future__ import annotations

import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.core.orchestrator import run_full_pipeline

ROOT = Path(__file__).resolve().parents[1]
LOGGER = logging.getLogger(__name__)


@dataclass
class Job:
    track_id: str
    recipe: dict[str, Any]
    status: str = "pending"
    progress: float = 0.0
    stage: str = "queued"
    project_dir: str = ""
    error: str = ""
    started_at: float = 0.0
    finished_at: float = 0.0
    result: dict[str, Any] = field(default_factory=dict)


def _summarize_pipeline_result(result: dict[str, Any]) -> dict[str, Any]:
    """Extract desktop job fields from the stable full-pipeline result contract."""
    release_dir = None
    master_path = None
    hit: dict[str, Any] = {}
    for stage in result.get("stages") or []:
        name = stage.get("name")
        output = stage.get("output") or {}
        if name == "_stage_release_pack":
            release_dir = output.get("path") or release_dir
        elif name == "_stage_polish":
            master_path = output.get("path") or output.get("out_wav") or master_path
        elif name == "_stage_mastering" and not master_path:
            master_path = (output.get("stands", {}) or {}).get("streaming", {}).get("out_wav")
        elif name == "_stage_hit_score":
            hit = output

    advice = [
        value.strip()
        for value in (hit.get("actions") or [])[:4]
        if isinstance(value, str) and value.strip()
    ]
    flags = [
        value.strip()
        for value in (result.get("warnings") or [])[:4]
        if isinstance(value, str) and value.strip()
    ]
    return {
        "pipeline": result,
        "master": master_path,
        "master_path": master_path,
        "release": {"release_dir": release_dir},
        "ai_detector": {
            "ok": bool(hit),
            "verdict": hit.get("verdict"),
            "score": hit.get("hit_score"),
            "flags": flags,
            "advice": advice,
        },
    }


class RuntimeOrchestrator:
    def __init__(self, log=None):
        self.log = log
        self.jobs: dict[str, Job] = {}
        self._queue: list[str] = []
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._worker: threading.Thread | None = None
        self._ensure_worker()

    def _log(self, msg: str) -> None:
        """Send runtime diagnostics without allowing an optional sink to hide failures."""
        try:
            if self.log is not None and hasattr(self.log, "info"):
                self.log.info(msg)
            else:
                LOGGER.info(msg)
        except Exception as error:
            LOGGER.warning("runtime diagnostic sink failed: %s", error)

    def _ensure_worker(self):
        if self._worker and self._worker.is_alive():
            return
        self._stop.clear()
        self._worker = threading.Thread(target=self._run_loop, daemon=True)
        self._worker.start()

    def stop(self, join_timeout: float = 1.0) -> None:
        """Request worker shutdown and wait briefly when it is idle."""
        self._stop.set()
        worker = self._worker
        if worker and worker is not threading.current_thread():
            worker.join(timeout=max(0.0, float(join_timeout)))

    def enqueue(self, recipe: dict[str, Any], only: set[str] | None = None) -> str:
        """Поставить трек в очередь.

        `only` — подмножество стадий (`STAGE_KEYS`): так работает «переделать
        только вокал/мастер» из экрана результата, без полной пересборки.
        """
        tid = uuid.uuid4().hex[:10]
        out_dir = ROOT / "output" / "desktop_runs" / tid
        payload = dict(recipe or {})
        if only:
            payload["only"] = sorted(only)
        job = Job(track_id=tid, recipe=payload, project_dir=str(out_dir))
        with self._lock:
            self.jobs[tid] = job
            self._queue.append(tid)
        self._ensure_worker()
        self._log(f"[runtime_orch] enqueued {tid}")
        return tid

    def enqueue_batch(self, recipes: list[dict[str, Any]]) -> list[str]:
        return [self.enqueue(r) for r in (recipes or [])]

    def _run_loop(self):
        while not self._stop.is_set():
            tid = None
            with self._lock:
                if self._queue:
                    tid = self._queue.pop(0)
            if not tid:
                # Event.wait preserves the poll interval but wakes immediately
                # when shutdown is requested instead of blocking on sleep.
                self._stop.wait(0.2)
                continue
            job = self.jobs.get(tid)
            if job:
                self._process(job)

    def _process(self, job: Job):
        out_dir = Path(job.project_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        job.status = "running"
        job.stage = "pipeline"
        job.progress = 0.1
        job.started_at = time.time()
        try:
            def on_stage(name: str, status: str, index: int, total: int) -> None:
                """Прогресс по факту: имя стадии и её статус из пайплайна."""
                job.stage = f"{name}:{status}".lower()
                # 5 % — старт, 95 % — конец: полоска не «прыгает» в 100 % заранее
                job.progress = min(0.95, 0.05 + 0.9 * index / max(total, 1))

            result = run_full_pipeline(
                job.track_id,
                job.recipe,
                dry_run=False,
                out_root=out_dir,
                on_stage=on_stage,
            )
            job.progress = 0.92
            job.result = _summarize_pipeline_result(result)
            job.status = "done" if result.get("verdict") not in ("FAILED",) else "error"
            job.stage = str(result.get("verdict") or "done").lower()
            job.progress = 1.0 if job.status == "done" else 0.0
            if job.status == "error":
                job.error = str(result.get("warnings") or ["pipeline failed"])
        except Exception as error:
            job.status = "error"
            job.stage = "failed"
            job.error = f"{type(error).__name__}: {error}"[:500]
            job.progress = 0.0
        finally:
            job.finished_at = time.time()
