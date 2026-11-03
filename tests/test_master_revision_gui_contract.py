"""Exercise result-screen callbacks with Qt stubs; this is not a GUI/Windows test."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType, SimpleNamespace
import sys

import pytest


@pytest.fixture
def gui_module(monkeypatch):
    qtwidgets = ModuleType("PySide6.QtWidgets")
    class MessageBox:
        class StandardButton:
            Yes = 1
            No = 0
        answer = 1
        warnings = []
        @classmethod
        def question(cls, *args): return cls.answer
        @classmethod
        def warning(cls, *args): cls.warnings.append(args)
        @classmethod
        def information(cls, *args): pass
    qtwidgets.QMessageBox = MessageBox
    for name in ("QHBoxLayout", "QLabel", "QProgressBar", "QPushButton", "QTextEdit"):
        setattr(qtwidgets, name, type(name, (), {}))
    qtcore = ModuleType("PySide6.QtCore")
    qtcore.Qt, qtcore.QTimer = type("Qt", (), {}), type("QTimer", (), {})
    pyside = ModuleType("PySide6")
    monkeypatch.setitem(sys.modules, "PySide6", pyside)
    monkeypatch.setitem(sys.modules, "PySide6.QtWidgets", qtwidgets)
    monkeypatch.setitem(sys.modules, "PySide6.QtCore", qtcore)
    ui = ModuleType("app.gui.wizard.ui")
    ui.DIM = ui.H1 = ui.H2 = ui.HR = lambda *a: None
    ui.StepBase = type("StepBase", (), {})
    monkeypatch.setitem(sys.modules, "app.gui.wizard.ui", ui)
    path = Path(__file__).resolve().parents[1] / "app/gui/wizard/steps_run.py"
    spec = spec_from_file_location("test_isolated_gui_callbacks", path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, MessageBox


def test_revision_button_forwards_only_allowed_settings_and_tracks_job(gui_module):
    module, box = gui_module
    calls = []
    run = SimpleNamespace(current_tid=None, track_job=lambda tid: calls.append(("track", tid)))
    orch = SimpleNamespace(enqueue_master_revision=lambda source, settings: calls.append((source, settings)) or "new-id")
    wizard = SimpleNamespace(steps=[run], orch=orch,
                             current_recipe=lambda: {"stands": ["car"], "export_stems": False, "theme": "changed"})
    obj = SimpleNamespace(current_job=SimpleNamespace(track_id="old-id"), wizard=wizard)
    module.StepResult.rebuild_part(obj)
    assert calls == [("old-id", {"stands": ["car"], "export_stems": False}), ("track", "new-id")]
    box.answer = box.StandardButton.No
    module.StepResult.rebuild_part(obj)
    assert len(calls) == 2
    run.current_tid = "busy"
    module.StepResult.rebuild_part(obj)
    assert len(calls) == 2 and box.warnings


def test_full_and_batch_are_attached_to_progress(gui_module):
    module, _ = gui_module
    calls = []
    run = SimpleNamespace(current_tid=None, track_job=lambda tid: calls.append(("track", tid)),
                          track_batch=lambda tids: calls.append(("batch", tids)))
    orch = SimpleNamespace(enqueue=lambda recipe: calls.append(("full", recipe)) or "full-id",
                           enqueue_batch=lambda recipes: calls.append(("recipes", recipes)) or ["a", "b", "c"])
    wizard = SimpleNamespace(steps=[run], orch=orch)
    obj = SimpleNamespace(current_job=SimpleNamespace(recipe={"theme": "x", "only": ["beat"]}), wizard=wizard)
    module.StepResult.rebuild_full(obj)
    module.StepResult.three_variants(obj)
    assert calls[0] == ("full", {"theme": "x"})
    assert calls[1] == ("track", "full-id")
    assert calls[-1] == ("batch", ["a", "b", "c"])
    assert all("only" not in recipe for recipe in calls[2][1])


def test_result_shows_reference_asr_status(gui_module):
    module, _ = gui_module
    class Label:
        text = ""
        def setText(self, text): self.text = text
    class Button:
        def setEnabled(self, enabled): pass
    info, detector = Label(), Label()
    obj = SimpleNamespace(info=info, detector=detector, btn_part=Button())
    asr = {"requested": True, "status": "BLOCKED", "reason": "local weights missing"}
    result = {"pipeline": {"verdict": "PARTIAL", "stages": [{"name": "_stage_lyrics", "output": {
        "creative_context": {"reference_asr": asr}}}]}}
    job = SimpleNamespace(result=result, track_id="test", started_at=1, finished_at=2, stage="done")
    module.StepResult.show_result(obj, job)
    assert "BLOCKED" in info.text and "local weights missing" in info.text
