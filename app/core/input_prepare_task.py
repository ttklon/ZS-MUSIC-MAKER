"""Read-only background preparation for explicit replacement inputs.

The worker cannot reserve a directory, create a job, or touch Qt. Cancellation
is cooperative between file reads; a blocked OS/network read can outlive the
dialog, so the thread is daemonized and never performs a later enqueue.
"""
from __future__ import annotations

import copy
import threading

from app.core.project_inputs import InputPreparationCancelled, prepare_replacements


class InputPreparationTask:
    def __init__(self, replacements: dict):
        self._replacements = copy.deepcopy(replacements)
        self._cancel = threading.Event()
        self._lock = threading.Lock()
        self._consumed = False
        self.done = threading.Event()
        self._result: dict | None = None
        self.error: str | None = None
        self.was_cancelled = False
        self._thread = threading.Thread(target=self._run, name="input-preparation", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def cancel(self) -> None:
        with self._lock:
            self._cancel.set()

    def take_result(self) -> dict:
        """Consume a successful, uncancelled preparation once before enqueue."""
        with self._lock:
            if (not self.done.is_set() or self._cancel.is_set() or self.was_cancelled
                    or self.error is not None or self._result is None or self._consumed):
                raise ValueError("input preparation is cancelled, unfinished, failed or already consumed")
            self._consumed = True
            return copy.deepcopy(self._result)

    def _run(self) -> None:
        try:
            self._result = prepare_replacements(self._replacements, cancelled=self._cancel.is_set)
            if self._cancel.is_set():
                self._result = None
                self.was_cancelled = True
        except InputPreparationCancelled:
            self.was_cancelled = True
        except Exception as exc:  # noqa: BLE001 - transfer error, never queue from this thread
            self.error = f"{type(exc).__name__}: {exc}"
        finally:
            self.done.set()
