"""Isolated GUI method tests using Qt stubs, not a live GUI or device test."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType, SimpleNamespace
import sys

import pytest


@pytest.fixture
def gui_modules(monkeypatch):
    widgets = ModuleType("PySide6.QtWidgets")
    class Base:
        pass
    class MessageBox:
        warnings = []
        @classmethod
        def warning(cls, *args): cls.warnings.append(args)
        @classmethod
        def information(cls, *args): pass
    for name in ("QCheckBox", "QComboBox", "QDialog", "QFileDialog", "QHBoxLayout", "QLabel",
                 "QPushButton", "QSpinBox", "QVBoxLayout"):
        setattr(widgets, name, type(name, (Base,), {}))
    widgets.QMessageBox = MessageBox
    core = ModuleType("PySide6.QtCore")
    core.QThread = type("QThread", (), {})
    core.QTimer = type("QTimer", (), {})
    core.Signal = lambda *a: None
    monkeypatch.setitem(sys.modules, "PySide6", ModuleType("PySide6"))
    monkeypatch.setitem(sys.modules, "PySide6.QtCore", core)
    monkeypatch.setitem(sys.modules, "PySide6.QtWidgets", widgets)
    ui = ModuleType("app.gui.wizard.ui")
    ui.DIM = ui.H1 = ui.H2 = lambda *a: None
    ui.StepBase = type("StepBase", (), {})
    monkeypatch.setitem(sys.modules, "app.gui.wizard.ui", ui)
    root = Path(__file__).resolve().parents[1] / "app/gui/wizard"
    def load(name):
        spec = spec_from_file_location("isolated_" + name, root / f"{name}.py")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return load("steps_voice"), load("record_dialog"), MessageBox


def test_selected_instrumental_and_project_duration_reach_record_dialog(gui_modules, monkeypatch):
    module, _, _ = gui_modules
    calls = []
    class Dialog:
        Accepted = 1
        result_path = "recorded.wav"
        def __init__(self, parent, **kwargs): calls.append(kwargs)
        def exec(self): return self.Accepted
    record_module = ModuleType("app.gui.wizard.record_dialog")
    record_module.RecordDialog = Dialog
    monkeypatch.setitem(sys.modules, "app.gui.wizard.record_dialog", record_module)
    wizard = SimpleNamespace(recipe={"beat_engine": "user_audio", "beat_input_path": "chosen.wav", "duration_sec": 240})
    obj = SimpleNamespace(wizard=wizard, set_own_vocal=lambda path: calls.append(path), refresh_vault=lambda: None)
    module.StepVoice.open_karaoke(obj)
    assert calls == [{"default_backing": "chosen.wav", "default_duration": 240}, "recorded.wav"]
    wizard.recipe = {"beat_engine": "procedural", "beat_input_path": "old.wav", "duration_sec": 60}
    module.StepVoice.open_karaoke(obj)
    assert calls[2]["default_backing"] == "" and calls[2]["default_duration"] == 60


def test_dialog_accepts_only_after_recording_thread_has_finished(gui_modules):
    _, module, _ = gui_modules
    events = []
    label = SimpleNamespace(setText=lambda text: events.append(("status", text)))
    button = SimpleNamespace(setEnabled=lambda value: events.append(("enabled", value)))
    thread = SimpleNamespace(isRunning=lambda: True)
    obj = SimpleNamespace(_thread=thread, _pending_accept=False, result_path=None, status=label, btn_record=button,
                          accept=lambda: events.append(("accept",)))
    module.RecordDialog._on_recorded(obj, {"path": "take.wav", "warning": ""})
    assert obj._pending_accept and obj.result_path == "take.wav" and ("accept",) not in events
    module.RecordDialog._on_thread_finished(obj)
    assert events[-1] == ("accept",) and ("enabled", True) in events


def test_recorder_reports_missing_file_as_failure(gui_modules, monkeypatch):
    _, module, _ = gui_modules
    fake = ModuleType("ui.karaoke_recorder")
    fake.record_with_backing = lambda *a, **k: {"ok": True}
    monkeypatch.setitem(sys.modules, "ui.karaoke_recorder", fake)
    messages = []
    obj = SimpleNamespace(backing="", duration_sec=1, style="singing", text="",
                          finished_ok=SimpleNamespace(emit=lambda value: messages.append(("ok", value))),
                          failed=SimpleNamespace(emit=lambda value: messages.append(("error", value))))
    module._Recorder.run(obj)
    assert len(messages) == 1 and messages[0][0] == "error"


def test_voice_commit_forwards_optional_effect_controls(gui_modules):
    module, _, _ = gui_modules
    obj = SimpleNamespace(mode=SimpleNamespace(currentIndex=lambda: 0), _own_vocal="voice.wav",
        use_rvc=SimpleNamespace(isChecked=lambda: False), use_vocal_fx=SimpleNamespace(isChecked=lambda: True),
        use_tune=SimpleNamespace(isChecked=lambda: False), _rvc_model_path="", _rvc_index_path="",
        rvc_pitch=SimpleNamespace(value=lambda: 0), vocal_offset=SimpleNamespace(value=lambda: -100))
    recipe = {}
    module.StepVoice.commit(obj, recipe)
    assert recipe["own_vocal_wav"] == "voice.wav" and not recipe["use_rvc"] and not recipe["tune"]
    assert recipe["use_vocal_fx"] and recipe["vocal_offset_ms"] == -100


def test_dialog_window_close_waits_for_live_recording_thread(gui_modules):
    _, module, _ = gui_modules
    calls = []
    obj = SimpleNamespace(_thread=SimpleNamespace(isRunning=lambda: True),
                          status=SimpleNamespace(setText=lambda text: calls.append(text)))
    event = SimpleNamespace(ignore=lambda: calls.append("ignored"))
    module.RecordDialog.closeEvent(obj, event)
    assert calls[-1] == "ignored" and "завершения записи" in calls[0]


def test_vault_ui_does_not_claim_phoneme_recognition_or_model_training(gui_modules, monkeypatch):
    from modules import voice_convert
    module, _, _ = gui_modules
    monkeypatch.setattr(voice_convert, "vault_summary", lambda: {
        "recordings": 3, "total_minutes": 10, "minimum_duration_met": True,
        "phoneme_coverage_pct": 70, "recommended_next_styles": []})
    messages = []
    obj = SimpleNamespace(vault_label=SimpleNamespace(setText=lambda value: messages.append(value)))
    module.StepVoice.refresh_vault(obj)
    assert "не распознавание аудио" in messages[0]
    assert "обучение RVC не подтверждено" in messages[0] and "Готово к обучению" not in messages[0]
