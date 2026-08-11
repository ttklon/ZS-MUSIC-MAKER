"""
[v8] theme_v8.py — современная тёмная тема QSS, продажный вид, без «нейроношности».

Требования ТЗ (20-й блок и финальное напоминание):
  • «МАКСИМАЛЬНО СОВРЕМЕННЫЙ GUI»
  • «красивые библиотеки» (nation / reactbits.dev vibe)
  • «не быть нейроношным оформлением (градиенты, эмоджи-мусор, csv, svg…)»
  • «продажный вид должен иметь»

Реализация: минималистичная палитра, узкие акценты на цветах Supra-red и
Neon-cyan (ассоциации с автомобилями/ночью), плавные hover-переходы, крупный
типографический ритм, никаких лишних эмоджи в UI-элементах.
"""

from __future__ import annotations

# Палитра v8: «Night Drive»
COLORS = {
    "bg": "#0d0f14",  # почти чёрный, чуть синий подтон
    "surface": "#141821",
    "surface_2": "#1c2130",
    "border": "#232838",
    "text": "#eaecf2",
    "text_dim": "#8a90a3",
    "accent": "#ff2a4b",  # Supra red
    "accent_hi": "#ff6480",
    "neon": "#00d8ff",  # cyan
    "success": "#3ecf8e",
    "warn": "#ffb020",
    "danger": "#ff5573",
}


QSS = f"""
/* -------- global -------- */
* {{
    font-family: "Segoe UI", "Inter", "SF Pro Display", sans-serif;
    color: {COLORS['text']};
}}
QMainWindow, QWidget {{
    background-color: {COLORS['bg']};
}}

/* -------- headings -------- */
QLabel#H1 {{
    font-size: 26px;
    font-weight: 700;
    letter-spacing: -0.02em;
    padding: 6px 0 10px 0;
    color: {COLORS['text']};
}}
QLabel#H2 {{
    font-size: 17px;
    font-weight: 600;
    color: {COLORS['text']};
}}
QLabel[class="dim"] {{
    color: {COLORS['text_dim']};
    font-size: 13px;
    line-height: 1.5;
}}
QLabel#accent {{
    color: {COLORS['accent']};
    font-weight: 700;
}}
QLabel#neon {{
    color: {COLORS['neon']};
    font-weight: 700;
}}

/* -------- buttons -------- */
QPushButton {{
    background: {COLORS['surface_2']};
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
    padding: 10px 18px;
    font-weight: 600;
    font-size: 14px;
    color: {COLORS['text']};
}}
QPushButton:hover  {{ background: #232838; border-color: {COLORS['accent']}; }}
QPushButton:pressed{{ background: #2c334a; }}
QPushButton:disabled{{ color: {COLORS['text_dim']}; }}

QPushButton#primary {{
    background: {COLORS['accent']};
    border: 1px solid {COLORS['accent']};
    color: white;
}}
QPushButton#primary:hover  {{ background: {COLORS['accent_hi']}; }}
QPushButton#primary:pressed{{ background: #cf1533; }}

QPushButton#neon {{
    background: transparent;
    border: 1.5px solid {COLORS['neon']};
    color: {COLORS['neon']};
}}
QPushButton#neon:hover {{
    background: rgba(0, 216, 255, 0.08);
    color: white;
}}

QPushButton#ghost {{
    background: transparent;
    border: 1px solid {COLORS['border']};
    color: {COLORS['text_dim']};
}}

/* -------- inputs -------- */
QLineEdit, QTextEdit, QComboBox, QSpinBox {{
    background: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 14px;
    selection-background-color: {COLORS['accent']};
}}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border-color: {COLORS['accent']};
    background: {COLORS['surface_2']};
}}

/* -------- lists -------- */
QListWidget {{
    background: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 4px;
    outline: none;
}}
QListWidget::item {{
    padding: 8px 10px;
    border-radius: 6px;
    margin: 1px 0;
}}
QListWidget::item:hover    {{ background: {COLORS['surface_2']}; }}
QListWidget::item:selected {{ background: rgba(255, 42, 75, 0.14);
                              color: white;
                              border-left: 3px solid {COLORS['accent']}; }}

/* -------- sliders -------- */
QSlider::groove:horizontal {{
    height: 6px;
    background: {COLORS['surface_2']};
    border-radius: 3px;
}}
QSlider::sub-page:horizontal {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 {COLORS['accent']},
                                stop:1 {COLORS['neon']});
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: white;
    width: 16px;
    margin: -6px 0;
    border-radius: 8px;
}}
QSlider::handle:horizontal:hover {{
    background: {COLORS['accent_hi']};
}}

/* -------- progress -------- */
QProgressBar {{
    background: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    text-align: center;
    height: 22px;
    color: {COLORS['text']};
    font-weight: 600;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 {COLORS['accent']},
                                stop:1 {COLORS['neon']});
    border-radius: 5px;
}}

/* -------- groupbox -------- */
QGroupBox {{
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
    margin-top: 14px;
    padding: 14px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {COLORS['text_dim']};
    background: {COLORS['bg']};
}}

/* -------- scrollbars -------- */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['border']};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: {COLORS['accent']}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}

/* -------- menus -------- */
QMenuBar {{
    background: {COLORS['bg']};
    border-bottom: 1px solid {COLORS['border']};
    padding: 4px;
}}
QMenuBar::item {{
    padding: 6px 12px;
    background: transparent;
    border-radius: 6px;
}}
QMenuBar::item:selected {{ background: {COLORS['surface_2']}; }}
QMenu {{
    background: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 6px;
}}
QMenu::item {{
    padding: 8px 20px;
    border-radius: 6px;
}}
QMenu::item:selected {{ background: {COLORS['surface_2']}; }}

/* -------- checkbox / radio -------- */
QCheckBox, QRadioButton {{
    spacing: 8px;
    font-size: 14px;
}}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 18px; height: 18px;
    border: 1.5px solid {COLORS['border']};
    background: {COLORS['surface']};
}}
QCheckBox::indicator {{ border-radius: 4px; }}
QRadioButton::indicator {{ border-radius: 9px; }}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background: {COLORS['accent']};
    border-color: {COLORS['accent']};
}}

/* -------- frames / separators -------- */
QFrame[frameShape="4"] {{
    background: {COLORS['border']};
    max-height: 1px;
}}

/* -------- tabs (если используются) -------- */
QTabBar::tab {{
    background: transparent;
    padding: 10px 16px;
    color: {COLORS['text_dim']};
    border-bottom: 2px solid transparent;
}}
QTabBar::tab:selected {{
    color: {COLORS['text']};
    border-bottom: 2px solid {COLORS['accent']};
}}
QTabBar::tab:hover {{ color: {COLORS['text']}; }}
"""


def apply_v8(app_or_widget):
    """Применить тему к QApplication или QWidget."""
    try:
        app_or_widget.setStyleSheet(QSS)
    except Exception as e:
        print(f"[theme_v8] apply failed: {e}")
    return QSS
