# -*- coding: utf-8 -*-
from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.orchestrator import run_full_pipeline

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Job:
    track_id: str
    recipe: Dict[str, Any]
    status: str = "pending"
    progress: float = 0.0
    stage: str = "queued"
    project_dir: str = ""
    error: str = ""
    started_at: float = 0.0
    finished_at: float = 0.0
    result: Dict[str, Any] = field(default_factory=dict)


class RuntimeOrchestrator:
    def __init__(self, log=None):
        self.log = log
        self.jobs: Dict[str, Job] = {}
        self._queue: List[str] = []
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._worker: Optional[threading.Thread] = None
        self._ensure_worker()

    def _log(self, msg: str):
        try:
            if self.log is not None and hasattr(self.log, "info"):
                self.log.info(msg)
            else:
                print(msg)
        except Exception:
            pass

    def _ensure_worker(self):
        if self._worker and self._worker.is_alive():
            return
        self._stop.clear()
        self._worker = threading.Thread(target=self._run_loop, daemon=True)
        self._worker.start()

    def enqueue(self, recipe: Dict[str, Any]) -> str:
        tid = uuid.uuid4().hex[:10]
        out_dir = ROOT / 'output' / 'desktop_runs' / tid
        job = Job(track_id=tid, recipe=dict(recipe or {}), project_dir=str(out_dir))
        with self._lock:
            self.jobs[tid] = job
            self._queue.append(tid)
        self._ensure_worker()
        self._log(f"[runtime_orch] enqueued {tid}")
        return tid

    def enqueue_batch(self, recipes: List[Dict[str, Any]]) -> List[str]:
        return [self.enqueue(r) for r in (recipes or [])]

    def _run_loop(self):
        while not self._stop.is_set():
            tid = None
            with self._lock:
                if self._queue:
                    tid = self._queue.pop(0)
            if not tid:
                time.sleep(0.2)
                continue
            job = self.jobs.get(tid)
            if job:
                self._process(job)

    def _process(self, job: Job):
        out_dir = Path(job.project_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        job.status = 'running'
        job.stage = 'pipeline'
        job.progress = 0.1
        job.started_at = time.time()
        try:
            res = run_full_pipeline(job.track_id, job.recipe, dry_run=False, out_root=out_dir)
            job.progress = 0.92
            stages = res.get('stages') or []
            release_dir = None
            master_path = None
            hit = {}
            for st in stages:
                name = st.get('name')
                out = st.get('output') or {}
                if name == '_stage_release_pack':
                    release_dir = out.get('path') or release_dir
                elif name == '_stage_polish':
                    master_path = out.get('path') or out.get('out_wav') or master_path
                elif name == '_stage_mastering' and not master_path:
                    master_path = (out.get('stands', {}) or {}).get('streaming', {}).get('out_wav')
                elif name == '_stage_hit_score':
                    hit = out

            advice = [a.strip() for a in (hit.get('actions') or [])[:4] if isinstance(a, str) and a.strip()]
            flags = [w.strip() for w in (res.get('warnings') or [])[:4] if isinstance(w, str) and w.strip()]

            job.result = {
                'pipeline': res,
                'master': master_path,
                'master_path': master_path,
                'release': {'release_dir': release_dir},
                'ai_detector': {
                    'ok': bool(hit),
                    'verdict': hit.get('verdict'),
                    'score': hit.get('hit_score'),
                    'flags': flags,
                    'advice': advice,
                },
            }
            job.status = 'done' if res.get('verdict') not in ('FAILED',) else 'error'
            job.stage = str(res.get('verdict') or 'done').lower()
            job.progress = 1.0 if job.status == 'done' else 0.0
            if job.status == 'error':
                job.error = str(res.get('warnings') or ['pipeline failed'])
        except Exception as e:
            job.status = 'error'
            job.stage = 'failed'
            job.error = f'{type(e).__name__}: {e}'[:500]
            job.progress = 0.0
        finally:
            job.finished_at = time.time()
