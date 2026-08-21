# Идентификаторы `app/gui/theme_v12.py`

## Имена (ast.Name) (уникальных: 12)

| Имя | Использований |
|-----|--------------:|
| `t` | 64 |
| `f` | 8 |
| `TOKENS` | 3 |
| `FONTS` | 3 |
| `len` | 3 |
| `s` | 2 |
| `qss` | 2 |
| `str` | 1 |
| `__name__` | 1 |
| `Exception` | 1 |
| `print` | 1 |
| `app` | 1 |

## Вызванные функции/методы (ast.Call) (уникальных: 4)

| Имя | Использований |
|-----|--------------:|
| `len` | 3 |
| `qss` | 2 |
| `print` | 1 |
| `setStyleSheet` | 1 |

## Обращения к атрибутам (.attr) (уникальных: 1)

| Имя | Использований |
|-----|--------------:|
| `setStyleSheet` | 1 |

## Строковые литералы (уникальных: 99)

| Имя | Использований |
|-----|--------------:|
| `text.primary` | 10 |
| `accent` | 9 |
| `;\n    color: ` | 9 |
| `;\n    border: 1px solid ` | 9 |
| `line.subtle` | 8 |
| `line.strong` | 8 |
| `text.muted` | 6 |
| `bg.surface` | 5 |
| `bg.raised` | 5 |
| `bg.hover` | 5 |
| `text.secondary` | 5 |
| `bg.canvas` | 3 |
| `text.on_accent` | 3 |
| `accent.hover` | 3 |
| `danger` | 3 |
| `size_h3` | 3 |
| `bg.pressed` | 2 |
| `accent.pressed` | 2 |
| `focus.ring` | 2 |
| `#22D3EE` | 2 |
| `family_ui` | 2 |
| `family_mono` | 2 |
| `size_body` | 2 |
| `size_h1` | 2 |
| `size_h2` | 2 |
| `;\n    font-size: ` | 2 |
| `warn` | 1 |
| `success` | 1 |
| `#0B0D10` | 1 |
| `#12161B` | 1 |
| `#171C22` | 1 |
| `#1D242C` | 1 |
| `#232B34` | 1 |
| `#232830` | 1 |
| `#2E3540` | 1 |
| `#EAF0F6` | 1 |
| `#A8B0BB` | 1 |
| `#6E7684` | 1 |
| `#001318` | 1 |
| `#38DEEE` | 1 |
| `#1AB4CC` | 1 |
| `#F5B441` | 1 |
| `#F87171` | 1 |
| `#34D399` | 1 |
| `size_small` | 1 |
| `Inter, 'Segoe UI Variable', 'Segoe UI', Arial` | 1 |
| `'JetBrains Mono', Consolas, monospace` | 1 |
| `13px` | 1 |
| `22px` | 1 |
| `17px` | 1 |
| `14px` | 1 |
| `11px` | 1 |
| `Возвращает QSS для PySide6/PyQt6. Без градиентов, без картинок.` | 1 |
| `Применить тему v12 к QApplication. Молча деградирует, если Qt нет.` | 1 |
| `__main__` | 1 |
| `\n/* ============ v12 base ============ */\n* {\n    font-family: ` | 1 |
| `;\n}\nQWidget {\n    background: ` | 1 |
| `;\n    outline: 0;\n}\nQMainWindow, QDialog {\n    background: ` | 1 |
| `;\n}\n\n/* ============ панели/карточки ============ */\nQFrame#Card, QGroupBox {\n    background: ` | 1 |
| `; font-weight: 600; letter-spacing: -0.01em; }\nQLabel[role="h2"] { font-size: ` | 1 |
| `; font-weight: 600; color: ` | 1 |
| `; }\nQLabel[role="h3"] { font-size: ` | 1 |
| `; font-weight: 500; color: ` | 1 |
| `; }\nQLabel[role="muted"] { color: ` | 1 |
| `; }\n\n/* ============ кнопки ============ */\nQPushButton {\n    background: ` | 1 |
| `;   border-color: ` | 1 |
| `; }\nQPushButton:pressed   { background: ` | 1 |
| `; }\nQPushButton:disabled  { color: ` | 1 |
| `;      border-color: ` | 1 |
| `; }\n\nQPushButton[variant="primary"] {\n    background: ` | 1 |
| `;\n}\nQPushButton[variant="primary"]:hover   { background: ` | 1 |
| `; }\nQPushButton[variant="primary"]:pressed { background: ` | 1 |
| `; }\n\nQPushButton[variant="ghost"] {\n    background: transparent;\n    border-color: ` | 1 |
| `;\n}\nQPushButton[variant="ghost"]:hover {\n    background: ` | 1 |
| `;\n}\n\nQPushButton[variant="danger"] {\n    background: transparent;\n    color: ` | 1 |
| `;\n}\nQPushButton[variant="danger"]:hover { background: ` | 1 |
| `;\n    border-radius: 8px;\n    padding: 6px 10px;\n    selection-background-color: ` | 1 |
| `;\n    selection-color: ` | 1 |
| `;\n}\nQComboBox QAbstractItemView {\n    background: ` | 1 |
| `;\n    selection-background-color: ` | 1 |
| `;\n    outline: 0;\n}\n\n/* ============ прогресс ============ */\nQProgressBar {\n    background: ` | 1 |
| `;\n    border-radius: 8px;\n    height: 10px;\n    text-align: center;\n    color: ` | 1 |
| `;\n}\nQProgressBar::chunk {\n    background: ` | 1 |
| `;\n    border-radius: 2px;\n}\nQSlider::handle:horizontal {\n    width: 16px; margin: -6px 0;\n    background: ` | 1 |
| `;\n    border-radius: 8px;\n}\nQSlider::handle:horizontal:hover { background: ` | 1 |
| `; }\n\n/* ============ табы (для экспертного режима) ============ */\nQTabWidget::pane { border: 1px solid ` | 1 |
| `; border-radius: 8px; top: -1px; }\nQTabBar::tab {\n    background: transparent;\n    color: ` | 1 |
| `; }\nQTabBar::tab:selected {\n    color: ` | 1 |
| `;\n    border-bottom: 2px solid ` | 1 |
| `;\n    font-size: 20px;\n    padding: 12px 16px;\n    background: ` | 1 |
| `;\n    border-radius: 10px;\n    color: ` | 1 |
| `;\n}\nQLabel#KaraokeLine[state="active"] {\n    border-color: ` | 1 |
| `;\n}\n\n/* ============ статус-бар ============ */\nQStatusBar {\n    background: ` | 1 |
| `;\n    border-top: 1px solid ` | 1 |
| `;\n}\n\n/* ============ тултипы ============ */\nQToolTip {\n    background: ` | 1 |
| `;\n    border-radius: 6px;\n    padding: 6px 8px;\n}\n` | 1 |
| `theme_v12 QSS length = ` | 1 |
| ` chars, tokens = ` | 1 |
| `, fonts = ` | 1 |

## Числовые литералы (уникальных: 0)

| Имя | Использований |
|-----|--------------:|