# -*- coding: utf-8 -*-
"""
ZS Music Maker — app/core/font_utils.py (v39.4, ШАГ 002)
========================================================================
Единый источник TTF-fallback для PIL. Раньше пути к шрифтам были жёстко
зашиты в трёх местах (cover_art_gen, video_edit, cover_gen) с
C:\\Windows\\Fonts\\arialbd.ttf — на Linux всё падало на fallback default.

Теперь: единый список кандидатов (Linux/macOS/Windows) + опциональный
override через ZSMM_FONT_PATH / config/fonts.txt. Никаких hardcoded
C:\\ и /home/ubuntu в production-коде.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable, Optional

_ROOT = Path(__file__).resolve().parents[2]


def _config_font_candidates() -> Iterable[str]:
    """Читает config/fonts.txt если есть — по одному пути на строку."""
    cfg = _ROOT / "config" / "fonts.txt"
    if not cfg.exists():
        return []
    try:
        return [
            line.strip()
            for line in cfg.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
    except OSError as e:  # noqa: BLE001 — сообщаем причину и работаем без конфига
        print(f"[font_utils] cannot read {cfg}: {e}", file=sys.stderr)
        return []


def font_candidates(bold: bool = True) -> list[str]:
    """
    Возвращает упорядоченный список кандидатов TTF: env → config → OS-defaults.
    Пути к системным шрифтам — только через os.path.join / стандартные
    OS-локации, ничего hardcoded под конкретную машину пользователя.
    """
    env = os.environ.get("ZSMM_FONT_PATH", "").strip()
    result: list[str] = []
    if env:
        result.append(env)
    result.extend(_config_font_candidates())
    # Linux
    linux_bold = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    ]
    linux_reg = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    # macOS
    mac_bold = ["/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial Bold.ttf"]
    # Windows — вычисляем от %WINDIR% (не hardcoded в код)
    win_bold: list[str] = []
    win_reg: list[str] = []
    windir = os.environ.get("WINDIR") or os.environ.get("SystemRoot")
    if windir:
        fonts = os.path.join(windir, "Fonts")
        win_bold = [os.path.join(fonts, "arialbd.ttf"), os.path.join(fonts, "Arial Bold.ttf")]
        win_reg = [os.path.join(fonts, "arial.ttf")]

    # PIL / bundled name fallback (PIL сам ищет в системных путях)
    named = ["arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"]

    if bold:
        result += linux_bold + mac_bold + win_bold + named
    else:
        result += linux_reg + [
            "/System/Library/Fonts/Helvetica.ttc",
        ] + win_reg + ["arial.ttf", "DejaVuSans.ttf"]
    # dedup preserve order
    seen: set[str] = set()
    uniq: list[str] = []
    for p in result:
        if p and p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq


def load_pil_font(size: int, bold: bool = True):
    """
    Возвращает PIL ImageFont: пробует all-candidates, честно логирует
    неожиданные ошибки в stderr, штатное отсутствие шрифта — тихо.
    Никогда не бросает — на самый крайний случай возвращает load_default().
    """
    try:
        from PIL import ImageFont
    except ImportError as e:
        raise RuntimeError(f"Pillow (PIL) не установлен: {e}") from e
    for cand in font_candidates(bold=bold):
        try:
            return ImageFont.truetype(cand, size)
        except OSError:
            continue  # штатное отсутствие
        except Exception as e:  # noqa: BLE001
            print(f"[font_utils] TTF load error {cand}: {e}", file=sys.stderr)
            continue
    return ImageFont.load_default()


def first_available_font_path(bold: bool = True) -> Optional[str]:
    """Возвращает первый существующий путь из кандидатов или None."""
    for cand in font_candidates(bold=bold):
        try:
            if cand and os.path.exists(cand):
                return cand
        except OSError:
            continue
    return None
