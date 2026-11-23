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


def test_empty_caller_context_receives_successful_changes():
    def change(h, ctx):
        ctx['committed'] = True
        return 'ok'
    context = {}
    runner = SequentialAIRunner(vram_probe=lambda: 0)
    runner.add(AIStage('change', None, change, timeout_sec=20))
    assert runner.run(context).stages[0].ok
    assert context['committed'] is True
    assert context['sink']['change'] == 'ok'


def test_registry_import_does_not_create_model_dirs_in_install_or_workspace(tmp_path):
    import json
    import subprocess
    import sys
    root = Path(__file__).resolve().parents[1]
    workspace = tmp_path / 'workspace'
    env = dict(os.environ, ZSMM_WORKSPACE=str(workspace))
    code = ('import json; from app.ai.registry import MODELS_DIR; '
            'print(json.dumps({"directory":str(MODELS_DIR),"exists":MODELS_DIR.exists()}))')
    result = subprocess.run([sys.executable, '-B', '-c', code], cwd=root, env=env,
                            text=True, capture_output=True, timeout=30, check=True)
    data = json.loads(result.stdout)
    assert Path(data['directory']) == workspace / 'data' / 'ai_models'
    assert not data['exists']
    assert not workspace.exists()


def test_real_dossier_local_closures_survive_process_boundary(tmp_path, monkeypatch):
    import json
    from modules.artist_dossier.manager import DossierManager
    monkeypatch.setenv('ZSMM_ONLINE', '0')
    monkeypatch.setenv('ZSMM_ALLOW_MODEL_DOWNLOAD', '0')
    manager = DossierManager(tmp_path / 'dossiers')
    track = manager.add_track('Worker Test Artist', 'Closure Song', lyrics='User supplied test lyrics')
    manager.build_full_dossier('Worker Test Artist')
    files = list((tmp_path / 'dossiers').glob(f'*/tracks/{track.track_id}.json'))
    assert len(files) == 1
    stored = json.loads(files[0].read_text(encoding='utf-8'))
    assert stored['lyrics'] == 'User supplied test lyrics'
    assert stored['status'] == 'partial'  # no analysis model installed in test runtime
    stages = stored['dossier']['report']['stages']
    assert len(stages) == 5
    assert all(s['ok'] for s in stages), stages
    assert all(not s['error'] for s in stages)


def test_ai_report_has_canonical_outcome_for_failed_payload():
    runner = SequentialAIRunner(vram_probe=lambda: 0)
    runner.add(AIStage('voice', None, lambda h, c: {'ok': False, 'reason': 'no voice'}, timeout_sec=20))
    report = runner.run().to_dict()
    assert report['outcome']['status'] == 'failed'
    assert not report['outcome']['succeeded']
