"""Limited, explicit edits for rebuilding an opened project with frozen inputs."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QLabel, QLineEdit, QMessageBox,
    QScrollArea, QSpinBox, QTextEdit, QVBoxLayout, QWidget,
)

from app.core.i18n import t
from app.core.project_edit import validate_project_overrides


class ProjectEditDialog(QDialog):
    def __init__(self, recipe: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("wizard.edit.title"))
        self.resize(780, 700)
        self._controls = {}
        layout = QVBoxLayout(self)
        notice = QLabel(t("wizard.edit.notice"))
        notice.setWordWrap(True)
        layout.addWidget(notice)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        panel = QWidget()
        form = QVBoxLayout(panel)

        def add(key, title, widget):
            check = QCheckBox(title)
            widget.setEnabled(False)
            check.toggled.connect(widget.setEnabled)
            form.addWidget(check)
            form.addWidget(widget)
            self._controls[key] = (check, widget)

        def line(key, title, fallback=""):
            widget = QLineEdit()
            value = recipe.get(key) or fallback
            widget.setText(value if isinstance(value, str) else "")
            add(key, title, widget)

        def text(key, title):
            widget = QTextEdit()
            widget.setMinimumHeight(90)
            value = recipe.get(key)
            if key == "user_lyrics_lines":
                value = "\n".join(value) if isinstance(value, list) and all(isinstance(v, str) for v in value) else ""
            widget.setPlainText(value if isinstance(value, str) else "")
            add(key, title, widget)

        line("theme", t("wizard.brief.theme"))
        line("artist", t("wizard.brief.artist"), recipe.get("artist_name", ""))
        line("user_extra_prompt", t("wizard.tuning.extra"))
        text("user_lyrics_lines", t("wizard.material.lyrics"))
        text("reference_lyrics", t("wizard.material.reference_text"))
        text("trend_notes", t("wizard.material.trend_notes"))
        for key, title, low, high, default in (
            ("bpm_override", t("wizard.tuning.bpm"), 0, 220, 0),
            ("vocal_offset_ms", t("wizard.voice.offset"), -5000, 5000, 0),
            ("n_verses", t("wizard.material.verses"), 1, 4, 2),
        ):
            widget = QSpinBox()
            widget.setRange(low, high)
            value = recipe.get(key)
            valid = type(value) is int and low <= value <= high
            if value is not None and not valid:
                title += " " + t("wizard.edit.not_representable")
            widget.setValue(value if valid else default)
            add(key, title, widget)
        stems = QCheckBox(t("wizard.tuning.stems"))
        value = recipe.get("export_stems", True)
        stems.setChecked(value if type(value) is bool else True)
        add("export_stems", t("wizard.edit.change_stems"), stems)
        form.addStretch()
        scroll.setWidget(panel)
        layout.addWidget(scroll)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._accept_changes)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._changes = None

    def selected_overrides(self) -> dict:
        changes = {}
        for key, (check, widget) in self._controls.items():
            if not check.isChecked():
                continue
            if isinstance(widget, QLineEdit):
                value = widget.text()
            elif isinstance(widget, QTextEdit):
                value = widget.toPlainText()
                if key == "user_lyrics_lines":
                    value = value.splitlines()
            elif isinstance(widget, QSpinBox):
                value = widget.value()
                if key == "bpm_override" and value == 0:
                    value = None
            else:
                value = widget.isChecked()
            changes[key] = value
        return validate_project_overrides(changes)

    def _accept_changes(self) -> None:
        self._changes = None
        try:
            self._changes = self.selected_overrides()
        except ValueError as error:
            QMessageBox.warning(self, t("dialog.error"), str(error))
            return
        if not self._changes:
            QMessageBox.information(self, t("wizard.edit.title"), t("wizard.edit.no_changes"))
            return
        self.accept()

    def changes(self) -> dict:
        return dict(self._changes or {})
