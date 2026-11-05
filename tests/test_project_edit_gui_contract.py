"""Project edit UI contract with Qt stubs; not a Qt or Windows device test."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType, SimpleNamespace
import sys

import pytest


@pytest.fixture
def fake_qt(monkeypatch):
    widgets = ModuleType('PySide6.QtWidgets')
    class Signal:
        def __init__(self): self.callbacks = []
        def connect(self, fn): self.callbacks.append(fn)
        def emit(self, *args):
            for callback in self.callbacks: callback(*args)
    class Widget:
        def __init__(self, *args): self.enabled = True
        def setEnabled(self, value): self.enabled = value
        def setWordWrap(self, value): pass
        def setMinimumHeight(self, value): pass
        def setText(self, value): self.value = value
    class Button(Widget):
        def __init__(self, *args):
            super().__init__(*args); self.clicked = Signal()
    class FileDialog:
        @staticmethod
        def getOpenFileName(*args): return ('', '')
        @staticmethod
        def getOpenFileNames(*args): return ([], '')
    class Dialog(Widget):
        def setWindowTitle(self, value): pass
        def resize(self, *args): pass
        def accept(self): self.accepted = True
        def reject(self): self.rejected = True
        def closeEvent(self, event): self.rejected = True
    class Progress(Widget):
        def setRange(self, low, high): self.range = (low, high)
    class Timer:
        def __init__(self, *args): self.timeout = Signal(); self.running = False
        def start(self, interval): self.running = True
        def stop(self): self.running = False
    class Check(Widget):
        def __init__(self, *args):
            super().__init__(); self.checked = False; self.toggled = Signal()
        def setChecked(self, value):
            self.checked = value; self.toggled.emit(value)
        def isChecked(self): return self.checked
    class Line(Widget):
        def setText(self, value): self.value = value
        def text(self): return self.value
    class Text(Widget):
        def setPlainText(self, value): self.value = value
        def toPlainText(self): return self.value
    class Spin(Widget):
        def setRange(self, low, high): pass
        def setValue(self, value): self.val = value
        def value(self): return self.val
    class Layout:
        def __init__(self, *args): pass
        def addWidget(self, *args): pass
        def addLayout(self, *args): pass
        def addStretch(self): pass
    class Scroll(Widget):
        def setWidgetResizable(self, value): pass
        def setWidget(self, value): pass
    class Buttons(Widget):
        class StandardButton:
            Ok = 1
            Cancel = 2
        def __init__(self, *args):
            super().__init__(); self.accepted = Signal(); self.rejected = Signal()
    class MessageBox:
        warnings, notices = [], []
        class StandardButton:
            Yes = 1
            No = 0
        answer = 1
        @classmethod
        def warning(cls, *args): cls.warnings.append(args)
        @classmethod
        def information(cls, *args): cls.notices.append(args)
        @classmethod
        def question(cls, *args): return cls.answer
    for name, cls in {'QCheckBox': Check, 'QDialog': Dialog, 'QDialogButtonBox': Buttons,
                      'QFileDialog': FileDialog, 'QHBoxLayout': Layout, 'QPushButton': Button, 'QProgressBar': Progress,
                      'QLabel': Widget, 'QLineEdit': Line, 'QMessageBox': MessageBox,
                      'QScrollArea': Scroll, 'QSpinBox': Spin, 'QTextEdit': Text,
                      'QVBoxLayout': Layout, 'QWidget': Widget}.items():
        setattr(widgets, name, cls)
    monkeypatch.delitem(sys.modules, 'app.gui.wizard.project_input_editor', raising=False)
    wizard = ModuleType('app.gui.wizard')
    wizard.__path__ = [str(Path(__file__).resolve().parents[1] / 'app/gui/wizard')]
    monkeypatch.setitem(sys.modules, 'app.gui.wizard', wizard)
    qtcore = ModuleType('PySide6.QtCore'); qtcore.QTimer = Timer
    monkeypatch.setitem(sys.modules, 'PySide6', ModuleType('PySide6'))
    monkeypatch.setitem(sys.modules, 'PySide6.QtCore', qtcore)
    monkeypatch.setitem(sys.modules, 'PySide6.QtWidgets', widgets)
    return widgets, MessageBox


def load(name, path):
    spec = spec_from_file_location(name, Path(__file__).resolve().parents[1] / path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_dialog_only_applies_checked_fields_and_rejects_bad_values(fake_qt):
    _, box = fake_qt
    module = load('isolated_project_edit_dialog', 'app/gui/wizard/project_edit_dialog.py')
    recipe = {'theme': 'before', 'artist': 'artist', 'user_lyrics_lines': ['line 1', 'line 2'],
              'vocal_offset_ms': -125, 'bpm_override': 140, 'references': ['a.wav'],
              'own_vocal_wav': 'voice.wav', 'export_stems': True}
    dialog = module.ProjectEditDialog(recipe)
    assert dialog.selected_overrides() == {}
    assert not dialog._controls['theme'][1].enabled
    theme_check, theme = dialog._controls['theme']
    theme_check.setChecked(True)
    assert theme.enabled
    theme.setText('after')
    lines_check, lines = dialog._controls['user_lyrics_lines']
    lines_check.setChecked(True)
    lines.setPlainText('changed line\nsecond line')
    assert dialog.selected_overrides() == {'theme': 'after', 'user_lyrics_lines': ['changed line', 'second line']}
    dialog._accept_changes()
    assert dialog.accepted and dialog.changes() == dialog.selected_overrides()
    assert recipe['theme'] == 'before' and recipe['own_vocal_wav'] == 'voice.wav'
    theme.setText(' ')
    dialog._accept_changes()
    assert box.warnings and 'invalid project edit' in box.warnings[-1][-1]


def test_action_confirmation_cancel_and_busy_paths(fake_qt, monkeypatch):
    _, box = fake_qt
    module = load('isolated_project_edit_action', 'app/gui/wizard/project_edit_action.py')
    calls = []
    class EditDialog:
        Accepted = 1
        result = 1
        def __init__(self, recipe, screen): calls.append(('dialog', recipe))
        def exec(self): return self.result
        def changes(self): return {'theme': 'new'}
        def replacements(self): return {}
    fake = ModuleType('app.gui.wizard.project_edit_dialog')
    fake.ProjectEditDialog = EditDialog
    monkeypatch.setitem(sys.modules, fake.__name__, fake)
    job = SimpleNamespace(track_id='opened-id', master_only=True, recipe={'theme': 'old'},
                          result={'pipeline': {'input_integrity': {'version': 1}}})
    run = SimpleNamespace(current_tid=None, batch_tids=[], track_job=lambda tid: calls.append(('track', tid)))
    orch = SimpleNamespace(enqueue_opened_rebuild=lambda source, changes: calls.append((source, changes)) or 'next')
    screen = SimpleNamespace(current_job=job, wizard=SimpleNamespace(steps=[run], orch=orch))
    EditDialog.result = 0
    module.start_project_edit(screen)
    assert len(calls) == 1
    EditDialog.result = 1
    box.answer = box.StandardButton.No
    module.start_project_edit(screen)
    assert len(calls) == 2
    box.answer = box.StandardButton.Yes
    module.start_project_edit(screen)
    assert calls[-2:] == [('opened-id', {'theme': 'new'}), ('track', 'next')]
    run.current_tid = 'busy'
    module.start_project_edit(screen)
    assert box.warnings and len(calls) == 5
    run.current_tid = None
    job.result = {'pipeline': {}}
    module.start_project_edit(screen)
    assert len(calls) == 5
