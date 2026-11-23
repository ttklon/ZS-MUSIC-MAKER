"""Stage liveness is not progress or inference success; never cancels CPU work on silence."""
from contextlib import contextmanager
import logging
import threading


@contextmanager
def stage_activity(stage_name: str, interval_sec: float = 15.0):
    stop = threading.Event()
    def heartbeat():
        while not stop.wait(interval_sec):
            logging.getLogger('SequentialAIRunner').info(
                'stage heartbeat: %s; alive is not measured model progress', stage_name)
    thread = threading.Thread(target=heartbeat, daemon=True, name='stage-heartbeat')
    thread.start()
    try:
        yield
    finally:
        stop.set()
        thread.join(timeout=1.0)
