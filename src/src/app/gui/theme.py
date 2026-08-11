"""Тёмная тема Qt в стиле «phonk night». Без внешних QSS-файлов."""


def apply_dark(app):
    try:
        from PySide6.QtGui import QColor, QPalette
    except Exception:
        return
    p = QPalette()
    p.setColor(QPalette.Window, QColor(15, 15, 18))
    p.setColor(QPalette.WindowText, QColor(230, 230, 235))
    p.setColor(QPalette.Base, QColor(22, 22, 27))
    p.setColor(QPalette.AlternateBase, QColor(28, 28, 34))
    p.setColor(QPalette.Text, QColor(232, 232, 235))
    p.setColor(QPalette.Button, QColor(30, 30, 36))
    p.setColor(QPalette.ButtonText, QColor(240, 240, 240))
    p.setColor(QPalette.Highlight, QColor(255, 90, 40))
    p.setColor(QPalette.HighlightedText, QColor(20, 20, 20))
    app.setPalette(p)
    app.setStyleSheet("""
        QWidget { font-family: 'Segoe UI', 'Arial'; font-size: 13px; color:#e8e8ee; }
        QMainWindow { background: #0f0f12; }
        QPushButton {
            background: #23232b; border: 1px solid #333;
            padding: 10px 20px; border-radius: 10px;
        }
        QPushButton:hover  { background: #2c2c36; border-color: #ff5a28; }
        QPushButton:pressed{ background: #ff5a28; color: #111; }
        QLabel#H1 { font-size: 22px; font-weight: 700; color: #ff5a28; }
        QLabel#H2 { font-size: 16px; font-weight: 600; color: #e8e8ee; }
        QLabel.dim { color: #9a9aa4; }
        QLineEdit, QTextEdit, QComboBox, QSpinBox, QListWidget {
            background: #17171d; border: 1px solid #2a2a34; border-radius: 8px;
            padding: 6px;
        }
        QProgressBar {
            background: #17171d; border: 1px solid #2a2a34;
            border-radius: 6px; text-align: center;
        }
        QProgressBar::chunk { background: #ff5a28; border-radius: 6px; }
    """)
