"""Regression coverage for observable theme application fallback."""

from app.gui import theme


class _App:
    def __init__(self, failure=None):
        self.failure = failure
        self.stylesheet = None

    def setStyleSheet(self, stylesheet):
        if self.failure:
            raise self.failure
        self.stylesheet = stylesheet


def test_apply_returns_applied_status():
    app = _App()

    result = theme.apply(app)

    assert result == {"ok": True, "status": "applied"}
    assert app.stylesheet == theme.qss()


def test_apply_reports_stylesheet_failure():
    result = theme.apply(_App(RuntimeError("Qt unavailable")))

    assert result == {
        "ok": False,
        "status": "failed",
        "error": "RuntimeError: Qt unavailable",
    }
