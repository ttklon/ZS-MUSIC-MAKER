from __future__ import annotations

import threading
from pathlib import Path

import modules.render_queue as queue_module
from modules.render_queue import RenderQueue


class FakeOrchestrator:
    def __init__(self, order: list[str], started: threading.Event | None = None):
        self.order = order
        self.started = started

    def run_pipeline(self, recipe, stage_hook):
        self.order.append(recipe["theme"])
        if self.started:
            self.started.set()
        stage_hook("lyrics", 0.5)
        stage_hook("master", 1.0)
        return {"master": f"{recipe['theme']}.wav"}


def test_render_queue_processes_fifo_and_persists(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(queue_module, "QUEUE_DIR", tmp_path)
    monkeypatch.setattr(queue_module, "STATE_FILE", tmp_path / "queue_state.json")
    order: list[str] = []
    queue = RenderQueue(orchestrator=FakeOrchestrator(order), log=lambda _message: None)
    first, second = queue.enqueue_batch([{"theme": "first"}, {"theme": "second"}])

    queue._process(queue.items[0])
    queue._process(queue.items[1])

    assert order == ["first", "second"]
    assert [item.status for item in queue.items] == ["done", "done"]
    restored = RenderQueue(orchestrator=FakeOrchestrator([]), log=lambda _message: None)
    assert [item["id"] for item in restored.list_items()] == [first, second]
    assert restored.status_summary()["done"] == 2


def test_render_queue_cancels_pending_and_running_at_stage_boundary(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(queue_module, "QUEUE_DIR", tmp_path)
    monkeypatch.setattr(queue_module, "STATE_FILE", tmp_path / "queue_state.json")
    queue = RenderQueue(orchestrator=FakeOrchestrator([]), log=lambda _message: None)
    pending = queue.enqueue({"theme": "pending"})
    assert queue.cancel(pending) is True
    assert queue.items[0].status == "cancelled"

    class CancellingOrchestrator:
        def __init__(self, owner):
            self.owner = owner

        def run_pipeline(self, recipe, stage_hook):
            assert self.owner.cancel(self.owner.items[1].id) is True
            stage_hook("music", 0.4)
            return {}

    running_id = queue.enqueue({"theme": "running"})
    queue.orchestrator = CancellingOrchestrator(queue)
    queue._process(queue.items[1])

    assert queue.items[1].id == running_id
    assert queue.items[1].status == "cancelled"
    assert queue.status_summary()["cancelled"] == 2


def test_render_queue_priorities_cancel_and_restart_recovery(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(queue_module, "QUEUE_DIR", tmp_path)
    monkeypatch.setattr(queue_module, "STATE_FILE", tmp_path / "queue.json")
    monkeypatch.setattr(queue_module, "LEGACY_STATE_FILE", tmp_path / "queue_state.json")
    queue = RenderQueue(orchestrator=FakeOrchestrator([]), log=lambda _message: None)
    first = queue.enqueue({"theme": "first"}, priority=0)
    middle = queue.enqueue({"theme": "middle"}, priority=5)
    third = queue.enqueue({"theme": "third"}, priority=0)

    assert queue.cancel(middle) is True
    assert queue.set_priority(third, 9) is True
    assert queue._pick_next().id == third
    assert queue_module.STATE_FILE.name == "queue.json"

    # A restarted worker resumes active work as pending but never resurrects cancellation.
    queue.items[0].status = "running"
    queue.items[0].stage = "music"
    queue.items[0].progress = 0.4
    queue._persist()
    restored = RenderQueue(orchestrator=FakeOrchestrator([]), log=lambda _message: None)
    restored_by_id = {item.id: item for item in restored.items}

    assert restored_by_id[first].status == "pending"
    assert restored_by_id[first].progress == 0.0
    assert restored_by_id[middle].status == "cancelled"
    assert restored._pick_next().id == third
