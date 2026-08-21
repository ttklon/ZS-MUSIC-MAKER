# -*- coding: utf-8 -*-
"""ZS Music Maker — tests for app/core/font_utils (ШАГ 002)."""
from __future__ import annotations

from app.core import font_utils as F


def test_candidates_non_empty():
    cands = F.font_candidates(bold=True)
    assert isinstance(cands, list)
    assert cands  # хотя бы 1
    # никаких дублей
    assert len(cands) == len(set(cands))


def test_candidates_regular_variant():
    cands = F.font_candidates(bold=False)
    assert cands


def test_env_override(monkeypatch):
    monkeypatch.setenv("ZSMM_FONT_PATH", "/custom/font.ttf")
    cands = F.font_candidates(bold=True)
    assert cands[0] == "/custom/font.ttf"


def test_load_pil_font_returns_something():
    f = F.load_pil_font(24, bold=True)
    assert f is not None
