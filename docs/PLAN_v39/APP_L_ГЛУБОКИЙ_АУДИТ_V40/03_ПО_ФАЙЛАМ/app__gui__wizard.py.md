# АУДИТ ФАЙЛА: `app/gui/wizard.py`

**LOC:** 1042  |  **Размер:** 40064 байт  |  **Проблем:** 29  |  **Risk score:** 9

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 16 | `__future__.annotations` | from |
| 18 | `os` | import |
| 19 | `sys` | import |
| 20 | `threading` | import |
| 21 | `time` | import |
| 22 | `webbrowser` | import |
| 23 | `pathlib.Path` | from |
| 25 | `PySide6.QtCore.Qt` | from |
| 25 | `PySide6.QtCore.QTimer` | from |
| 26 | `PySide6.QtGui.QAction` | from |
| 26 | `PySide6.QtGui.QDragEnterEvent` | from |
| 26 | `PySide6.QtGui.QDropEvent` | from |
| 26 | `PySide6.QtGui.QKeySequence` | from |
| 26 | `PySide6.QtGui.QShortcut` | from |
| 33 | `PySide6.QtWidgets.QCheckBox` | from |
| 33 | `PySide6.QtWidgets.QComboBox` | from |
| 33 | `PySide6.QtWidgets.QFileDialog` | from |
| 33 | `PySide6.QtWidgets.QFrame` | from |
| 33 | `PySide6.QtWidgets.QGroupBox` | from |
| 33 | `PySide6.QtWidgets.QHBoxLayout` | from |
| 33 | `PySide6.QtWidgets.QInputDialog` | from |
| 33 | `PySide6.QtWidgets.QLabel` | from |
| 33 | `PySide6.QtWidgets.QLineEdit` | from |
| 33 | `PySide6.QtWidgets.QListWidget` | from |
| 33 | `PySide6.QtWidgets.QMainWindow` | from |
| 33 | `PySide6.QtWidgets.QMessageBox` | from |
| 33 | `PySide6.QtWidgets.QProgressBar` | from |
| 33 | `PySide6.QtWidgets.QPushButton` | from |
| 33 | `PySide6.QtWidgets.QSlider` | from |
| 33 | `PySide6.QtWidgets.QSpinBox` | from |
| 33 | `PySide6.QtWidgets.QSplitter` | from |
| 33 | `PySide6.QtWidgets.QStackedWidget` | from |
| 33 | `PySide6.QtWidgets.QTextEdit` | from |
| 33 | `PySide6.QtWidgets.QVBoxLayout` | from |
| 33 | `PySide6.QtWidgets.QWidget` | from |
| 131 | `modules.user_profile.get_artist_name` | from |
| 139 | `modules.user_profile.set_artist_name` | from |
| 383 | `agents.sample_hunter` | from |
| 502 | `modules.voice_convert.vault_summary` | from |
| 528 | `modules.voice_convert.train_rvc_model` | from |
| 543 | `modules.voice_convert.get_training_status` | from |
| 954 | `app.gui.onboarding.maybe_show_onboarding` | from |
| 964 | `app.gui.onboarding.show_help_tour` | from |
| 826 | `webbrowser` | import |
| 827 | `pathlib.Path` | from |
| 1027 | `main` | import |
| 1034 | `runpy` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 64 | `H1` | 3 | 0 | ❌ |
| 70 | `H2` | 3 | 0 | ❌ |
| 76 | `DIM` | 5 | 0 | ❌ |
| 84 | `HR` | 4 | 0 | ❌ |
| 92 | `__init__` | 5 | 0 | ❌ |
| 99 | `enter` | 1 | 0 | ❌ |
| 102 | `commit` | 1 | 0 | ❌ |
| 105 | `help_text` | 1 | 0 | ❌ |
| 113 | `__init__` | 14 | 0 | ❌ |
| 129 | `enter` | 6 | 1 | ❌ |
| 137 | `commit` | 7 | 3 | ❌ |
| 146 | `help_text` | 1 | 0 | ❌ |
| 154 | `__init__` | 48 | 0 | ❌ |
| 204 | `dragEnterEvent` | 2 | 1 | ❌ |
| 208 | `dropEvent` | 4 | 3 | ❌ |
| 214 | `pick_files` | 5 | 1 | ❌ |
| 221 | `commit` | 5 | 1 | ❌ |
| 228 | `help_text` | 5 | 0 | ❌ |
| 240 | `__init__` | 56 | 1 | ❌ |
| 298 | `commit` | 21 | 0 | ❌ |
| 321 | `help_text` | 5 | 0 | ❌ |
| 333 | `__init__` | 46 | 0 | ❌ |
| 381 | `search` | 19 | 3 | ❌ |
| 402 | `commit` | 3 | 0 | ❌ |
| 407 | `help_text` | 1 | 0 | ❌ |
| 415 | `__init__` | 26 | 0 | ❌ |
| 443 | `commit` | 5 | 0 | ❌ |
| 450 | `help_text` | 1 | 0 | ❌ |
| 458 | `__init__` | 40 | 0 | ❌ |
| 500 | `enter` | 12 | 2 | ❌ |
| 514 | `open_karaoke` | 10 | 1 | ❌ |
| 526 | `train_rvc` | 13 | 1 | ❌ |
| 541 | `refresh_status` | 13 | 2 | ❌ |
| 556 | `commit` | 2 | 0 | ❌ |
| 560 | `help_text` | 5 | 0 | ❌ |
| 572 | `__init__` | 32 | 0 | ❌ |
| 606 | `commit` | 5 | 1 | ❌ |
| 613 | `help_text` | 1 | 0 | ❌ |
| 621 | `__init__` | 40 | 0 | ❌ |
| 663 | `start` | 11 | 2 | ❌ |
| 676 | `start_batch` | 24 | 3 | ❌ |
| 702 | `tick` | 37 | 8 | ❌ |
| 741 | `commit` | 1 | 0 | ❌ |
| 744 | `help_text` | 4 | 0 | ❌ |
| 755 | `__init__` | 38 | 0 | ❌ |
| 795 | `show_result` | 21 | 4 | ❌ |
| 818 | `open_folder` | 12 | 3 | ❌ |
| 832 | `rebuild_full` | 4 | 1 | ❌ |
| 838 | `rebuild_part` | 10 | 2 | ❌ |
| 850 | `three_variants` | 14 | 2 | ❌ |
| 866 | `commit` | 1 | 0 | ❌ |
| 869 | `help_text` | 4 | 0 | ❌ |
| 880 | `__init__` | 66 | 1 | ❌ |
| 948 | `_crumb_text` | 2 | 0 | ❌ |
| 952 | `_maybe_onboarding` | 8 | 2 | ❌ |
| 962 | `_show_tour` | 6 | 1 | ❌ |
| 970 | `_about` | 9 | 0 | ❌ |
| 981 | `show_help` | 7 | 0 | ❌ |
| 990 | `back` | 4 | 1 | ❌ |
| 996 | `next` | 8 | 1 | ❌ |
| 1006 | `go_to_result` | 14 | 4 | ✅ |
| 1022 | `launch_gradio_expert` | 20 | 2 | ❌ |
| 1025 | `_run` | 13 | 2 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 91 | `StepBase` | ❌ |
| 112 | `StepArtist` | ❌ |
| 153 | `StepReferences` | ❌ |
| 239 | `StepPreset` | ❌ |
| 332 | `StepSamples` | ❌ |
| 414 | `StepLyrics` | ❌ |
| 457 | `StepVoice` | ❌ |
| 571 | `StepExpert` | ❌ |
| 620 | `StepRun` | ❌ |
| 754 | `StepResult` | ❌ |
| 879 | `Wizard` | ❌ |

## Проблемы (детально, с цитатой кода)

### MISSING_DOCSTRING — 12 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 298** — public function 'commit' без docstring

  ```
        296 |         self.root.addWidget(gb)
        297 | 
  >>>   298 |     def commit(self, recipe):
        299 |         keys = [
        300 |             None,
  ```

- **строка 381** — public function 'search' без docstring

  ```
        379 |         self.root.addLayout(opt)
        380 | 
  >>>   381 |     def search(self):
        382 |         try:
        383 |             from agents import sample_hunter
  ```

- **строка 500** — public function 'enter' без docstring

  ```
        498 |         self.timer.start(2000)
        499 | 
  >>>   500 |     def enter(self):
        501 |         try:
        502 |             from modules.voice_convert import vault_summary
  ```

- **строка 526** — public function 'train_rvc' без docstring

  ```
        524 |             QMessageBox.warning(self, "Караоке", f"Пока недоступно: {e}")
        525 | 
  >>>   526 |     def train_rvc(self, night: bool = False):
        527 |         try:
        528 |             from modules.voice_convert import train_rvc_model
  ```

- **строка 541** — public function 'refresh_status' без docstring

  ```
        539 |             QMessageBox.warning(self, "RVC", f"Ошибка запуска: {e}")
        540 | 
  >>>   541 |     def refresh_status(self):
        542 |         try:
        543 |             from modules.voice_convert import get_training_status
  ```

- **строка 663** — public function 'start' без docstring

  ```
        661 |         self.batch_tids = []
        662 | 
  >>>   663 |     def start(self):
        664 |         recipe = self.wizard.recipe
        665 |         if not recipe.get("references") and not recipe.get("preset"):
  ```

- **строка 676** — public function 'start_batch' без docstring

  ```
        674 |         self.btn_start.setEnabled(False)
        675 | 
  >>>   676 |     def start_batch(self):
        677 |         recipe = self.wizard.recipe
        678 |         if not recipe.get("preset") and not recipe.get("references"):
  ```

- **строка 702** — public function 'tick' без docstring

  ```
        700 |         self.queue_label.setText(f"Очередь: {len(self.batch_tids)} треков в работе")
        701 | 
  >>>   702 |     def tick(self):
        703 |         # обновляем очередь
        704 |         active = list(self.batch_tids) + (
  ```

- **строка 795** — public function 'show_result' без docstring

  ```
        793 |         self.current_job = None
        794 | 
  >>>   795 |     def show_result(self, job):
        796 |         self.current_job = job
        797 |         result = job.result or {}
  ```

- **строка 818** — public function 'open_folder' без docstring

  ```
        816 |             self.detector.setText("🧪 AI-детектор: пока не запускался")
        817 | 
  >>>   818 |     def open_folder(self):
        819 |         if not self.current_job:
        820 |             return
  ```

- **строка 850** — public function 'three_variants' без docstring

  ```
        848 |         QMessageBox.information(self, "Готово", f"«{item}» пойдёт заново в очередь.")
        849 | 
  >>>   850 |     def three_variants(self):
        851 |         if not self.current_job:
        852 |             return
  ```

- **строка 1022** — public function 'launch_gradio_expert' без docstring

  ```
       1020 |             self.log.warning(f"go_to_result failed: {e}")
       1021 | 
  >>>  1022 |     def launch_gradio_expert(self):
       1023 |         self.log.info("Ctrl+E → v5 Gradio")
       1024 | 
  ```

### MISSING_CLASS_DOCSTRING — 11 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 91** — public class 'StepBase' без docstring

  ```
         89 | 
         90 | 
  >>>    91 | class StepBase(QWidget):
         92 |     def __init__(self, wizard):
         93 |         super().__init__()
  ```

- **строка 112** — public class 'StepArtist' без docstring

  ```
        110 | # Шаг 0: имя артиста (только при первом запуске)
        111 | # ============================================================
  >>>   112 | class StepArtist(StepBase):
        113 |     def __init__(self, wizard):
        114 |         super().__init__(wizard)
  ```

- **строка 153** — public class 'StepReferences' без docstring

  ```
        151 | # Шаг 1: референсы + тема + длительность
        152 | # ============================================================
  >>>   153 | class StepReferences(StepBase):
        154 |     def __init__(self, wizard):
        155 |         super().__init__(wizard)
  ```

- **строка 239** — public class 'StepPreset' без docstring

  ```
        237 | # Шаг 2: стиль (пресет) + режим генерации + стенды
        238 | # ============================================================
  >>>   239 | class StepPreset(StepBase):
        240 |     def __init__(self, wizard):
        241 |         super().__init__(wizard)
  ```

- **строка 332** — public class 'StepSamples' без docstring

  ```
        330 | # Шаг 3: Sample Browser — split-view local vs online
        331 | # ============================================================
  >>>   332 | class StepSamples(StepBase):
        333 |     def __init__(self, wizard):
        334 |         super().__init__(wizard)
  ```

- **строка 414** — public class 'StepLyrics' без docstring

  ```
        412 | # Шаг 4: Текст (bilingual + user_lyrics_lines)
        413 | # ============================================================
  >>>   414 | class StepLyrics(StepBase):
        415 |     def __init__(self, wizard):
        416 |         super().__init__(wizard)
  ```

- **строка 457** — public class 'StepVoice' без docstring

  ```
        455 | # Шаг 5: Голос — ProVoice основной
        456 | # ============================================================
  >>>   457 | class StepVoice(StepBase):
        458 |     def __init__(self, wizard):
        459 |         super().__init__(wizard)
  ```

- **строка 571** — public class 'StepExpert' без docstring

  ```
        569 | # Шаг 6: Экспертные опции
        570 | # ============================================================
  >>>   571 | class StepExpert(StepBase):
        572 |     def __init__(self, wizard):
        573 |         super().__init__(wizard)
  ```

- **строка 620** — public class 'StepRun' без docstring

  ```
        618 | # Шаг 7: Запуск + очередь
        619 | # ============================================================
  >>>   620 | class StepRun(StepBase):
        621 |     def __init__(self, wizard):
        622 |         super().__init__(wizard)
  ```

- **строка 754** — public class 'StepResult' без docstring

  ```
        752 | # Шаг 8: Результат — 3 кнопки (Пересобрать / Переделать часть / 3 варианта)
        753 | # ============================================================
  >>>   754 | class StepResult(StepBase):
        755 |     def __init__(self, wizard):
        756 |         super().__init__(wizard)
  ```

- **строка 879** — public class 'Wizard' без docstring

  ```
        877 | # Wizard — главное окно
        878 | # ============================================================
  >>>   879 | class Wizard(QMainWindow):
        880 |     def __init__(self, orch, hw, log):
        881 |         super().__init__()
  ```

### SILENT_EXCEPT_PASS — 4 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 134** — except: pass — тихое подавление ошибок

  ```
        132 | 
        133 |             self.name.setText(get_artist_name())
  >>>   134 |         except Exception:
        135 |             pass
        136 | 
  ```

- **строка 142** — except: pass — тихое подавление ошибок

  ```
        140 | 
        141 |             set_artist_name(self.name.text().strip() or "ZSMM Artist")
  >>>   142 |         except Exception:
        143 |             pass
        144 |         recipe["artist_name"] = self.name.text().strip() or "ZSMM Artist"
  ```

- **строка 553** — except: pass — тихое подавление ошибок

  ```
        551 |                     f"[RVC training] {st}  |  {stage}  |  {int(prog*100)}%"
        552 |                 )
  >>>   553 |         except Exception:
        554 |             pass
        555 | 
  ```

- **строка 829** — except: pass — тихое подавление ошибок

  ```
        827 |                 from pathlib import Path
        828 |                 webbrowser.open(Path(p).absolute().as_uri())
  >>>   829 |         except Exception:
        830 |             pass
        831 | 
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 16** — import 'annotations' не используется в теле файла

  ```
         14 | """
         15 | 
  >>>    16 | from __future__ import annotations
         17 | 
         18 | import os
  ```

### BLOCKING_SLEEP — 1 шт. — 🟢 LOW
**Смысл:** time.sleep() без комментария/аргументации
**Fix:** Комментарий или await asyncio.sleep().

- **строка 1041** — time.sleep(...) без пояснения

  ```
       1039 | 
       1040 |         threading.Thread(target=_run, daemon=True).start()
  >>>  1041 |         time.sleep(2)
       1042 |         webbrowser.open("http://127.0.0.1:7860")
  ```
