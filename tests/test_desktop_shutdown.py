"""Queue shutdown contracts; real worker threads, no Windows or live GUI claim."""
from concurrent.futures import ThreadPoolExecutor
import threading
import time

import pytest

from app.runtime_orchestrator import RuntimeOrchestrator


def wait_until(predicate, timeout=3):
    deadline = time.monotonic() + timeout
    while not predicate():
        if time.monotonic() >= deadline:
            pytest.fail('worker did not reach expected state')
        threading.Event().wait(0.01)


def test_queued_jobs_prevent_shutdown_without_discarding_them(tmp_path, monkeypatch):
    import app.runtime_orchestrator as module
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    runtime = RuntimeOrchestrator()
    runtime.stop()
    monkeypatch.setattr(runtime, '_ensure_worker', lambda: None)
    tid = runtime.enqueue({'theme': 'queued'})
    assert not runtime.shutdown_if_idle()
    assert runtime._queue == [tid] and runtime.jobs[tid].status == 'pending'
    assert not runtime._closing


def test_active_worker_prevents_shutdown_even_after_status_done(tmp_path, monkeypatch):
    import app.runtime_orchestrator as module
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    runtime = RuntimeOrchestrator()
    entered, release = threading.Event(), threading.Event()
    def process(job):
        job.status = 'done'  # worker has not returned from finalization yet
        entered.set()
        assert release.wait(3)
    monkeypatch.setattr(runtime, '_process', process)
    tid = runtime.enqueue({'theme': 'running'})
    try:
        assert entered.wait(3)
        assert runtime.jobs[tid].status == 'done'
        assert not runtime.shutdown_if_idle()
        release.set()
        wait_until(lambda: runtime.shutdown_if_idle())
        assert runtime.jobs[tid].status == 'done'
        assert runtime._stop.is_set()
        with pytest.raises(RuntimeError, match='shutting down'):
            runtime.enqueue({'theme': 'late'})
        assert len(runtime.jobs) == 1
    finally:
        release.set()
        runtime.stop()


def test_shutdown_and_enqueue_are_serialized_without_orphaned_jobs(tmp_path, monkeypatch):
    import app.runtime_orchestrator as module
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    for i in range(10):
        runtime = RuntimeOrchestrator()
        runtime.stop()
        monkeypatch.setattr(runtime, '_ensure_worker', lambda: None)
        gate = threading.Barrier(2)
        def close():
            gate.wait()
            return runtime.shutdown_if_idle()
        def enqueue():
            gate.wait()
            try:
                return runtime.enqueue({'theme': str(i)})
            except RuntimeError:
                return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            a, b = pool.submit(close), pool.submit(enqueue)
            closed, tid = a.result(), b.result()
        assert (closed and tid is None and not runtime.jobs) or (
            not closed and tid in runtime.jobs and runtime._queue == [tid])


def test_worker_unexpected_failure_is_visible_and_does_not_strand_queue(tmp_path, monkeypatch):
    import app.runtime_orchestrator as module
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    runtime = RuntimeOrchestrator()
    def fail(job):
        raise OSError('project directory unavailable')
    monkeypatch.setattr(runtime, '_process', fail)
    first = runtime.enqueue({'theme': 'one'})
    second = runtime.enqueue({'theme': 'two'})
    try:
        wait_until(lambda: all(runtime.jobs[x].status == 'error' for x in (first, second)))
        wait_until(lambda: runtime.shutdown_if_idle())
        assert 'project directory unavailable' in runtime.jobs[first].error
        assert 'project directory unavailable' in runtime.jobs[second].error
    finally:
        runtime.stop()
