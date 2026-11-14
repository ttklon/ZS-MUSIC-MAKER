# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller-сборка ZS Music Maker (Windows 11, onedir по умолчанию).

Что важно и почему именно так:

* **onedir, а не onefile.** План требовал onefile, но onefile каждый запуск
  распаковывает ~200 МБ во временную папку: старт «< 5 c» на HDD недостижим, а
  антивирус Windows каждый раз проверяет новый файл. onedir стартует за секунды
  и обновляется копированием файлов. Если нужен именно один файл — соберите
  с `--onefile` вручную, spec это допускает флагом ZSMM_ONEFILE=1.
* **console=False** для сборки без окна консоли; журналы при этом всё равно
  пишутся в `%LOCALAPPDATA%\\ZS Music Maker\\logs` (см. app/core/logger.py).
* **Данные проекта** (`data/`, `version.json`, `scripts/`, `docs/`) копируются
  явно: без них программа запустится, но жанровые пресеты и промпты пропадут.
* **Скрытые импорты** перечислены вручную: PySide6 и librosa тянут плагины,
  которые анализатор импортов не видит.

Сборка: `scripts\\build_exe.cmd` (Windows) или
`python -m PyInstaller packaging/zsmm.spec --noconfirm`.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(SPECPATH).resolve().parent  # noqa: F821 - SPECPATH задаёт PyInstaller
sys.path.insert(0, str(ROOT))

ONEFILE = os.environ.get("ZSMM_ONEFILE") == "1"
ICON = ROOT / "assets" / "app.ico"
ICON_PATH = str(ICON) if ICON.exists() else None

datas = [
    (str(ROOT / "data"), "data"),
    (str(ROOT / "docs"), "docs"),
    (str(ROOT / "scripts"), "scripts"),
    (str(ROOT / "version.json"), "."),
    (str(ROOT / "VERSION"), "."),
    (str(ROOT / "INSTALL.md"), "."),
    (str(ROOT / "LICENSE"), "."),
]

hiddenimports = [
    "soundfile",
    "sounddevice",
    "scipy.signal",
    "scipy.ndimage",
    "librosa",
    "pyloudnorm",
    "pedalboard",
    "PIL.Image",
    "PIL.ImageDraw",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "app.gui.wizard",
    "modules.genre_engine",
    "modules.mastering",
    "modules.anti_neuro",
]

excludes = [
    "torch",
    "torchaudio",
    "audiocraft",
    "transformers",
    "diffusers",
    "demucs",
    "TTS",
    "bark",
    "gradio",
    "matplotlib",
    "tkinter",
    "IPython",
]

analysis = Analysis(  # noqa: F821 - имена PyInstaller доступны только в spec
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(analysis.pure)  # noqa: F821

if ONEFILE:
    exe = EXE(  # noqa: F821
        pyz,
        analysis.scripts,
        analysis.binaries,
        analysis.datas,
        name="ZS Music Maker",
        console=False,
        icon=ICON_PATH,
        upx=False,
    )
else:
    exe = EXE(  # noqa: F821
        pyz,
        analysis.scripts,
        [],
        exclude_binaries=True,
        name="ZS Music Maker",
        console=False,
        icon=ICON_PATH,
        upx=False,
    )
    collect = COLLECT(  # noqa: F821
        exe,
        analysis.binaries,
        analysis.datas,
        strip=False,
        upx=False,
        name="ZS Music Maker",
    )
