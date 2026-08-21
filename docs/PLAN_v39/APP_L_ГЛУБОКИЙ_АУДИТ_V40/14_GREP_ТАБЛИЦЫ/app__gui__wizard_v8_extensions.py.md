# grep-таблицы `app/gui/wizard_v8_extensions.py`

## `import` — 12 совпадений
```
   17 | from __future__ import annotations
   20 |     from PySide6.QtCore import Qt, Signal
   21 |     from PySide6.QtWidgets import (
   88 |                 from modules.author_ref_lyrics import list_authors
   99 |                 from modules.author_ref_lyrics import scan_library
  117 |                 from modules.author_ref_lyrics import fetch_and_ingest_author
  180 |                 from modules.female_backing import synth_female_line
  199 |                 from app.core.hw_autodetect import detect
  304 |                 from modules.track_templates import list_templates
  318 |                 import time
  334 |                 from modules.track_templates import delete_template
  346 |                 from modules.track_templates import load_template
```

## `except` — 9 совпадений
```
   40 | except Exception:
   94 |             except Exception as e:
  107 |             except Exception as e:
  125 |             except Exception as e:
  184 |             except Exception as e:
  203 |             except Exception:
  307 |             except Exception:
  338 |             except Exception as e:
  349 |             except Exception:
```

## `try` — 9 совпадений
```
   19 | try:
   87 |             try:
   98 |             try:
  116 |             try:
  179 |             try:
  198 |             try:
  303 |             try:
  333 |             try:
  345 |             try:
```

## `def` — 17 совпадений
```
   52 |         def __init__(self, parent=None):
   86 |         def _refresh_authors(self):
   97 |         def _on_scan(self):
  110 |         def _on_fetch(self):
  128 |         def selected_author(self) -> str:
  138 |         def __init__(self, parent=None):
  169 |         def is_enabled(self) -> bool:
  172 |         def placement(self) -> str:
  177 |         def _preview(self):
  191 |         def __init__(self, parent=None):
  197 |         def refresh(self):
  221 |         def __init__(self, parent=None):
  234 |         def set_report(self, report: dict):
  277 |         def __init__(self, parent=None):
  302 |         def _reload(self):
  329 |         def _delete(self):
  341 |         def selected_template(self) -> dict | None:
```

## `class` — 5 совпадений
```
   49 |     class AuthorPickerPanel(QGroupBox):
  137 |     class FemaleBackingPanel(QGroupBox):
  190 |     class QualityBadge(QLabel):
  218 |     class AutoQAResultPanel(QGroupBox):
  276 |     class TemplateManagerDialog(QDialog):
```

## `return` — 9 совпадений
```
  114 |                 return
  131 |                 return ""
  132 |             return t.split("·")[0].strip()
  170 |             return self.chk_enable.isChecked()
  173 |             return {0: "chorus", 1: "chorus_adlibs", 2: "adlibs_only", 3: "everywhere"}[
  332 |                 return
  344 |                 return None
  348 |                 return load_template(self._ids[row])
  350 |                 return None
```

## `if` — 6 совпадений
```
   47 | if PYSIDE_OK:
  112 |             if not author or author.startswith("("):
  130 |             if not t or t.startswith("("):
  237 |                 if w:
  331 |             if row < 0:
  343 |             if row < 0:
```

## `for` — 4 совпадений
```
   92 |                 for a in list_authors():
  235 |             for i in reversed(range(self.actions_lay.count())):
  249 |             for a in report.get("actions", []):
  311 |             for r, t in enumerate(items):
```
