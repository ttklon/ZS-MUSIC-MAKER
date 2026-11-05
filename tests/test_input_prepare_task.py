"""Background hashing is read-only, cancellable and cannot itself enqueue a job."""
import hashlib
import threading
import time
from pathlib import Path

import pytest

from app.core import input_integrity
from app.core.input_prepare_task import InputPreparationTask
from app.core.project_inputs import InputPreparationCancelled, prepare_replacements
from app.runtime_orchestrator import Job, RuntimeOrchestrator


def test_task_reads_in_background_and_cancellation_stops_before_job(tmp_path, monkeypatch):
    source = tmp_path/'voice.wav'
    source.write_bytes(b'content' * 1000)
    initial = source.read_bytes()
    entered = threading.Event()
    real = input_integrity._sha256
    def slow(path, checkpoint=None):
        entered.set()
        while True:
            time.sleep(.005)
            checkpoint()
    monkeypatch.setattr(input_integrity, '_sha256', slow)
    task = InputPreparationTask({'own_vocal_wav': str(source), 'ack_unverified_pairing': True})
    task.start()
    assert entered.wait(2)
    with pytest.raises(ValueError, match='unfinished'):
        task.take_result()
    task.cancel()
    assert task.done.wait(2) and task.was_cancelled and task.error is None
    with pytest.raises(ValueError, match='cancelled'):
        task.take_result()
    assert source.read_bytes() == initial
    assert sorted(p.name for p in tmp_path.iterdir()) == ['voice.wav']
    monkeypatch.setattr(input_integrity, '_sha256', real)


def test_hash_checkpoint_is_called_between_chunks_and_can_abort(tmp_path):
    file = tmp_path/'large.wav'
    file.write_bytes(b'a' * (2 * 1024 * 1024 + 1))
    checks = []
    def cancel():
        checks.append(1)
        return len(checks) >= 4
    with pytest.raises(InputPreparationCancelled):
        prepare_replacements({'references': [str(file)]}, cancelled=cancel)
    assert len(checks) >= 4 and file.stat().st_size == 2 * 1024 * 1024 + 1


def test_prepared_job_uses_frozen_hash_and_is_single_use(tmp_path, monkeypatch):
    import app.runtime_orchestrator as module
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    source = tmp_path/'source'; source.mkdir()
    path = tmp_path/'ref.wav'; path.write_bytes(b'reference')
    raw = {'references': [str(path)]}
    task = InputPreparationTask(raw)
    raw['references'].clear()
    task.start(); assert task.done.wait(2) and task.error is None
    runtime = RuntimeOrchestrator(); runtime.stop()
    monkeypatch.setattr(runtime, '_ensure_worker', lambda: None)
    runtime.jobs['open'] = Job(track_id='open', recipe={}, status='done', master_only=True,
                               project_dir=str(source), result={'pipeline': {'input_integrity': {}}})
    tid = runtime.enqueue_prepared_opened_rebuild('open', {'theme': 'test'}, task)
    selected = runtime.jobs[tid].rebuild_replacements['references'][0]
    assert selected['path'] == str(path)
    assert selected['sha256'] == hashlib.sha256(b'reference').hexdigest()
    assert runtime._queue == [tid]
    with pytest.raises(ValueError, match='already consumed'):
        runtime.enqueue_prepared_opened_rebuild('open', {}, task)
    with pytest.raises(ValueError, match='completed input preparation'):
        runtime.enqueue_prepared_opened_rebuild('open', {}, {'references': ['/other.wav']})
    assert runtime._queue == [tid]


def test_error_and_cancelled_tasks_cannot_enqueue(tmp_path, monkeypatch):
    import app.runtime_orchestrator as module
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    source = tmp_path/'source'; source.mkdir()
    runtime = RuntimeOrchestrator(); runtime.stop()
    monkeypatch.setattr(runtime, '_ensure_worker', lambda: None)
    runtime.jobs['open'] = Job(track_id='open', recipe={}, status='done', master_only=True,
                               project_dir=str(source), result={'pipeline': {'input_integrity': {}}})
    task = InputPreparationTask({'references': [str(tmp_path/'missing.wav')]})
    task.start(); assert task.done.wait(2) and task.error
    with pytest.raises(ValueError, match='failed'):
        runtime.enqueue_prepared_opened_rebuild('open', {}, task)
    cancelled = InputPreparationTask({'references': []}); cancelled.cancel(); cancelled.start()
    assert cancelled.done.wait(2) and cancelled.was_cancelled
    with pytest.raises(ValueError, match='cancelled'):
        runtime.enqueue_prepared_opened_rebuild('open', {}, cancelled)
    assert runtime._queue == [] and not (tmp_path/'output').exists()


def test_qt_core_event_loop_keeps_ticking_during_slow_hash(tmp_path, monkeypatch):
    """Real QtCore event loop, not QtWidgets or Windows."""
    core = pytest.importorskip('PySide6.QtCore')
    path = tmp_path/'input.wav'; path.write_bytes(b'abc')
    release, entered = threading.Event(), threading.Event()
    real = input_integrity._sha256
    def slow(path, checkpoint=None):
        entered.set()
        while not release.wait(.005):
            checkpoint()
        return real(path, checkpoint=checkpoint)
    monkeypatch.setattr(input_integrity, '_sha256', slow)
    app = core.QCoreApplication.instance() or core.QCoreApplication([])
    task = InputPreparationTask({'references': [str(path)]})
    task.start(); assert entered.wait(2)
    loop = core.QEventLoop()
    ticks = []
    timer = core.QTimer(); timer.setInterval(5)
    def tick():
        ticks.append(1)
        if len(ticks) == 5: release.set()
        if task.done.is_set(): loop.quit()
    timer.timeout.connect(tick); timer.start()
    core.QTimer.singleShot(3000, loop.quit)
    loop.exec(); timer.stop()
    assert len(ticks) >= 5 and task.done.wait(1) and task.error is None
    assert task.take_result()['references'][0]['sha256'] == hashlib.sha256(b'abc').hexdigest()
    assert app is not None
