"""QtWidgets dialogue contracts with stubs; does not test a real desktop."""
import threading

from test_project_edit_gui_contract import fake_qt, load


def test_preparation_dialog_success_error_cancel_and_close(fake_qt, monkeypatch):
    from app.core import input_prepare_task
    _, box = fake_qt
    class Task:
        def __init__(self, replacements):
            self.done = threading.Event(); self.was_cancelled = False
            self.error = None; self.cancelled = False; self.started = False
        def start(self): self.started = True
        def cancel(self): self.cancelled = True
    monkeypatch.setattr(input_prepare_task, 'InputPreparationTask', Task)
    module = load('isolated_prepare_dialog', 'app/gui/wizard/input_prepare_dialog.py')
    dialog = module.InputPrepareDialog({'references': []})
    assert dialog.task.started and dialog._timer.running
    dialog._poll()
    assert not getattr(dialog, 'accepted', False)
    dialog.task.done.set(); dialog._poll()
    assert dialog.accepted and not dialog._timer.running and not dialog.task.cancelled
    cancel = module.InputPrepareDialog({'references': []})
    cancel.reject()
    assert cancel.rejected and cancel.task.cancelled and not cancel._timer.running
    cancel.task.done.set(); cancel._poll()  # a late timer event must not accept a cancelled dialog
    assert not getattr(cancel, 'accepted', False)
    closed = module.InputPrepareDialog({'references': []})
    closed.closeEvent(object())
    assert closed.task.cancelled and not closed._timer.running
    error = module.InputPrepareDialog({'references': []})
    error.task.error = 'disk read failed'; error.task.done.set()
    error._poll()
    assert error.rejected and box.warnings[-1][-1] == 'disk read failed'
    stopped = module.InputPrepareDialog({'references': []})
    stopped.task.was_cancelled = True; stopped.task.done.set()
    stopped._poll()
    assert stopped.rejected and not getattr(stopped, 'accepted', False)
