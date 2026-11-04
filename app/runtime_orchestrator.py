from __future__ import annotations

import copy
import hashlib
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
    revision_source_id: str | None = None
    source_report_id: str | None = None
    source_report_sha256: str | None = None
    master_only: bool = False


def _summarize_pipeline_result(result: dict[str, Any]) -> dict[str, Any]:
    """Extract desktop job fields from the stable full-pipeline result contract."""
    release_dir = None
    master_path = result.get("master_path")
    hit: dict[str, Any] = {}
    for stage in result.get("stages") or []:
        name = stage.get("name")
        output = stage.get("output") or {}
        if name == "_stage_release_pack":
            release_dir = output.get("path") or release_dir
        elif name == "_stage_polish" and not result.get("master_path"):
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

    def _reserve_project(self, source_dir: str | None = None) -> tuple[str, Path]:
        base = ROOT / "output" / "desktop_runs"
        if source_dir:
            source = Path(source_dir).resolve()
            if base.resolve() == source or base.resolve().is_relative_to(source):
                raise ValueError("revision destination would be inside the source project")
        base.mkdir(parents=True, exist_ok=True)
        for _ in range(32):
            tid = uuid.uuid4().hex
            if tid in self.jobs:
                continue
            path = base / tid
            try:
                path.mkdir()
            except FileExistsError:
                continue
            return tid, path
        raise RuntimeError("could not reserve a unique project directory")

    def open_project(self, project_dir: str | Path) -> str:
        """Open an explicitly selected project for re-mastering, never a full resume."""
        from app.core.project_snapshot import read_project_report, restore_recipe
        from app.core.revision import validate_master_source

        source = Path(project_dir).resolve(strict=True)
        if not source.is_dir():
            raise ValueError("select a project directory")
        report, raw = read_project_report(source)
        project_id = report.get("project_id")
        if not isinstance(project_id, str) or not project_id or len(project_id) > 200:
            raise ValueError("invalid project id")
        recipe = restore_recipe(report)
        validate_master_source(source, report)
        with self._lock:
            for _ in range(32):
                tid = "opened-" + uuid.uuid4().hex
                if tid not in self.jobs:
                    break
            else:
                raise RuntimeError("could not allocate a unique job id")
            summary = _summarize_pipeline_result(report)
            # Old master/release paths may be stale after a project was moved.
            summary.update(master=None, master_path=None, release={"release_dir": None})
            self.jobs[tid] = Job(
                track_id=tid, recipe=recipe, status="done", stage="opened",
                project_dir=str(source), result=summary,
                source_report_id=project_id, source_report_sha256=hashlib.sha256(raw).hexdigest(),
                master_only=True,
            )
        return tid

    def enqueue(self, recipe: dict[str, Any], only: set[str] | None = None) -> str:
        """Поставить трек в очередь.

        `only` — подмножество стадий (`STAGE_KEYS`) в новой директории.
        Переиспользование предыдущего проекта здесь не реализовано.
        """
        payload = copy.deepcopy(recipe or {})
        if only:
            payload["only"] = sorted(only)
        with self._lock:
            tid, out_dir = self._reserve_project()
            job = Job(track_id=tid, recipe=payload, project_dir=str(out_dir))
            self.jobs[tid] = job
            self._queue.append(tid)
        self._ensure_worker()
        self._log(f"[runtime_orch] enqueued {tid}")
        return tid

    def enqueue_master_revision(self, source_id: str, overrides: dict[str, Any] | None = None) -> str:
        """Create a new job from a completed or explicitly opened project."""
        with self._lock:
            source = self.jobs.get(source_id)
            if not source or source.status != "done":
                raise ValueError("source project is not a completed or opened job")
            source_report = source.result.get("pipeline") or {}
            if (source_report.get("only") or source_report.get("resume") or source_report.get("dry_run")
                    or not (source_report.get("artifact_integrity") or {}).get("mix")):
                raise ValueError("source has no verified full-run mix manifest; run a new full render first")
            payload = copy.deepcopy(source.recipe)
            payload.pop("only", None)
            for key in ("stands", "export_stems"):
                if key in (overrides or {}):
                    payload[key] = copy.deepcopy(overrides[key])
            tid, out_dir = self._reserve_project(source.project_dir)
            job = Job(track_id=tid, recipe=payload, project_dir=str(out_dir),
                      revision_source_id=source_id, master_only=source.master_only)
            self.jobs[tid] = job
            self._queue.append(tid)
        self._ensure_worker()
        self._log(f"[runtime_orch] enqueued mastering revision {tid} from {source_id}")
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

            reused_stages = None
            if job.revision_source_id:
                from app.core.project_snapshot import read_project_report
                from app.core.revision import prepare_master_revision

                source = self.jobs.get(job.revision_source_id)
                if not source or source.status != "done":
                    raise ValueError("source job is no longer available")
                source_report, raw = read_project_report(Path(source.project_dir))
                if source.source_report_sha256 and hashlib.sha256(raw).hexdigest() != source.source_report_sha256:
                    raise ValueError("source report changed since opening; open it again")
                if source_report.get("project_id") != (source.source_report_id or source.track_id):
                    raise ValueError("source report project id does not match")
                reused_stages = prepare_master_revision(Path(source.project_dir), out_dir, source_report)
            result = run_full_pipeline(
                job.track_id,
                job.recipe,
                dry_run=False,
                out_root=out_dir,
                on_stage=on_stage,
                reused_stages=reused_stages,
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
