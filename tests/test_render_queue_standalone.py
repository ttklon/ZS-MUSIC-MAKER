"""T7: ночная очередь рендера работает автономно и не врёт о результате.

До доработки `RenderQueue._process` импортировал `Orchestrator` и `probe_hw`,
которых нет (`app.core.orchestrator` экспортирует `run_full_pipeline`,
`app.hw_probe` — `probe`). Любая задача очереди падала на `ImportError`,
а `schedule_night_run` вызывал `render_queue.enqueue`, хотя публичный API —
`RenderQueue().enqueue`.
"""

from __future__ import annotations

import json

import pytest

from modules import render_queue as rq
from modules import rvc_trainer


@pytest.fixture
def isolated_state(monkeypatch, tmp_path):
    """Очередь не должна трогать реальный файл состояния пользователя."""
    state = tmp_path / "queue_state.json"
    monkeypatch.setattr(rq, "STATE_FILE", state)
    monkeypatch.setattr(rq, "_load_state", lambda: [])
    return state


def _run_one(queue: rq.RenderQueue) -> rq.QueueItem:
    item = queue.items[0]
    queue._process(item)
    return item


def test_queue_renders_with_orchestrator_function(isolated_state, monkeypatch) -> None:
    """Оркестратор — это функция `run_full_pipeline`, а не класс."""
    calls: list[dict] = []

    def fake_run(project_id, recipe, **kwargs):
        calls.append({"project_id": project_id, "recipe": recipe, "kwargs": kwargs})
        return {"verdict": "PASS", "master_path": "/tmp/master.wav"}

    monkeypatch.setattr("app.core.orchestrator.run_full_pipeline", fake_run, raising=True)

    queue = rq.RenderQueue(log=lambda *_: None)
    queue.enqueue({"theme": "night drive", "genre": "drift_phonk"})
    item = _run_one(queue)

    assert item.status == "done", item.error
    assert calls and calls[0]["recipe"]["theme"] == "night drive"
    assert item.result_paths["verdict"] == "PASS"


def test_progress_hook_is_reported(isolated_state, monkeypatch) -> None:
    seen: list[tuple] = []

    def fake_run(project_id, recipe, **kwargs):
        hook = kwargs.get("on_stage") or kwargs.get("stage_hook")
        assert callable(hook), f"стадии не сообщают прогресс: {sorted(kwargs)}"
        hook("_stage_beat", 0.5)
        return {"verdict": "PASS"}

    monkeypatch.setattr("app.core.orchestrator.run_full_pipeline", fake_run)

    queue = rq.RenderQueue(log=seen.append)
    queue.enqueue({"theme": "x"})
    item = _run_one(queue)

    assert item.status == "done"
    assert item.stage == "_stage_beat"


def test_missing_orchestrator_is_an_error_not_a_crash(isolated_state, monkeypatch) -> None:
    """Отсутствие оркестратора — состояние задачи, а не падение процесса."""
    import app.core.orchestrator as orchestrator

    monkeypatch.delattr(orchestrator, "run_full_pipeline", raising=True)

    queue = rq.RenderQueue(log=lambda *_: None)
    queue.enqueue({"theme": "x"})
    item = _run_one(queue)

    assert item.status == "error"
    assert "run_full_pipeline" in item.error or "orchestrator" in item.error.lower()


def test_rvc_night_payload_is_blocked_with_reason(isolated_state, monkeypatch) -> None:
    """Обучение RVC нельзя «выполнить» очередью — это честный BLOCKED."""
    def forbidden(*args, **kwargs):
        pytest.fail("очередь не должна запускать рендер для rvc_train_night")

    monkeypatch.setattr("app.core.orchestrator.run_full_pipeline", forbidden)

    queue = rq.RenderQueue(log=lambda *_: None)
    queue.enqueue({"kind": "rvc_train_night", "manifest_path": "/tmp/manifest.json"})
    item = _run_one(queue)

    assert item.status == "blocked"
    assert "night" in item.error.lower() or "training" in item.error.lower()


def test_queue_state_survives_a_restart(isolated_state, monkeypatch) -> None:
    def load() -> list[dict]:
        if not isolated_state.exists():
            return []
        return json.loads(isolated_state.read_text(encoding="utf-8"))

    monkeypatch.setattr(rq, "_load_state", load)

    queue = rq.RenderQueue(log=lambda *_: None)
    queue.enqueue({"theme": "persisted"})

    restored = rq.RenderQueue(log=lambda *_: None)

    assert [item.recipe["theme"] for item in restored.items] == ["persisted"]


# ------------------------------------------------------------------ trainer
def test_schedule_night_run_uses_queue_api(monkeypatch) -> None:
    seen: dict = {}

    class FakeQueue:
        def enqueue(self, payload, priority=None):
            seen["payload"] = payload
            return "queue-id-1"

    monkeypatch.setattr(rq, "RenderQueue", lambda *a, **k: FakeQueue())

    result = rvc_trainer.schedule_night_run("/tmp/voice_manifest.json")

    assert result["ok"] is True
    assert result["queue_id"] == "queue-id-1"
    assert seen["payload"]["kind"] == "rvc_train_night"


def test_schedule_night_run_reports_fallback_reason(monkeypatch) -> None:
    """Фолбэк допустим, но причина обязана быть видна."""
    def broken(*args, **kwargs):
        raise RuntimeError("queue unavailable")

    monkeypatch.setattr(rq, "RenderQueue", broken)
    monkeypatch.setattr(
        rvc_trainer,
        "retrain_incremental",
        lambda *a, **k: {"id": "job-1", "plan": {"epochs": 320}},
    )

    result = rvc_trainer.schedule_night_run("/tmp/voice_manifest.json")

    assert result["ok"] is True
    assert result["fallback"] is True
    assert "queue unavailable" in result["reason"]
