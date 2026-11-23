"""Probe safety contracts; WAV fixtures do not certify a hardware profile."""
import json
import numpy as np
import pytest
import soundfile as sf

from tools.pipeline_hardware_probe import scenario, evaluate, inspect_master, probe


def test_scenario_is_explicit_cpu_instrumental():
    assert scenario(20)['voice_mode'] == 'off'
    assert scenario(120)['beat_engine'] == 'procedural'
    for bad in (True, 20.0, '20', 0, -1, 600):
        with pytest.raises(ValueError):
            scenario(bad)


def test_master_file_does_not_promote_blocked_pipeline(tmp_path):
    target = tmp_path / 'master.wav'
    audio = np.sin(np.arange(44100) * 0.02) * 0.2
    sf.write(target, np.column_stack((audio, audio)), 44100)
    report = {'master_path': str(target), 'outcome': {'succeeded': False, 'status': 'blocked'}}
    assert inspect_master(report, 1)['sha256']
    with pytest.raises(ValueError, match='did not succeed'):
        evaluate(report, 1)
    report['outcome'] = {'succeeded': True}
    assert evaluate(report, 1)['seconds'] == 1
    for key, value in [('dry_run', True), ('only', ['master'])]:
        with pytest.raises(ValueError, match='Partial/dry'):
            evaluate(dict(report, **{key: value}), 1)
    with pytest.raises(ValueError, match='duration'):
        evaluate(report, 20)


def test_probe_refuses_to_reuse_existing_directory(tmp_path):
    previous = tmp_path / 'probe_report.json'
    previous.write_text(json.dumps({'previous': True}))
    with pytest.raises(FileExistsError):
        probe(20, tmp_path)
    assert json.loads(previous.read_text()) == {'previous': True}
