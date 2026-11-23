"""Caller scope contracts; no audio/model inference in this suite."""
from app.core.recipe import build_recipe
from app.core.stage_request import disabled_stages, attach_request_outcome
from app.core.pipeline_runtime import STAGE_RECORDS, _run_texture_stage
from app.pipeline import StageResult, StageStatus


def test_explicit_texture_off_is_not_inferred_from_truthy_strings(tmp_path):
    assert build_recipe({'use_texture': False})['use_texture'] is False
    for value in (None, '', 'false', 0):
        assert build_recipe({'use_texture': value})['use_texture'] is True
    recipe = build_recipe({'voice_mode': 'off', 'export_stems': False, 'use_texture': False})
    disabled = disabled_stages(recipe)
    assert disabled == {'_stage_texture', '_stage_voice_synth', '_stage_rvc', '_stage_vocal_fx', '_stage_stems'}
    stage = _run_texture_stage(recipe, tmp_path, {}, None)
    assert stage.status == StageStatus.BLOCKED
    assert stage.output['requested'] is False


def test_caller_scope_never_suppresses_executed_failure_or_missing_master():
    recipe = build_recipe({'voice_mode': 'off', 'export_stems': False, 'use_texture': False})
    disabled = disabled_stages(recipe)
    stages = [StageResult(name, StageStatus.BLOCKED if name in disabled else StageStatus.OK)
              for name in STAGE_RECORDS]
    report = {}
    attach_request_outcome(report, recipe, stages, [], False, None)
    assert report['outcome']['succeeded'] is True
    assert all(s['status'] == 'not_requested' for s in report['outcome']['stages'] if s['name'] in disabled)
    texture = next(s for s in stages if s.name == '_stage_texture')
    texture.status = StageStatus.FAILED
    attach_request_outcome(report, recipe, stages, [], False, None)
    assert report['outcome']['status'] == 'failed'
    texture.status = StageStatus.BLOCKED
    attach_request_outcome(report, recipe, [s for s in stages if s.name != '_stage_mastering'], [], False, None)
    assert report['outcome']['status'] == 'blocked'


def test_local_service_discovery_can_be_disabled_without_sockets(monkeypatch):
    from modules.hit_factory import adaptive
    monkeypatch.setenv('ZSMM_PROBE_LOCAL_SERVICES', '0')
    monkeypatch.setattr(adaptive.socket, 'socket', lambda *a: (_ for _ in ()).throw(AssertionError('must not probe')))
    assert adaptive._local_ace_available() is False


def test_adapter_uses_original_caller_request_not_forged_report_scope():
    from app.core.stage_request import classic_outcome
    disabled = disabled_stages(build_recipe({'voice_mode': 'off', 'export_stems': False, 'use_texture': False}))
    report = {'stages': [{'name': n, 'status': 'BLOCKED' if n in disabled else 'OK'} for n in STAGE_RECORDS],
              'request_scope': {'not_requested': list(STAGE_RECORDS)},
              'recipe': {'voice_mode': 'off', 'export_stems': False, 'use_texture': False},
              'outcome': {'status': 'success', 'succeeded': True}}
    state = {'voice_mode': 'off', 'export_stems': False, 'use_texture': False}
    assert classic_outcome(report, state)['succeeded'] is True
    assert classic_outcome(report, {})['status'] == 'blocked'
    report['stages'] = [s for s in report['stages'] if s['name'] != '_stage_mastering']
    assert classic_outcome(report, state)['status'] == 'blocked'


def test_scoped_typed_boundary_still_requires_content_evidence(tmp_path):
    import numpy as np
    import soundfile as sf
    from app.core.stage_request import classic_result
    target = tmp_path / 'fixture.wav'
    signal = np.sin(np.arange(44100) * 0.02) * 0.1
    sf.write(target, np.column_stack((signal, signal)), 44100)
    state = {'voice_mode': 'off', 'export_stems': False, 'use_texture': False}
    disabled = disabled_stages(build_recipe(state))
    report = {'master_path': str(target),
              'stages': [{'name': n, 'status': 'BLOCKED' if n in disabled else 'OK'} for n in STAGE_RECORDS],
              'outcome': {'status': 'success', 'succeeded': True}}
    result = classic_result(report, state, requested_kind='instrumental')
    assert result['status'] == 'degraded' and result['succeeded'] is False
    assert 'состава аудио' in ' '.join(result['reasons'])
    for name in ('_stage_mix_and_sidechain', '_stage_mastering'):
        row = next(s for s in report['stages'] if s['name'] == name)
        row['status'] = 'FAILED'
        assert classic_result(report, state, requested_kind='instrumental')['status'] == 'failed'
        row['status'] = 'OK'
