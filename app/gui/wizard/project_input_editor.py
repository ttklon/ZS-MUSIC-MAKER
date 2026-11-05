"""Explicit replacement controls; selecting files never modifies the originals."""
from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QFileDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.core.i18n import t


class ProjectInputEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected = {"references": None, "beat_input_path": None, "own_vocal_wav": None}
        self._checks = {}
        self._labels = {}
        root = QVBoxLayout(self)
        note = QLabel(t("wizard.inputs.notice"))
        note.setWordWrap(True)
        root.addWidget(note)
        for key, label in (("references", "wizard.inputs.references"),
                           ("beat_input_path", "wizard.inputs.backing"),
                           ("own_vocal_wav", "wizard.inputs.voice")):
            check = QCheckBox(t(label))
            self._checks[key] = check
            root.addWidget(check)
            row = QHBoxLayout()
            selected = QLabel(t("wizard.inputs.not_selected"))
            selected.setWordWrap(True)
            self._labels[key] = selected
            choose = QPushButton(t("wizard.inputs.choose"))
            choose.setEnabled(False)
            check.toggled.connect(choose.setEnabled)
            choose.clicked.connect(lambda _checked=False, k=key: self._choose(k))
            row.addWidget(selected, 1)
            row.addWidget(choose)
            if key == "references":
                clear = QPushButton(t("wizard.inputs.clear_references"))
                clear.setEnabled(False)
                check.toggled.connect(clear.setEnabled)
                clear.clicked.connect(self._clear_refs)
                row.addWidget(clear)
            root.addLayout(row)

    def _choose(self, key: str) -> None:
        title = t("wizard.inputs.choose")
        if key == "references":
            paths, _ = QFileDialog.getOpenFileNames(self, title, "", "Audio (*.wav *.flac *.ogg)")
            if paths:
                self._selected[key] = list(paths)
                self._labels[key].setText("\n".join(paths))
        else:
            path, _ = QFileDialog.getOpenFileName(self, title, "", "Audio (*.wav *.flac *.ogg)")
            if path:
                self._selected[key] = path
                self._labels[key].setText(path)

    def _clear_refs(self) -> None:
        self._selected["references"] = []
        self._labels["references"].setText(t("wizard.inputs.cleared"))

    def selections(self) -> dict:
        result = {}
        for key, check in self._checks.items():
            if not check.isChecked():
                continue
            selected = self._selected[key]
            if selected is None:
                raise ValueError(t("wizard.inputs.selection_required"))
            result[key] = list(selected) if key == "references" else selected
        return result
