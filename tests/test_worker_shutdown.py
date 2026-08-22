from __future__ import annotations

import time

from app.runtime_orchestrator import RuntimeOrchestrator
from modules.render_queue import RenderQueue


def test_idle_workers_stop_promptly_via_stop_events() -> None:
    runtime = RuntimeOrchestrator(log=None)
    queue = RenderQueue(orchestrator=object(), log=lambda _message: None)
    queue.start()

    started = time.monotonic()
    runtime.stop(join_timeout=0.5)
    queue.stop()
    assert queue._worker is not None
    queue._worker.join(timeout=0.5)
    elapsed = time.monotonic() - started

    assert runtime._worker is not None
    assert not runtime._worker.is_alive()
    assert not queue._worker.is_alive()
    assert elapsed < 0.5
