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
STATE_FILE = QUEUE_DIR / "queue.json"
LEGACY_STATE_FILE = QUEUE_DIR / "queue_state.json"
# v22: ленивое создание (не при импорте)


WORK_KINDS = ("track", "rvc_train_night")


@dataclass
class QueueItem:
    id: str
    recipe: dict
    # pending | running | done | error | cancelled | blocked
    status: str = "pending"
    cancel_requested: bool = False
    progress: float = 0.0
    stage: str = ""
    project_dir: str = ""
    error: str = ""
    started_at: float = 0.0
    finished_at: float = 0.0
    result_paths: dict = field(default_factory=dict)
    priority: int = 0  # higher values run first; ties keep enqueue order
    created_at: float = field(default_factory=time.time)

    def to_dict(self):
        return asdict(self)


def _load_state() -> list[dict]:
    for candidate in (STATE_FILE, LEGACY_STATE_FILE):
        if candidate.exists():
            try:
                payload = json.loads(candidate.read_text(encoding="utf-8"))
                return payload if isinstance(payload, list) else []
            except Exception:
                return []
    return []


def _save_state(items: list[QueueItem]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
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
            # Running work is safe to resume after restart unless cancellation was requested.
            if d.get("status") == "running":
                if d.get("cancel_requested"):
                    d["status"] = "cancelled"
                    d["error"] = "cancelled before restart"
                else:
                    d["status"] = "pending"
                    d["stage"] = ""
                    d["progress"] = 0.0
            item = QueueItem(
                **{k: v for k, v in d.items() if k in QueueItem.__dataclass_fields__}
            )
            self.items.append(item)

    def _persist(self):
        _save_state(self.items)

    # ------------------------------------------------------- API
    def enqueue(self, recipe: dict, priority: int | None = None) -> str:
        requested_priority = recipe.get("priority", 0) if priority is None else priority
        try:
            normalized_priority = int(requested_priority)
        except (TypeError, ValueError):
            normalized_priority = 0
        item = QueueItem(id=uuid.uuid4().hex[:10], recipe=dict(recipe), priority=normalized_priority)
        self.items.append(item)
        self._persist()
        self.log(f"[queue] enqueued {item.id} ({recipe.get('theme', '?')})")
        return item.id

    def enqueue_batch(self, recipes: list[dict]) -> list[str]:
        return [self.enqueue(recipe) for recipe in recipes]

    def set_priority(self, item_id: str, priority: int) -> bool:
        """Change a pending item's priority and persist the revised scheduling order."""
        for item in self.items:
            if item.id == item_id and item.status == "pending":
                item.priority = int(priority)
                self._persist()
                return True
        return False

    def status_summary(self) -> dict:
        c = {"pending": 0, "running": 0, "done": 0, "error": 0, "cancelled": 0, "blocked": 0}
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
                # Wake as soon as stop() sets the event; do not keep a worker
                # alive for the full idle poll interval during shutdown.
                self._stop.wait(3)
                continue
            self._process(next_item)

    def _pick_next(self) -> QueueItem | None:
        pending = [(index, item) for index, item in enumerate(self.items) if item.status == "pending"]
        if not pending:
            return None
        # Higher priority wins; list index preserves FIFO for equal priorities.
        return min(pending, key=lambda pair: (-pair[1].priority, pair[0]))[1]

    # ------------------------------------------------------- run one
    def _process(self, item: QueueItem):
        item.status = "running"
        item.started_at = time.time()
        self._persist()
        try:
            kind = str(item.recipe.get("kind") or "track")
            if kind == "rvc_train_night":
                # Обучение RVC — отдельный процесс модели, а не рендер трека.
                # Честный BLOCKED с причиной вместо общего error.
                item.status = "blocked"
                item.error = (
                    "rvc_train_night requires a training backend; "
                    "the render queue does not run RVC training"
                )
                self.log(f"[queue] {item.id} blocked: {item.error}")
                return

            runner = self._resolve_runner()
            progress: list = []

            def on_stage(*args):
                # `run_full_pipeline` отдаёт (name, status, index, total),
                # очередь ведёт только прогресс и уважает отмену.
                if item.cancel_requested or self._stop.is_set():
                    raise RuntimeError("cancelled")
                name = str(args[0]) if args else ""
                item.stage = name
                progress.append(1)
                if len(args) >= 4:
                    try:
                        item.progress = float(args[2]) / float(args[3] or 1)
                    except (TypeError, ValueError, ZeroDivisionError) as exc:
                        # Прогресс — украшение, но причина должна быть в логе,
                        # а не исчезать в пустом `except`.
                        item.stage = f"{name} (progress unknown: {type(exc).__name__})"
                self._persist()

            project_id = item.id
            res = runner(project_id, item.recipe, on_stage=on_stage)
            item.result_paths = res or {}
            item.status = "done"
            item.progress = 1.0 if progress else item.progress
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

    def _resolve_runner(self) -> Callable[..., dict]:
        """Привести исполнителя рендера к единой сигнатуре.

        Публичный API оркестратора — функция `run_full_pipeline(project_id,
        recipe, on_stage=...)`. Раньше здесь импортировался несуществующий
        класс `Orchestrator`, поэтому каждая задача падала на ImportError.
        Внедрённый объект уважается в обеих формах: `run_full_pipeline(...)`
        и легаси `run_pipeline(recipe, stage_hook)` — иначе подмена в тестах
        молча игнорируется и очередь уходит в настоящий многоминутный рендер.
        """
        injected = self.orchestrator
        if injected is not None:
            full = getattr(injected, "run_full_pipeline", None)
            if callable(full):
                return full
            legacy = getattr(injected, "run_pipeline", None)
            if callable(legacy):
                return lambda project_id, recipe, on_stage=None: legacy(recipe, on_stage)
            if callable(injected):
                return injected
        try:
            from app.core.orchestrator import run_full_pipeline
        except Exception as exc:  # noqa: BLE001 - очередь должна честно сообщить
            raise RuntimeError(f"orchestrator unavailable: {type(exc).__name__}: {exc}") from exc
        return run_full_pipeline

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
