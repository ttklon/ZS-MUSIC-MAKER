"""
[v8] render_queue.py — Рендер-очередь для ночных пачек (5+ треков).

ТЗ 20.2 п.7: «Объём: ~5 треков в неделю. Добавить рендер-очередь: 5+ проектов
на ночь. Утром — готовый набор.»

Работает поверх Orchestrator: принимает список recipe.json, запускает их
последовательно, ведёт state, умеет восстанавливаться после перезапуска.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE_DIR = ROOT / "output" / "queue"
STATE_FILE = QUEUE_DIR / "queue_state.json"
# v22: ленивое создание (не при импорте)


@dataclass
class QueueItem:
    id: str
    recipe: dict
    status: str = "pending"  # pending | running | done | error | cancelled
    cancel_requested: bool = False
    progress: float = 0.0
    stage: str = ""
    project_dir: str = ""
    error: str = ""
    started_at: float = 0.0
    finished_at: float = 0.0
    result_paths: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


def _load_state() -> list[dict]:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_state(items: list[QueueItem]) -> None:
    STATE_FILE.write_text(
        json.dumps([i.to_dict() for i in items], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


class RenderQueue:
    """
    Автономная очередь. Использует Orchestrator для реального рендера.
    Работает в фоне (демонический поток).
    """

    def __init__(self, orchestrator=None, log: Callable[[str], None] = print):
        self.items: list[QueueItem] = []
        self.orchestrator = orchestrator
        self.log = log
        self._stop = threading.Event()
        self._worker: threading.Thread | None = None
        self._restore()

    # ------------------------------------------------------- persistence
    def _restore(self):
        for d in _load_state():
            # Возвращаем running → pending при рестарте.
            if d.get("status") == "running":
                d["status"] = "pending"
            item = QueueItem(
                **{k: v for k, v in d.items() if k in QueueItem.__dataclass_fields__}
            )
            self.items.append(item)

    def _persist(self):
        _save_state(self.items)

    # ------------------------------------------------------- API
    def enqueue(self, recipe: dict) -> str:
        item = QueueItem(id=uuid.uuid4().hex[:10], recipe=recipe)
        self.items.append(item)
        self._persist()
        self.log(f"[queue] enqueued {item.id} ({recipe.get('theme', '?')})")
        return item.id

    def enqueue_batch(self, recipes: list[dict]) -> list[str]:
        return [self.enqueue(r) for r in recipes]

    def status_summary(self) -> dict:
        c = {"pending": 0, "running": 0, "done": 0, "error": 0, "cancelled": 0}
        for it in self.items:
            c[it.status] = c.get(it.status, 0) + 1
        c["total"] = len(self.items)
        return c

    def list_items(self) -> list[dict]:
        return [i.to_dict() for i in self.items]

    def cancel(self, item_id: str) -> bool:
        for it in self.items:
            if it.id == item_id and it.status == "pending":
                it.status = "cancelled"
                it.error = "cancelled before execution"
                self._persist()
                return True
            if it.id == item_id and it.status == "running":
                it.cancel_requested = True
                self._persist()
                return True
        return False

    def clear_done(self):
        self.items = [i for i in self.items if i.status not in ("done",)]
        self._persist()

    # ------------------------------------------------------- worker
    def start(self):
        if self._worker and self._worker.is_alive():
            return
        self._stop.clear()
        self._worker = threading.Thread(target=self._run_loop, daemon=True)
        self._worker.start()
        self.log("[queue] worker started")

    def stop(self):
        self._stop.set()
        self.log("[queue] stop requested")

    def _run_loop(self):
        while not self._stop.is_set():
            next_item = self._pick_next()
            if not next_item:
                time.sleep(3)
                continue
            self._process(next_item)

    def _pick_next(self) -> QueueItem | None:
        for it in self.items:
            if it.status == "pending":
                return it
        return None

    # ------------------------------------------------------- run one
    def _process(self, item: QueueItem):
        item.status = "running"
        item.started_at = time.time()
        self._persist()
        try:
            if self.orchestrator is None:
                # Ленивый импорт, чтобы модуль работал автономно.
                from app.core.orchestrator import Orchestrator
                from app.hw_probe import probe_hw
                from app.logger import make_logger

                self.orchestrator = Orchestrator(probe_hw(), make_logger())

            def on_stage(stage: str, progress: float):
                if item.cancel_requested or self._stop.is_set():
                    raise RuntimeError("cancelled")
                item.stage = stage
                item.progress = float(progress)
                self._persist()

            res = self.orchestrator.run_pipeline(item.recipe, stage_hook=on_stage)
            item.result_paths = res or {}
            item.status = "done"
            item.progress = 1.0
        except Exception as e:
            if item.cancel_requested or str(e) == "cancelled":
                item.status = "cancelled"
                item.error = "cancelled"
                self.log(f"[queue] {item.id} cancelled")
            else:
                item.status = "error"
                item.error = str(e)[:400]
                self.log(f"[queue] {item.id} FAILED: {e}")
        finally:
            item.finished_at = time.time()
            self._persist()

    # ------------------------------------------------------- morning report
    def morning_report(self) -> dict:
        done = [i for i in self.items if i.status == "done"]
        errs = [i for i in self.items if i.status == "error"]
        pend = [i for i in self.items if i.status == "pending"]
        return {
            "total": len(self.items),
            "done": len(done),
            "errors": len(errs),
            "pending": len(pend),
            "delivered_paths": [i.result_paths for i in done],
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }


if __name__ == "__main__":
    q = RenderQueue()
    print(json.dumps(q.status_summary(), indent=2))
