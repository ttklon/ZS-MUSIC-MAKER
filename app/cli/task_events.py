"""Versioned NDJSON task messages; unrelated stdout is never a result."""
from __future__ import annotations

import json
import os
import uuid

from app.cli.env import safe_print


class TaskEvents:
    def __init__(self, task_id: str | None = None):
        self.task_id = task_id or os.environ.get('ZSMM_TASK_ID') or uuid.uuid4().hex
        self.seq = 0
        self.finished = False

    def emit(self, event_type: str, **payload) -> None:
        if self.finished or event_type not in ('progress', 'artifact', 'error', 'done'):
            raise ValueError('invalid task event transition')
        self.seq += 1
        event = dict(schema='zsmm.task', version=1, task_id=self.task_id,
                     seq=self.seq, type=event_type, **payload)
        # JSON escapes embedded line breaks and supports Windows legacy codepages.
        safe_print(json.dumps(event, ensure_ascii=True, allow_nan=False))
        self.finished = event_type == 'done'

    def progress(self, message: str) -> None:
        self.emit('progress', message=message)
