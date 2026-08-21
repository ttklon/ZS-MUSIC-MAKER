# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/gui/theme_v12.py`

**Всего строк:** 261

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| docstring | 189 | 72.4 |
| code | 38 | 14.6 |
| blank | 26 | 10.0 |
| comment | 2 | 0.8 |
| def | 2 | 0.8 |
| try_block | 2 | 0.8 |
| import | 1 | 0.4 |
| branch | 1 | 0.4 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v12 «Hit Locked Pro» — theme_v12.py
    3 [docstring ] ==================================================
    4 [blank     ] 
    5 [docstring ] Современная строгая тема без градиентов, эмодзи и «нейроношного» блеска.
    6 [docstring ] Реализует пункт «ПРОДАЖНЫЙ ВИД, СОВРЕМЕННЫЙ GUI» из финального напоминания ТЗ.
    7 [blank     ] 
    8 [docstring ] Принципы (Nation / reactbits / material-3 minimal):
    9 [docstring ]   · plain flat surfaces, никаких linear-gradient;
   10 [docstring ]   · один accent-цвет (electric-cyan), один warning (amber);
   11 [docstring ]   · строгая типографика Inter/JetBrains Mono;
   12 [docstring ]   · плотная сетка 4pt, крупные тач-цели ≥40px;
   13 [docstring ]   · плавные, но короткие hover (120ms), никаких «прыгающих» эффектов;
   14 [docstring ]   · тёмный фон, оффсетный контраст 4.5:1 минимум (WCAG AA).
   15 [blank     ] 
   16 [docstring ] Тема оставлена рядом с v8-темой (theme_v8.py) — v11 продолжает работать,
   17 [docstring ] а v12 UI просто предпочитает эту, если PySide6 доступен.
   18 [docstring ] """
   19 [blank     ] 
   20 [import    ] from __future__ import annotations
   21 [blank     ] 
   22 [comment   ] # Токены дизайн-системы v12 (RGB, без градиентов).
   23 [code      ] TOKENS = {
   24 [code      ]     "bg.canvas": "#0B0D10",  # почти-чёрный фон
   25 [code      ]     "bg.surface": "#12161B",  # карточки/панели
   26 [code      ]     "bg.raised": "#171C22",  # диалоги, поповеры
   27 [code      ]     "bg.hover": "#1D242C",
   28 [code      ]     "bg.pressed": "#232B34",
   29 [code      ]     "line.subtle": "#232830",
   30 [code      ]     "line.strong": "#2E3540",
   31 [code      ]     "text.primary": "#EAF0F6",
   32 [code      ]     "text.secondary": "#A8B0BB",
   33 [code      ]     "text.muted": "#6E7684",
   34 [code      ]     "text.on_accent": "#001318",
   35 [code      ]     "accent": "#22D3EE",  # electric cyan
   36 [code      ]     "accent.hover": "#38DEEE",
   37 [code      ]     "accent.pressed": "#1AB4CC",
   38 [code      ]     "warn": "#F5B441",
   39 [code      ]     "danger": "#F87171",
   40 [code      ]     "success": "#34D399",
   41 [code      ]     "focus.ring": "#22D3EE",
   42 [code      ] }
   43 [blank     ] 
   44 [code      ] FONTS = {
   45 [code      ]     "family_ui": "Inter, 'Segoe UI Variable', 'Segoe UI', Arial",
   46 [code      ]     "family_mono": "'JetBrains Mono', Consolas, monospace",
   47 [code      ]     "size_body": "13px",
   48 [code      ]     "size_h1": "22px",
   49 [code      ]     "size_h2": "17px",
   50 [code      ]     "size_h3": "14px",
   51 [code      ]     "size_small": "11px",
   52 [code      ] }
   53 [blank     ] 
   54 [blank     ] 
   55 [def       ] def qss() -> str:
   56 [docstring ]     """Возвращает QSS для PySide6/PyQt6. Без градиентов, без картинок."""
   57 [code      ]     t = TOKENS
   58 [code      ]     f = FONTS
   59 [docstring ]     return f"""
   60 [docstring ] /* ============ v12 base ============ */
   61 [docstring ] * {{
   62 [docstring ]     font-family: {f['family_ui']};
   63 [docstring ]     font-size: {f['size_body']};
   64 [docstring ]     color: {t['text.primary']};
   65 [docstring ] }}
   66 [docstring ] QWidget {{
   67 [docstring ]     background: {t['bg.canvas']};
   68 [docstring ]     outline: 0;
   69 [docstring ] }}
   70 [docstring ] QMainWindow, QDialog {{
   71 [docstring ]     background: {t['bg.canvas']};
   72 [docstring ] }}
   73 [blank     ] 
   74 [docstring ] /* ============ панели/карточки ============ */
   75 [docstring ] QFrame#Card, QGroupBox {{
   76 [docstring ]     background: {t['bg.surface']};
   77 [docstring ]     border: 1px solid {t['line.subtle']};
   78 [docstring ]     border-radius: 10px;
   79 [docstring ]     padding: 12px;
   80 [docstring ] }}
   81 [docstring ] QGroupBox::title {{
   82 [docstring ]     subcontrol-origin: margin;
   83 [docstring ]     left: 10px;
   84 [docstring ]     padding: 0 6px;
   85 [docstring ]     color: {t['text.secondary']};
   86 [docstring ]     font-size: {f['size_h3']};
   87 [docstring ]     letter-spacing: 0.02em;
   88 [docstring ]     text-transform: uppercase;
   89 [docstring ] }}
   90 [blank     ] 
   91 [docstring ] /* ============ заголовки ============ */
   92 [docstring ] QLabel[role="h1"] {{ font-size: {f['size_h1']}; font-weight: 600; letter-spacing: -0.01em; }}
   93 [docstring ] QLabel[role="h2"] {{ font-size: {f['size_h2']}; font-weight: 600; color: {t['text.primary']}; }}
   94 [docstring ] QLabel[role="h3"] {{ font-size: {f['size_h3']}; font-weight: 500; color: {t['text.secondary']}; }}
   95 [docstring ] QLabel[role="muted"] {{ color: {t['text.muted']}; }}
   96 [blank     ] 
   97 [docstring ] /* ============ кнопки ============ */
   98 [docstring ] QPushButton {{
   99 [docstring ]     background: {t['bg.raised']};
  100 [docstring ]     color: {t['text.primary']};
  101 [docstring ]     border: 1px solid {t['line.strong']};
  102 [docstring ]     border-radius: 8px;
  103 [docstring ]     padding: 8px 16px;
  104 [docstring ]     min-height: 34px;
  105 [docstring ]     font-weight: 500;
  106 [docstring ] }}
  107 [docstring ] QPushButton:hover     {{ background: {t['bg.hover']};   border-color: {t['line.strong']}; }}
  108 [docstring ] QPushButton:pressed   {{ background: {t['bg.pressed']}; }}
  109 [docstring ] QPushButton:disabled  {{ color: {t['text.muted']};      border-color: {t['line.subtle']}; }}
  110 [blank     ] 
  111 [docstring ] QPushButton[variant="primary"] {{
  112 [docstring ]     background: {t['accent']};
  113 [docstring ]     color: {t['text.on_accent']};
  114 [docstring ]     border: 1px solid {t['accent']};
  115 [docstring ] }}
  116 [docstring ] QPushButton[variant="primary"]:hover   {{ background: {t['accent.hover']}; }}
  117 [docstring ] QPushButton[variant="primary"]:pressed {{ background: {t['accent.pressed']}; }}
  118 [blank     ] 
  119 [docstring ] QPushButton[variant="ghost"] {{
  120 [docstring ]     background: transparent;
  121 [docstring ]     border-color: {t['line.subtle']};
  122 [docstring ]     color: {t['text.secondary']};
  123 [docstring ] }}
  124 [docstring ] QPushButton[variant="ghost"]:hover {{
  125 [docstring ]     background: {t['bg.hover']};
  126 [docstring ]     color: {t['text.primary']};
  127 [docstring ] }}
  128 [blank     ] 
  129 [docstring ] QPushButton[variant="danger"] {{
  130 [docstring ]     background: transparent;
  131 [docstring ]     color: {t['danger']};
  132 [docstring ]     border: 1px solid {t['danger']};
  133 [docstring ] }}
  134 [docstring ] QPushButton[variant="danger"]:hover {{ background: {t['bg.hover']}; }}
  135 [blank     ] 
  136 [docstring ] /* ============ поля ============ */
  137 [docstring ] QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
  138 [docstring ]     background: {t['bg.surface']};
  139 [docstring ]     color: {t['text.primary']};
  140 [docstring ]     border: 1px solid {t['line.strong']};
  141 [docstring ]     border-radius: 8px;
  142 [docstring ]     padding: 6px 10px;
  143 [docstring ]     selection-background-color: {t['accent']};
  144 [docstring ]     selection-color: {t['text.on_accent']};
  145 [docstring ] }}
  146 [docstring ] QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus,
  147 [docstring ] QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
  148 [docstring ]     border: 1px solid {t['focus.ring']};
  149 [docstring ] }}
  150 [docstring ] QComboBox QAbstractItemView {{
  151 [docstring ]     background: {t['bg.raised']};
  152 [docstring ]     border: 1px solid {t['line.strong']};
  153 [docstring ]     selection-background-color: {t['bg.hover']};
  154 [docstring ]     outline: 0;
  155 [docstring ] }}
  156 [blank     ] 
  157 [docstring ] /* ============ прогресс ============ */
  158 [docstring ] QProgressBar {{
  159 [docstring ]     background: {t['bg.surface']};
  160 [docstring ]     border: 1px solid {t['line.subtle']};
  161 [docstring ]     border-radius: 8px;
  162 [docstring ]     height: 10px;
  163 [docstring ]     text-align: center;
  164 [docstring ]     color: {t['text.muted']};
  165 [docstring ] }}
  166 [docstring ] QProgressBar::chunk {{
  167 [docstring ]     background: {t['accent']};
  168 [docstring ]     border-radius: 7px;
  169 [docstring ] }}
  170 [blank     ] 
  171 [docstring ] /* ============ слайдер ============ */
  172 [docstring ] QSlider::groove:horizontal {{
  173 [docstring ]     height: 4px;
  174 [docstring ]     background: {t['line.strong']};
  175 [docstring ]     border-radius: 2px;
  176 [docstring ] }}
  177 [docstring ] QSlider::handle:horizontal {{
  178 [docstring ]     width: 16px; margin: -6px 0;
  179 [docstring ]     background: {t['accent']};
  180 [docstring ]     border-radius: 8px;
  181 [docstring ] }}
  182 [docstring ] QSlider::handle:horizontal:hover {{ background: {t['accent.hover']}; }}
  183 [blank     ] 
  184 [docstring ] /* ============ табы (для экспертного режима) ============ */
  185 [docstring ] QTabWidget::pane {{ border: 1px solid {t['line.subtle']}; border-radius: 8px; top: -1px; }}
  186 [docstring ] QTabBar::tab {{
  187 [docstring ]     background: transparent;
  188 [docstring ]     color: {t['text.secondary']};
  189 [docstring ]     padding: 8px 14px;
  190 [docstring ]     border: 1px solid transparent;
  191 [docstring ]     border-bottom: 2px solid transparent;
  192 [docstring ]     margin-right: 4px;
  193 [docstring ] }}
  194 [docstring ] QTabBar::tab:hover  {{ color: {t['text.primary']}; }}
  195 [docstring ] QTabBar::tab:selected {{
  196 [docstring ]     color: {t['text.primary']};
  197 [docstring ]     border-bottom: 2px solid {t['accent']};
  198 [docstring ] }}
  199 [blank     ] 
  200 [docstring ] /* ============ скроллы (тонкие) ============ */
  201 [docstring ] QScrollBar:vertical, QScrollBar:horizontal {{
  202 [docstring ]     background: transparent; width: 10px; height: 10px; margin: 0;
  203 [docstring ] }}
  204 [docstring ] QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
  205 [docstring ]     background: {t['line.strong']};
  206 [docstring ]     border-radius: 5px; min-height: 24px; min-width: 24px;
  207 [docstring ] }}
  208 [docstring ] QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{
  209 [docstring ]     background: {t['text.muted']};
  210 [docstring ] }}
  211 [docstring ] QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
  212 [docstring ] QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
  213 [blank     ] 
  214 [docstring ] /* ============ караоке-плашка ============ */
  215 [docstring ] QLabel#KaraokeLine {{
  216 [docstring ]     font-family: {f['family_mono']};
  217 [docstring ]     font-size: 20px;
  218 [docstring ]     padding: 12px 16px;
  219 [docstring ]     background: {t['bg.raised']};
  220 [docstring ]     border: 1px solid {t['line.subtle']};
  221 [docstring ]     border-radius: 10px;
  222 [docstring ]     color: {t['text.primary']};
  223 [docstring ] }}
  224 [docstring ] QLabel#KaraokeLine[state="active"] {{
  225 [docstring ]     border-color: {t['accent']};
  226 [docstring ]     color: {t['accent']};
  227 [docstring ] }}
  228 [blank     ] 
  229 [docstring ] /* ============ статус-бар ============ */
  230 [docstring ] QStatusBar {{
  231 [docstring ]     background: {t['bg.surface']};
  232 [docstring ]     border-top: 1px solid {t['line.subtle']};
  233 [docstring ]     color: {t['text.muted']};
  234 [docstring ] }}
  235 [blank     ] 
  236 [docstring ] /* ============ тултипы ============ */
  237 [docstring ] QToolTip {{
  238 [docstring ]     background: {t['bg.raised']};
  239 [docstring ]     color: {t['text.primary']};
  240 [docstring ]     border: 1px solid {t['line.strong']};
  241 [docstring ]     border-radius: 6px;
  242 [docstring ]     padding: 6px 8px;
  243 [docstring ] }}
  244 [docstring ] """
  245 [blank     ] 
  246 [blank     ] 
  247 [def       ] def apply(app) -> None:
  248 [docstring ]     """Применить тему v12 к QApplication. Молча деградирует, если Qt нет."""
  249 [try_block ]     try:
  250 [code      ]         app.setStyleSheet(qss())
  251 [try_block ]     except Exception:
  252 [code      ]         pass
  253 [blank     ] 
  254 [blank     ] 
  255 [comment   ] # Простой self-test — QSS должен сгенерироваться без ошибок.
  256 [branch    ] if __name__ == "__main__":
  257 [code      ]     s = qss()
  258 [code      ]     print(
  259 [code      ]         f"theme_v12 QSS length = {len(s)} chars, "
  260 [code      ]         f"tokens = {len(TOKENS)}, fonts = {len(FONTS)}"
  261 [code      ]     )
```