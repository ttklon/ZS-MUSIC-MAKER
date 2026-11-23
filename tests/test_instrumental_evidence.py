"""Producer trace fixtures, NOT music listening tests or real model certification."""
import numpy as np
import pytest
import soundfile as sf

from app.core.instrumental_evidence import attach_instrumental_evidence
from app.core.stages.mix_trace import fingerprint, prepare_traced_mix
from app.pipeline import StageResult, StageStatus


@pytest.fixture
def chain(tmp_path):
    signal = np.sin(np.arange(44100) * 0.02) * 0.1
    for name in ('beat', 'mix', 'master'):
        sf.write(tmp_path / f'{name}.wav', np.column_stack((signal, signal)), 44100)
    beat, mix, master = [tmp_path / f'{name}.wav' for name in ('beat', 'mix', 'master')]
    stages = [StageResult('_stage_beat', StageStatus.OK, {'ok': True, 'engine': 'beat_constructor.construct_beat',
        'sections': [{'name': 'fixture'}], 'path': str(beat)}),
        StageResult('_stage_mix_and_sidechain', StageStatus.OK, {'ok': True, 'engine': 'modules.mix.bus',
        'vocal_used': False, 'gates_passed': True, 'out_wav': str(mix), 'source_trace': {
        'schema': 1, 'beat': fingerprint(beat), 'mix': fingerprint(mix), 'vocal_requested': False}}),
        StageResult('_stage_mastering', StageStatus.OK, {'ok': True}),
        StageResult('_stage_polish', StageStatus.OK, {'ok': True})]
    report = {'master_path': str(master), 'outcome': {'succeeded': True, 'status': 'success'},
              'artifact_integrity': {'master': fingerprint(master)}}
    recipe = {'voice_mode': 'off', 'beat_engine': 'procedural', 'use_texture': False, 'export_stems': False}
    return report, recipe, stages, tmp_path


def test_live_producer_manifest_is_narrow_and_hash_bound(chain):
    report, recipe, stages, root = chain
    attach_instrumental_evidence(report, recipe, stages, root)
    assert report['render_evidence']['kind'] == 'instrumental'
    assert report['render_evidence']['checks'] == {'music_present': True}
    assert 'vocal_method' not in report['render_evidence']


@pytest.mark.parametrize('name', ['beat', 'mix', 'master'])
def test_changed_asset_removes_old_manifest(chain, name):
    report, recipe, stages, root = chain
    attach_instrumental_evidence(report, recipe, stages, root)
    (root / f'{name}.wav').write_bytes(b'changed asset')
    attach_instrumental_evidence(report, recipe, stages, root)
    assert 'render_evidence' not in report
    assert report.get('content_evidence_unavailable')


@pytest.mark.parametrize('mutation', ['no_trace', 'null_hash', 'vocal', 'fallback', 'failed', 'duplicate', 'outside'])
def test_incomplete_or_contradictory_trace_is_not_content_evidence(chain, mutation, tmp_path):
    report, recipe, stages, root = chain
    mix = stages[1].output
    if mutation == 'no_trace': mix.pop('source_trace')
    if mutation == 'null_hash': mix['source_trace']['beat']['sha256'] = None
    if mutation == 'vocal': mix['vocal_used'] = True
    if mutation == 'fallback': stages[0].output['fallback_used'] = True
    if mutation == 'failed': stages[0].status = StageStatus.FAILED
    if mutation == 'duplicate': stages.append(stages[0])
    if mutation == 'outside': stages[0].output['path'] = str(root.parent / 'outside.wav')
    attach_instrumental_evidence(report, recipe, stages, root)
    assert 'render_evidence' not in report


def test_input_change_during_real_mixer_call_is_rejected(tmp_path, monkeypatch):
    beat = tmp_path / 'beat.wav'
    beat.write_bytes(b'original')
    def fake_mix(*args, **kwargs):
        beat.write_bytes(b'replaced')
        return {'ok': True, 'out_wav': str(beat)}
    monkeypatch.setattr('modules.mix.bus.prepare_mix', fake_mix)
    with pytest.raises(ValueError, match='changed during mixing'):
        prepare_traced_mix(str(beat), None, tmp_path)
