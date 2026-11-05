from __future__ import annotations

import sys
import types

import pytest

from app.cli import gui


def test_gui_theme_failure_is_reported_without_blocking_startup(monkeypatch) -> None:
    class FakeApplication:
        @staticmethod
        def instance():
            return None

        def __init__(self, _argv):
            pass

        def exec(self):
            return 0

    class FakeWizard:
        def __init__(self, **_kwargs):
            pass

        def setWindowTitle(self, _title):
            pass

        def show(self):
            pass

    qt_widgets = types.ModuleType("PySide6.QtWidgets")
    qt_widgets.QApplication = FakeApplication
    gui_package = types.ModuleType("app.gui")
    theme = types.ModuleType("app.gui.theme")
    theme.apply = lambda _app: (_ for _ in ()).throw(RuntimeError("theme boom"))
    wizard = types.ModuleType("app.gui.wizard")
    wizard.Wizard = FakeWizard
    hw_probe = types.ModuleType("app.hw_probe")
    hw_probe.probe = lambda: object()
    logger = types.ModuleType("app.logger")
    logger.setup_logger = lambda _name: object()
    runtime = types.ModuleType("app.runtime_orchestrator")
    runtime.RuntimeOrchestrator = lambda **_kwargs: object()

    gui_package.theme = theme
    monkeypatch.setitem(sys.modules, "PySide6", types.ModuleType("PySide6"))
    monkeypatch.setitem(sys.modules, "PySide6.QtWidgets", qt_widgets)
    monkeypatch.setitem(sys.modules, "app.gui", gui_package)
    monkeypatch.setitem(sys.modules, "app.gui.theme", theme)
    monkeypatch.setitem(sys.modules, "app.gui.wizard", wizard)
    monkeypatch.setitem(sys.modules, "app.hw_probe", hw_probe)
    monkeypatch.setitem(sys.modules, "app.logger", logger)
    monkeypatch.setitem(sys.modules, "app.runtime_orchestrator", runtime)
    messages: list[str] = []
    monkeypatch.setattr(gui, "safe_print", messages.append)

    with pytest.raises(SystemExit) as result:
        gui.try_launch_pyside()

    assert result.value.code == 0
    assert messages == ["[main] GUI theme fallback after apply failure: theme boom"]
