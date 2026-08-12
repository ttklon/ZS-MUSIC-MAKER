# -*- coding: utf-8 -*-
"""
ZS Music Maker v12 «Hit Locked Pro» — theme_v12.py
==================================================

Современная строгая тема без градиентов, эмодзи и «нейроношного» блеска.
Реализует пункт «ПРОДАЖНЫЙ ВИД, СОВРЕМЕННЫЙ GUI» из финального напоминания ТЗ.

Принципы (Nation / reactbits / material-3 minimal):
  · plain flat surfaces, никаких linear-gradient;
  · один accent-цвет (electric-cyan), один warning (amber);
  · строгая типографика Inter/JetBrains Mono;
  · плотная сетка 4pt, крупные тач-цели ≥40px;
  · плавные, но короткие hover (120ms), никаких «прыгающих» эффектов;
  · тёмный фон, оффсетный контраст 4.5:1 минимум (WCAG AA).

Тема оставлена рядом с v8-темой (theme_v8.py) — v11 продолжает работать,
а v12 UI просто предпочитает эту, если PySide6 доступен.
"""

from __future__ import annotations

# Токены дизайн-системы v12 (RGB, без градиентов).
TOKENS = {
    "bg.canvas":    "#0B0D10",   # почти-чёрный фон
    "bg.surface":   "#12161B",   # карточки/панели
    "bg.raised":    "#171C22",   # диалоги, поповеры
    "bg.hover":     "#1D242C",
    "bg.pressed":   "#232B34",

    "line.subtle":  "#232830",
    "line.strong":  "#2E3540",

    "text.primary":   "#EAF0F6",
    "text.secondary": "#A8B0BB",
    "text.muted":     "#6E7684",
    "text.on_accent": "#001318",

    "accent":         "#22D3EE",  # electric cyan
    "accent.hover":   "#38DEEE",
    "accent.pressed": "#1AB4CC",

    "warn":           "#F5B441",
    "danger":         "#F87171",
    "success":        "#34D399",

    "focus.ring":     "#22D3EE",
}

FONTS = {
    "family_ui":   "Inter, 'Segoe UI Variable', 'Segoe UI', Arial",
    "family_mono": "'JetBrains Mono', Consolas, monospace",
    "size_body":   "13px",
    "size_h1":     "22px",
    "size_h2":     "17px",
    "size_h3":     "14px",
    "size_small":  "11px",
}


def qss() -> str:
    """Возвращает QSS для PySide6/PyQt6. Без градиентов, без картинок."""
    t = TOKENS
    f = FONTS
    return f"""
/* ============ v12 base ============ */
* {{
    font-family: {f['family_ui']};
    font-size: {f['size_body']};
    color: {t['text.primary']};
}}
QWidget {{
    background: {t['bg.canvas']};
    outline: 0;
}}
QMainWindow, QDialog {{
    background: {t['bg.canvas']};
}}

/* ============ панели/карточки ============ */
QFrame#Card, QGroupBox {{
    background: {t['bg.surface']};
    border: 1px solid {t['line.subtle']};
    border-radius: 10px;
    padding: 12px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: {t['text.secondary']};
    font-size: {f['size_h3']};
    letter-spacing: 0.02em;
    text-transform: uppercase;
}}

/* ============ заголовки ============ */
QLabel[role="h1"] {{ font-size: {f['size_h1']}; font-weight: 600; letter-spacing: -0.01em; }}
QLabel[role="h2"] {{ font-size: {f['size_h2']}; font-weight: 600; color: {t['text.primary']}; }}
QLabel[role="h3"] {{ font-size: {f['size_h3']}; font-weight: 500; color: {t['text.secondary']}; }}
QLabel[role="muted"] {{ color: {t['text.muted']}; }}

/* ============ кнопки ============ */
QPushButton {{
    background: {t['bg.raised']};
    color: {t['text.primary']};
    border: 1px solid {t['line.strong']};
    border-radius: 8px;
    padding: 8px 16px;
    min-height: 34px;
    font-weight: 500;
}}
QPushButton:hover     {{ background: {t['bg.hover']};   border-color: {t['line.strong']}; }}
QPushButton:pressed   {{ background: {t['bg.pressed']}; }}
QPushButton:disabled  {{ color: {t['text.muted']};      border-color: {t['line.subtle']}; }}

QPushButton[variant="primary"] {{
    background: {t['accent']};
    color: {t['text.on_accent']};
    border: 1px solid {t['accent']};
}}
QPushButton[variant="primary"]:hover   {{ background: {t['accent.hover']}; }}
QPushButton[variant="primary"]:pressed {{ background: {t['accent.pressed']}; }}

QPushButton[variant="ghost"] {{
    background: transparent;
    border-color: {t['line.subtle']};
    color: {t['text.secondary']};
}}
QPushButton[variant="ghost"]:hover {{
    background: {t['bg.hover']};
    color: {t['text.primary']};
}}

QPushButton[variant="danger"] {{
    background: transparent;
    color: {t['danger']};
    border: 1px solid {t['danger']};
}}
QPushButton[variant="danger"]:hover {{ background: {t['bg.hover']}; }}

/* ============ поля ============ */
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background: {t['bg.surface']};
    color: {t['text.primary']};
    border: 1px solid {t['line.strong']};
    border-radius: 8px;
    padding: 6px 10px;
    selection-background-color: {t['accent']};
    selection-color: {t['text.on_accent']};
}}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border: 1px solid {t['focus.ring']};
}}
QComboBox QAbstractItemView {{
    background: {t['bg.raised']};
    border: 1px solid {t['line.strong']};
    selection-background-color: {t['bg.hover']};
    outline: 0;
}}

/* ============ прогресс ============ */
QProgressBar {{
    background: {t['bg.surface']};
    border: 1px solid {t['line.subtle']};
    border-radius: 8px;
    height: 10px;
    text-align: center;
    color: {t['text.muted']};
}}
QProgressBar::chunk {{
    background: {t['accent']};
    border-radius: 7px;
}}

/* ============ слайдер ============ */
QSlider::groove:horizontal {{
    height: 4px;
    background: {t['line.strong']};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    width: 16px; margin: -6px 0;
    background: {t['accent']};
    border-radius: 8px;
}}
QSlider::handle:horizontal:hover {{ background: {t['accent.hover']}; }}

/* ============ табы (для экспертного режима) ============ */
QTabWidget::pane {{ border: 1px solid {t['line.subtle']}; border-radius: 8px; top: -1px; }}
QTabBar::tab {{
    background: transparent;
    color: {t['text.secondary']};
    padding: 8px 14px;
    border: 1px solid transparent;
    border-bottom: 2px solid transparent;
    margin-right: 4px;
}}
QTabBar::tab:hover  {{ color: {t['text.primary']}; }}
QTabBar::tab:selected {{
    color: {t['text.primary']};
    border-bottom: 2px solid {t['accent']};
}}

/* ============ скроллы (тонкие) ============ */
QScrollBar:vertical, QScrollBar:horizontal {{
    background: transparent; width: 10px; height: 10px; margin: 0;
}}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
    background: {t['line.strong']};
    border-radius: 5px; min-height: 24px; min-width: 24px;
}}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{
    background: {t['text.muted']};
}}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

/* ============ караоке-плашка ============ */
QLabel#KaraokeLine {{
    font-family: {f['family_mono']};
    font-size: 20px;
    padding: 12px 16px;
    background: {t['bg.raised']};
    border: 1px solid {t['line.subtle']};
    border-radius: 10px;
    color: {t['text.primary']};
}}
QLabel#KaraokeLine[state="active"] {{
    border-color: {t['accent']};
    color: {t['accent']};
}}

/* ============ статус-бар ============ */
QStatusBar {{
    background: {t['bg.surface']};
    border-top: 1px solid {t['line.subtle']};
    color: {t['text.muted']};
}}

/* ============ тултипы ============ */
QToolTip {{
    background: {t['bg.raised']};
    color: {t['text.primary']};
    border: 1px solid {t['line.strong']};
    border-radius: 6px;
    padding: 6px 8px;
}}
"""


def apply(app) -> None:
    """Применить тему v12 к QApplication. Молча деградирует, если Qt нет."""
    try:
        app.setStyleSheet(qss())
    except Exception:
        pass


# Простой self-test — QSS должен сгенерироваться без ошибок.
if __name__ == "__main__":
    s = qss()
    print(f"theme_v12 QSS length = {len(s)} chars, "
          f"tokens = {len(TOKENS)}, fonts = {len(FONTS)}")
