"""Real subprocess isolation contracts, also run on Windows CI."""
import os
from pathlib import Path
import time

from app.ai.sequential_runner import AIStage, SequentialAIRunner


def test_closure_context_sink_and_pid_cross_boundary(tmp_path):
    captured = 'closure works'
    def first(handle, ctx):
        ctx['mutated'] = captured
        return {'pid': os.getpid(), 'value': captured}
    def second(handle, ctx):
        return ctx['sink']['first']['pid'], ctx['mutated']
    context = {'sentinel': True}
    runner = SequentialAIRunner(vram_probe=lambda: 0)
    runner.add(AIStage('first', None, first, timeout_sec=20))
    runner.add(AIStage('second', None, second, timeout_sec=20))
    report = runner.run(context)
    assert all(s.ok for s in report.stages), report.to_dict()
    assert runner.sink()['first']['pid'] != os.getpid()
    assert runner.sink()['second'] == (runner.sink()['first']['pid'], captured)
    assert context['mutated'] == captured


def test_timeout_cannot_write_later_and_next_stage_runs(tmp_path):
    marker = tmp_path / 'late.txt'
    def stuck(handle, ctx):
        time.sleep(5)
        marker.write_text('escaped')
    runner = SequentialAIRunner(vram_probe=lambda: 0)
    runner.add(AIStage('hung', None, stuck, timeout_sec=.2))
    runner.add(AIStage('next', None, lambda h, c: 7, timeout_sec=20))
    report = runner.run()
    assert not report.stages[0].ok
    assert 'including model loading' in report.stages[0].error
    assert report.stages[1].ok
    assert runner.sink()['next'] == 7
    time.sleep(5.1)
    assert not marker.exists()


def test_worker_failure_is_reported_without_context_commit():
    def broken(h, ctx):
        ctx['bad'] = True
        raise ValueError('deliberate')
    context = {'original': True}
    runner = SequentialAIRunner(vram_probe=lambda: 0)
    runner.add(AIStage('bad', None, broken, timeout_sec=20))
    report = runner.run(context)
    assert not report.stages[0].ok
    assert 'deliberate' in report.stages[0].error
    assert 'bad' not in context
