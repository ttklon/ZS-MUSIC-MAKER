# АУДИТ ФАЙЛА: `app/gui/wizard_v8_extensions.py`

**LOC:** 350  |  **Размер:** 14340 байт  |  **Проблем:** 8  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 17 | `__future__.annotations` | from |
| 20 | `PySide6.QtCore.Qt` | from |
| 20 | `PySide6.QtCore.Signal` | from |
| 21 | `PySide6.QtWidgets.QCheckBox` | from |
| 21 | `PySide6.QtWidgets.QComboBox` | from |
| 21 | `PySide6.QtWidgets.QDialog` | from |
| 21 | `PySide6.QtWidgets.QFrame` | from |
| 21 | `PySide6.QtWidgets.QGroupBox` | from |
| 21 | `PySide6.QtWidgets.QHBoxLayout` | from |
| 21 | `PySide6.QtWidgets.QHeaderView` | from |
| 21 | `PySide6.QtWidgets.QLabel` | from |
| 21 | `PySide6.QtWidgets.QMessageBox` | from |
| 21 | `PySide6.QtWidgets.QPushButton` | from |
| 21 | `PySide6.QtWidgets.QScrollArea` | from |
| 21 | `PySide6.QtWidgets.QTableWidget` | from |
| 21 | `PySide6.QtWidgets.QTableWidgetItem` | from |
| 21 | `PySide6.QtWidgets.QVBoxLayout` | from |
| 21 | `PySide6.QtWidgets.QWidget` | from |
| 88 | `modules.author_ref_lyrics.list_authors` | from |
| 99 | `modules.author_ref_lyrics.scan_library` | from |
| 117 | `modules.author_ref_lyrics.fetch_and_ingest_author` | from |
| 180 | `modules.female_backing.synth_female_line` | from |
| 199 | `app.core.hw_autodetect.detect` | from |
| 304 | `modules.track_templates.list_templates` | from |
| 318 | `time` | import |
| 334 | `modules.track_templates.delete_template` | from |
| 346 | `modules.track_templates.load_template` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 52 | `__init__` | 32 | 0 | ❌ |
| 86 | `_refresh_authors` | 9 | 2 | ❌ |
| 97 | `_on_scan` | 11 | 1 | ❌ |
| 110 | `_on_fetch` | 16 | 3 | ❌ |
| 128 | `selected_author` | 4 | 2 | ❌ |
| 138 | `__init__` | 29 | 0 | ❌ |
| 169 | `is_enabled` | 1 | 0 | ❌ |
| 172 | `placement` | 3 | 0 | ❌ |
| 177 | `_preview` | 8 | 1 | ❌ |
| 191 | `__init__` | 4 | 0 | ❌ |
| 197 | `refresh` | 16 | 1 | ❌ |
| 221 | `__init__` | 11 | 0 | ❌ |
| 234 | `set_report` | 37 | 3 | ❌ |
| 277 | `__init__` | 23 | 0 | ❌ |
| 302 | `_reload` | 25 | 2 | ❌ |
| 329 | `_delete` | 10 | 2 | ❌ |
| 341 | `selected_template` | 9 | 2 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 49 | `AuthorPickerPanel` | ❌ |
| 137 | `FemaleBackingPanel` | ❌ |
| 190 | `QualityBadge` | ❌ |
| 218 | `AutoQAResultPanel` | ❌ |
| 276 | `TemplateManagerDialog` | ❌ |

## Проблемы (детально, с цитатой кода)

### MISSING_CLASS_DOCSTRING — 5 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 49** — public class 'AuthorPickerPanel' без docstring

  ```
         47 | if PYSIDE_OK:
         48 | 
  >>>    49 |     class AuthorPickerPanel(QGroupBox):
         50 |         author_changed = Signal(str)
         51 | 
  ```

- **строка 137** — public class 'FemaleBackingPanel' без docstring

  ```
        135 |     # FemaleBackingPanel
        136 |     # ============================================================
  >>>   137 |     class FemaleBackingPanel(QGroupBox):
        138 |         def __init__(self, parent=None):
        139 |             super().__init__("Женский бэк-вокал (Silero v4 — Ksenia/Baya)", parent)
  ```

- **строка 190** — public class 'QualityBadge' без docstring

  ```
        188 |     # QualityBadge
        189 |     # ============================================================
  >>>   190 |     class QualityBadge(QLabel):
        191 |         def __init__(self, parent=None):
        192 |             super().__init__(parent)
  ```

- **строка 218** — public class 'AutoQAResultPanel' без docstring

  ```
        216 |     # AutoQAResultPanel
        217 |     # ============================================================
  >>>   218 |     class AutoQAResultPanel(QGroupBox):
        219 |         rebuild_requested = Signal(list)  # список targets
        220 | 
  ```

- **строка 276** — public class 'TemplateManagerDialog' без docstring

  ```
        274 |     # TemplateManagerDialog
        275 |     # ============================================================
  >>>   276 |     class TemplateManagerDialog(QDialog):
        277 |         def __init__(self, parent=None):
        278 |             super().__init__(parent)
  ```

### MISSING_DOCSTRING — 2 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 197** — public function 'refresh' без docstring

  ```
        195 |             self.refresh()
        196 | 
  >>>   197 |         def refresh(self):
        198 |             try:
        199 |                 from app.core.hw_autodetect import detect
  ```

- **строка 234** — public function 'set_report' без docstring

  ```
        232 |             self.lay.addWidget(self.actions_area, 1)
        233 | 
  >>>   234 |         def set_report(self, report: dict):
        235 |             for i in reversed(range(self.actions_lay.count())):
        236 |                 w = self.actions_lay.itemAt(i).widget()
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 17** — import 'annotations' не используется в теле файла

  ```
         15 | """
         16 | 
  >>>    17 | from __future__ import annotations
         18 | 
         19 | try:
  ```
