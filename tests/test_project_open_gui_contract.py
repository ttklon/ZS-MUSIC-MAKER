"""GUI callbacks tested with stubs, not a real Qt/Windows session."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType, SimpleNamespace
import sys

import pytest


@pytest.fixture
def module(monkeypatch):
    core = ModuleType('PySide6.QtCore')
    core.QTimer = type('QTimer', (), {})
    gui = ModuleType('PySide6.QtGui')
    for name in ('QAction', 'QKeySequence', 'QShortcut'):
        setattr(gui, name, type(name, (), {}))
    widgets = ModuleType('PySide6.QtWidgets')
    for name in ('QHBoxLayout', 'QLabel', 'QMainWindow', 'QPushButton', 'QScrollArea',
                 'QStackedWidget', 'QVBoxLayout', 'QWidget'):
        setattr(widgets, name, type(name, (), {}))
    class Box:
        warnings = []
        notices = []
        @classmethod
        def warning(cls, *args): cls.warnings.append(args)
        @classmethod
        def information(cls, *args): cls.notices.append(args)
    class Dialog:
        path = ''
        @classmethod
        def getExistingDirectory(cls, *args): return cls.path
    widgets.QFileDialog, widgets.QMessageBox = Dialog, Box
    monkeypatch.setitem(sys.modules, 'PySide6', ModuleType('PySide6'))
    monkeypatch.setitem(sys.modules, 'PySide6.QtCore', core)
    monkeypatch.setitem(sys.modules, 'PySide6.QtGui', gui)
    monkeypatch.setitem(sys.modules, 'PySide6.QtWidgets', widgets)
    for filename, names in [('steps_brief', ['StepBrief']), ('steps_material', ['StepMaterial']),
                            ('steps_run', ['StepResult', 'StepRun']), ('steps_tuning', ['StepTuning']),
                            ('steps_voice', ['StepVoice']), ('ui', ['StepBase'])]:
        fake = ModuleType('app.gui.wizard.' + filename)
        for name in names: setattr(fake, name, type(name, (), {}))
        monkeypatch.setitem(sys.modules, fake.__name__, fake)
    path = Path(__file__).resolve().parents[1] / 'app/gui/wizard/window.py'
    spec = spec_from_file_location('test_project_open_window', path)
    loaded = module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded, Box, Dialog


def test_open_project_requires_selection_and_blocks_when_busy(module):
    window, box, dialog = module
    calls = []
    job = object()
    orch = SimpleNamespace(open_project=lambda p: calls.append(p) or 'id', jobs={'id': job})
    run = SimpleNamespace(current_tid='active')
    wizard = SimpleNamespace(steps=[run], orch=orch, go_to_result=lambda j: calls.append(j))
    window.Wizard.open_project(wizard)
    assert box.warnings and not calls and not box.notices
    run.current_tid = None
    dialog.path = ''
    window.Wizard.open_project(wizard)
    assert box.notices and not calls
    dialog.path = '/selected/project'
    window.Wizard.open_project(wizard)
    assert calls == ['/selected/project', job]


def test_open_project_shows_invalid_project_error(module):
    window, box, dialog = module
    dialog.path = '/invalid'
    def fail(path): raise ValueError('invalid report')
    wizard = SimpleNamespace(steps=[SimpleNamespace(current_tid=None)],
                             orch=SimpleNamespace(open_project=fail))
    window.Wizard.open_project(wizard)
    assert box.warnings and 'invalid report' in box.warnings[-1][-1]
