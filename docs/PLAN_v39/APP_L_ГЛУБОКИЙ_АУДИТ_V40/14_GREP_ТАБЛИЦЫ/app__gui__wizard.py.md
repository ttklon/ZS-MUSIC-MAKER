# grep-таблицы `app/gui/wizard.py`

## `import` — 22 совпадений
```
   16 | from __future__ import annotations
   18 | import os
   19 | import sys
   20 | import threading
   21 | import time
   22 | import webbrowser
   23 | from pathlib import Path
   25 | from PySide6.QtCore import Qt, QTimer
   26 | from PySide6.QtGui import (
   33 | from PySide6.QtWidgets import (
  131 |             from modules.user_profile import get_artist_name
  139 |             from modules.user_profile import set_artist_name
  383 |             from agents import sample_hunter
  502 |             from modules.voice_convert import vault_summary
  528 |             from modules.voice_convert import train_rvc_model
  543 |             from modules.voice_convert import get_training_status
  826 |                 import webbrowser
  827 |                 from pathlib import Path
  954 |             from app.gui.onboarding import maybe_show_onboarding
  964 |             from app.gui.onboarding import show_help_tour
 1027 |                 import main as v5main
 1034 |                     import runpy
```

## `except` — 12 совпадений
```
  134 |         except Exception:
  142 |         except Exception:
  399 |         except Exception as e:
  511 |         except Exception as e:
  523 |         except Exception as e:
  538 |         except Exception as e:
  553 |         except Exception:
  829 |         except Exception:
  959 |         except Exception as e:
  967 |         except Exception as e:
 1019 |         except Exception as e:
 1037 |             except Exception as e:
```

## `try` — 12 совпадений
```
  130 |         try:
  138 |         try:
  382 |         try:
  501 |         try:
  515 |         try:
  527 |         try:
  542 |         try:
  822 |         try:
  953 |         try:
  963 |         try:
 1008 |         try:
 1026 |             try:
```

## `def` — 63 совпадений
```
   64 | def H1(text):
   70 | def H2(text):
   76 | def DIM(text):
   84 | def HR():
   92 |     def __init__(self, wizard):
   99 |     def enter(self):
  102 |     def commit(self, recipe: dict):
  105 |     def help_text(self) -> str:
  113 |     def __init__(self, wizard):
  129 |     def enter(self):
  137 |     def commit(self, recipe):
  146 |     def help_text(self):
  154 |     def __init__(self, wizard):
  204 |     def dragEnterEvent(self, e: QDragEnterEvent):
  208 |     def dropEvent(self, e: QDropEvent):
  214 |     def pick_files(self):
  221 |     def commit(self, recipe):
  228 |     def help_text(self):
  240 |     def __init__(self, wizard):
  298 |     def commit(self, recipe):
  321 |     def help_text(self):
  333 |     def __init__(self, wizard):
  381 |     def search(self):
  402 |     def commit(self, recipe):
  407 |     def help_text(self):
  415 |     def __init__(self, wizard):
  443 |     def commit(self, recipe):
  450 |     def help_text(self):
  458 |     def __init__(self, wizard):
  500 |     def enter(self):
  514 |     def open_karaoke(self):
  526 |     def train_rvc(self, night: bool = False):
  541 |     def refresh_status(self):
  556 |     def commit(self, recipe):
  560 |     def help_text(self):
  572 |     def __init__(self, wizard):
  606 |     def commit(self, recipe):
  613 |     def help_text(self):
  621 |     def __init__(self, wizard):
  663 |     def start(self):
  676 |     def start_batch(self):
  702 |     def tick(self):
  741 |     def commit(self, recipe):
  744 |     def help_text(self):
  755 |     def __init__(self, wizard):
  795 |     def show_result(self, job):
  818 |     def open_folder(self):
  832 |     def rebuild_full(self):
  838 |     def rebuild_part(self):
  850 |     def three_variants(self):
  866 |     def commit(self, recipe):
  869 |     def help_text(self):
  880 |     def __init__(self, orch, hw, log):
  948 |     def _crumb_text(self):
  952 |     def _maybe_onboarding(self):
  962 |     def _show_tour(self):
  970 |     def _about(self):
  981 |     def show_help(self):
  990 |     def back(self):
  996 |     def next(self):
 1006 |     def go_to_result(self, job):
 1022 |     def launch_gradio_expert(self):
 1025 |         def _run():
```

## `class` — 11 совпадений
```
   91 | class StepBase(QWidget):
  112 | class StepArtist(StepBase):
  153 | class StepReferences(StepBase):
  239 | class StepPreset(StepBase):
  332 | class StepSamples(StepBase):
  414 | class StepLyrics(StepBase):
  457 | class StepVoice(StepBase):
  571 | class StepExpert(StepBase):
  620 | class StepRun(StepBase):
  754 | class StepResult(StepBase):
  879 | class Wizard(QMainWindow):
```

## `return` — 23 совпадений
```
   67 |     return l
   73 |     return l
   81 |     return l
   88 |     return line
  106 |         return ""
  147 |         return "Артист-имя — то, под которым ты выпускаешь треки."
  229 |         return (
  322 |         return (
  408 |         return "Введи что ищешь и нажми «Найти». Двойной клик добавляет сэмпл в проект."
  451 |         return "Что впишешь в «Мои строчки» — 100% попадёт в текст. Это твоя мысль, не нейросети."
  561 |         return (
  614 |         return "Можно ничего не менять. Или Ctrl+E — старый Gradio v5 со всеми настройками."
  671 |             return
  682 |             return
  709 |             return
  745 |         return (
  820 |             return
  834 |             return
  844 |             return
  852 |             return
  870 |         return (
  950 |         return f"Шаг {i+1} / {len(self.steps)}"
 1015 |                 return
```

## `if` — 26 совпадений
```
  205 |         if e.mimeData().hasUrls():
  211 |             if p and p.lower().endswith((".mp3", ".wav", ".flac", ".m4a", ".ogg")):
  318 |             if w.isChecked()
  546 |             if s:
  665 |         if not recipe.get("references") and not recipe.get("preset"):
  678 |         if not recipe.get("preset") and not recipe.get("references"):
  708 |         if not active:
  713 |             if not j:
  716 |             if j.status in ("done", "error") and j == self.wizard.orch.jobs.get(
  719 |                 if j.status == "done":
  726 |                 if self.wizard.stack.currentIndex() == self.wizard.stack.indexOf(self):
  730 |         if active:
  734 |                     if self.wizard.orch.jobs.get(t)
  808 |         if ai.get("ok"):
  819 |         if not self.current_job:
  823 |             if sys.platform.startswith("win"):
  833 |         if not self.current_job:
  843 |         if not ok or not self.current_job:
  851 |         if not self.current_job:
  957 |             if shown:
  985 |             if hasattr(cur, "help_text")
  992 |         if i > 0:
 1000 |         if i < self.stack.count() - 1:
 1011 |                 if isinstance(s, StepResult):
 1014 |             if idx is None:
 1029 |                 if hasattr(v5main, "build_ui"):
```

## `for` — 12 совпадений
```
  209 |         for u in e.mimeData().urls():
  218 |         for f in files:
  293 |         for c in (self.chk_car, self.chk_club, self.chk_str):
  313 |             for k, w in [
  393 |             for it in r.get("local", []):
  395 |             for it in r.get("online", []):
  692 |         for t in themes:
  711 |         for tid in active:
  737 |                 for t in active
  854 |         for i in range(3):
  902 |         for s in self.steps:
 1010 |             for i, s in enumerate(self.steps):
```

## `sleep` — 1 совпадений
```
 1041 |         time.sleep(2)
```

## `open` — 2 совпадений
```
  828 |                 webbrowser.open(Path(p).absolute().as_uri())
 1042 |         webbrowser.open("http://127.0.0.1:7860")
```
