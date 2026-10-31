# -*- coding: utf-8 -*-
"""
app/gui/wizard/ui.py — общие элементы шагов: заголовки, разделители и базовый класс шага.
"""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

def H1(text):
    l = QLabel(text)
    l.setObjectName("H1")
    return l
def H2(text):
    l = QLabel(text)
    l.setObjectName("H2")
    return l
def DIM(text):
    l = QLabel(text)
    l.setProperty("class", "dim")
    l.setStyleSheet("color:#9a9aa4;")
    l.setWordWrap(True)
    return l
def HR():
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet("color:#2a2a34;")
    return line
class StepBase(QWidget):
    def __init__(self, wizard):
        super().__init__()
        self.wizard = wizard
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(30, 20, 30, 20)
        self.root.setSpacing(12)
    def enter(self):
        pass
    def commit(self, recipe: dict):
        pass
    def help_text(self) -> str:
        return ""
