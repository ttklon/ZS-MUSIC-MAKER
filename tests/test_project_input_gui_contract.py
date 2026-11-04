"""File-replacement controls use Qt stubs, not a Windows/Qt integration test."""
from types import ModuleType, SimpleNamespace
import sys

from test_project_edit_gui_contract import fake_qt, load  # shared Qt doubles


def test_selection_is_explicit_cancel_preserves_and_clear_requires_action(fake_qt, monkeypatch):
    widgets, box = fake_qt
    module = load('isolated_project_input_editor', 'app/gui/wizard/project_input_editor.py')
    editor = module.ProjectInputEditor()
    assert editor.selections() == {}
    refs = editor._checks['references']
    refs.setChecked(True)
    try:
        editor.selections()
        assert False, 'checked references require a choice or explicit clear'
    except ValueError:
        pass
    monkeypatch.setattr(widgets.QFileDialog, 'getOpenFileNames', lambda *a: (['/one.wav', '/two.flac'], ''))
    editor._choose('references')
    assert editor.selections() == {'references': ['/one.wav', '/two.flac']}
    monkeypatch.setattr(widgets.QFileDialog, 'getOpenFileNames', lambda *a: ([], ''))
    editor._choose('references')
    assert len(editor.selections()['references']) == 2
    editor._clear_refs()
    assert editor.selections() == {'references': []}
    refs.setChecked(False)
    assert editor.selections() == {}


def test_pairing_confirmation_is_separate_and_cancel_never_enqueues(fake_qt, monkeypatch):
    _, box = fake_qt
    module = load('isolated_input_edit_action', 'app/gui/wizard/project_edit_action.py')
    calls = []
    class EditDialog:
        Accepted = 1
        def __init__(self, recipe, screen): pass
        def exec(self): return 1
        def changes(self): return {}
        def replacements(self): return {'own_vocal_wav': '/take.wav'}
    fake = ModuleType('app.gui.wizard.project_edit_dialog')
    fake.ProjectEditDialog = EditDialog
    monkeypatch.setitem(sys.modules, fake.__name__, fake)
    job = SimpleNamespace(track_id='source', master_only=True, recipe={},
                          result={'pipeline': {'input_integrity': {'version': 1}}})
    run = SimpleNamespace(current_tid=None, batch_tids=[], track_job=lambda tid: calls.append(('track', tid)))
    orch = SimpleNamespace(enqueue_opened_rebuild=lambda *args: calls.append(args) or 'new')
    screen = SimpleNamespace(current_job=job, wizard=SimpleNamespace(steps=[run], orch=orch))
    answers = iter([box.StandardButton.No])
    monkeypatch.setattr(box, 'question', lambda *args: next(answers))
    module.start_project_edit(screen)
    assert not calls
    answers = iter([box.StandardButton.Yes, box.StandardButton.No])
    module.start_project_edit(screen)
    assert not calls
    answers = iter([box.StandardButton.Yes, box.StandardButton.Yes])
    module.start_project_edit(screen)
    assert calls == [('source', {}, {'own_vocal_wav': '/take.wav', 'ack_unverified_pairing': True}), ('track', 'new')]
