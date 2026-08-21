# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/gui/theme.py`

**Всего строк:** 41

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| docstring | 23 | 56.1 |
| code | 11 | 26.8 |
| blank | 2 | 4.9 |
| try_block | 2 | 4.9 |
| def | 1 | 2.4 |
| import | 1 | 2.4 |
| return | 1 | 2.4 |

## Полный листинг с классификацией
```
    1 [docstring ] """Тёмная тема Qt в стиле «phonk night». Без внешних QSS-файлов."""
    2 [blank     ] 
    3 [blank     ] 
    4 [def       ] def apply_dark(app):
    5 [try_block ]     try:
    6 [import    ]         from PySide6.QtGui import QColor, QPalette
    7 [try_block ]     except Exception:
    8 [return    ]         return
    9 [code      ]     p = QPalette()
   10 [code      ]     p.setColor(QPalette.Window, QColor(15, 15, 18))
   11 [code      ]     p.setColor(QPalette.WindowText, QColor(230, 230, 235))
   12 [code      ]     p.setColor(QPalette.Base, QColor(22, 22, 27))
   13 [code      ]     p.setColor(QPalette.AlternateBase, QColor(28, 28, 34))
   14 [code      ]     p.setColor(QPalette.Text, QColor(232, 232, 235))
   15 [code      ]     p.setColor(QPalette.Button, QColor(30, 30, 36))
   16 [code      ]     p.setColor(QPalette.ButtonText, QColor(240, 240, 240))
   17 [code      ]     p.setColor(QPalette.Highlight, QColor(255, 90, 40))
   18 [code      ]     p.setColor(QPalette.HighlightedText, QColor(20, 20, 20))
   19 [code      ]     app.setPalette(p)
   20 [docstring ]     app.setStyleSheet("""
   21 [docstring ]         QWidget { font-family: 'Segoe UI', 'Arial'; font-size: 13px; color:#e8e8ee; }
   22 [docstring ]         QMainWindow { background: #0f0f12; }
   23 [docstring ]         QPushButton {
   24 [docstring ]             background: #23232b; border: 1px solid #333;
   25 [docstring ]             padding: 10px 20px; border-radius: 10px;
   26 [docstring ]         }
   27 [docstring ]         QPushButton:hover  { background: #2c2c36; border-color: #ff5a28; }
   28 [docstring ]         QPushButton:pressed{ background: #ff5a28; color: #111; }
   29 [docstring ]         QLabel#H1 { font-size: 22px; font-weight: 700; color: #ff5a28; }
   30 [docstring ]         QLabel#H2 { font-size: 16px; font-weight: 600; color: #e8e8ee; }
   31 [docstring ]         QLabel.dim { color: #9a9aa4; }
   32 [docstring ]         QLineEdit, QTextEdit, QComboBox, QSpinBox, QListWidget {
   33 [docstring ]             background: #17171d; border: 1px solid #2a2a34; border-radius: 8px;
   34 [docstring ]             padding: 6px;
   35 [docstring ]         }
   36 [docstring ]         QProgressBar {
   37 [docstring ]             background: #17171d; border: 1px solid #2a2a34;
   38 [docstring ]             border-radius: 6px; text-align: center;
   39 [docstring ]         }
   40 [docstring ]         QProgressBar::chunk { background: #ff5a28; border-radius: 6px; }
   41 [docstring ]     """)
```