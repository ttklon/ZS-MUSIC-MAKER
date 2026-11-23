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
