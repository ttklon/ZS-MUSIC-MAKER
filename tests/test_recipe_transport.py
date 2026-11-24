"""Real recipe/factory boundaries with the expensive audio executor replaced explicitly."""
from __future__ import annotations

import copy
import json

import pytest

from app.core.project_snapshot import restore_recipe, snapshot_recipe
from app.core.recipe import build_recipe, resolve_style_vector
from modules.agent_guide import runner
from modules.hit_factory.generator import HitFactory


def recipe():
    return dict(genre='trap', theme='Ночь', artist='Автор', duration_sec=37, seed=123,
                bpm_override=143, references=['ref.wav'], reference_lyrics='Первая\nВторая',
                user_lyrics_lines=['Первая', 'Вторая'], own_vocal_wav='take.wav', use_rvc=False,
                voice_mode='pro', n_verses=3, bilingual=False, trend_notes='ночь',
                style_vector={'target_mode': 'major', 'prompt_hint': 'soft'})


def test_agent_forwards_exact_recipe_without_evolution(monkeypatch, tmp_path):
    seen = {}
    monkeypatch.setattr(HitFactory, '__init__', lambda self, **kw: None)
    def make(self, **kw):
        seen.update(kw)
        return {'master_path': None}
    monkeypatch.setattr(HitFactory, 'make_one', make)
    state = recipe()
    runner._run_pipeline(state, str(tmp_path), None)
    assert seen == {'recipe': state, 'evolve': False}


def test_factory_to_normalized_recipe_and_snapshot_roundtrip(monkeypatch, tmp_path):
    import modules.hit_factory.generator as generator
    state = recipe()
    original = copy.deepcopy(state)
    seen = []
    def execute(self, project_id, wizard_state, rng):
        seen.append(copy.deepcopy(wizard_state))
        return dict(project_id=project_id, hit_score=0, verdict='PARTIAL',
                    master_path=None, out_root=str(tmp_path))
    monkeypatch.setattr(HitFactory, '_run_pipeline_once', execute)
    monkeypatch.setattr(generator, '_save_factory_summary', lambda *a: None)
    factory = HitFactory(output_root=str(tmp_path), adaptive=False, evolve=False)
    output = factory.make_one(recipe=state)
    assert len(seen) == 1
    for key, value in state.items():
        assert seen[0][key] == value, key
    normalized = build_recipe(seen[0])
    assert normalized['refs'] == state['references']
    for key in ('theme', 'seed', 'bpm_override', 'duration_sec', 'own_vocal_wav',
                'reference_lyrics', 'user_lyrics_lines', 'use_rvc', 'voice_mode', 'style_vector'):
        assert normalized[key] == state[key]
    style = resolve_style_vector(normalized, {})
    assert style['target_bpm'] == 143 and style['target_mode'] == 'major'
    restored = restore_recipe({'desktop_recipe_snapshot': snapshot_recipe(seen[0])})
    assert restored == seen[0] == output['wizard_state']
    assert state == original


@pytest.mark.parametrize('bad', [{'unknown_input': True}, {'seed': float('nan')}])
def test_bad_recipe_rejected_before_executor(tmp_path, bad):
    factory = HitFactory(output_root=str(tmp_path), adaptive=False, evolve=False)
    with pytest.raises(ValueError):
        factory.make_one(recipe=bad)


def test_conflicting_legacy_overrides_are_not_silently_ignored(tmp_path):
    factory = HitFactory(output_root=str(tmp_path), adaptive=False, evolve=False)
    with pytest.raises(ValueError, match='mixed'):
        factory.make_one(recipe=recipe(), seed=999)


def test_ndjson_escapes_multiline_text_and_has_single_terminal(capsys):
    from app.cli.task_events import TaskEvents
    events = TaskEvents('test-id')
    events.progress('Текст\nс переносом и {"master_path":"не результат"}')
    events.emit('done', ok=False, report={'blocked': ['voice']})
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 2
    decoded = [json.loads(line) for line in lines]
    assert decoded[0]['message'].startswith('Текст\n')
    assert [e['seq'] for e in decoded] == [1, 2]
    assert all(e['task_id'] == 'test-id' for e in decoded)
    with pytest.raises(ValueError):
        events.progress('too late')


@pytest.mark.parametrize('field,value', [('seed', True), ('seed', '7'), ('duration_sec', -1),
                                        ('references', 'one.wav'), ('use_rvc', 'false'),
                                        ('style_vector', []), ('bpm_override', 900)])
def test_explicit_recipe_rejects_ambiguous_types(tmp_path, field, value):
    state = recipe()
    state[field] = value
    factory = HitFactory(output_root=str(tmp_path), adaptive=False, evolve=False)
    with pytest.raises(ValueError):
        factory.make_one(recipe=state)


def test_cli_produces_terminal_after_progress_and_marks_partial(monkeypatch, capsys):
    from types import SimpleNamespace
    from app.cli import agent_task
    import modules.agent_guide as guide
    monkeypatch.setenv('ZSMM_TASK_ID', 'cli-fixture')
    monkeypatch.setattr(agent_task, '_prepare', lambda online: {})
    monkeypatch.setattr(guide, 'run_conversation_hit', lambda *a, **kw: {'master_path': None})
    monkeypatch.setattr(guide, 'narrate', lambda report: 'plain trailing noise')
    code = agent_task.run_agent_hit(SimpleNamespace(online=False))
    records = []
    for line in capsys.readouterr().out.splitlines():
        try:
            records.append(json.loads(line))
        except ValueError:
            pass
    assert code == 1
    assert records[0]['type'] == 'progress'
    assert records[-1]['type'] == 'done' and records[-1]['ok'] is False
    assert all(r['task_id'] == 'cli-fixture' for r in records)


def test_cli_exception_has_error_and_terminal(monkeypatch, capsys):
    from types import SimpleNamespace
    from app.cli import agent_task
    import modules.agent_guide as guide
    monkeypatch.setattr(agent_task, '_prepare', lambda online: {})
    def fail(*a, **kw):
        raise RuntimeError('fixture failure\nmultiline')
    monkeypatch.setattr(guide, 'run_conversation_hit', fail)
    assert agent_task.run_agent_hit(SimpleNamespace(online=False)) == 2
    records = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert [r['type'] for r in records] == ['progress', 'progress', 'error', 'done']
    assert 'неполная' in records[1]['message']
    assert records[-1]['ok'] is False


def test_supplied_lyrics_reach_actual_lyrics_stage_unchanged():
    from app.core.stages.lyrics import _run_lyrics_stage
    state = recipe()
    stage, structure, text = _run_lyrics_stage(build_recipe(state))
    assert stage.ok
    assert text == '\n'.join(state['user_lyrics_lines'])
    assert stage.output['provider'] == 'user_lyrics'
    assert structure


def test_prepared_rvc_take_is_not_converted_twice(monkeypatch, tmp_path):
    from modules.hit_factory import breakthrough
    monkeypatch.setattr(breakthrough, 'prepare_voice', lambda *a, **kw: {
        'ok': True, 'source': 'rvc', 'path': 'converted.wav'})
    state = recipe()
    state['use_rvc'] = True
    runner._voice(state, tmp_path)
    assert state['own_vocal_wav'] == 'converted.wav'
    assert state['use_rvc'] is False
