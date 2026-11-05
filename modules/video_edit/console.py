# -*- coding: utf-8 -*-
"""
modules/video_edit/console.py — безопасный вывод для консолей Windows.
"""

from __future__ import annotations

import sys


def safe_print(msg: str) -> None:
    try:
        print(msg)
    except UnicodeEncodeError:
        sys.stdout.buffer.write((msg + "\n").encode("cp866", errors="replace"))
