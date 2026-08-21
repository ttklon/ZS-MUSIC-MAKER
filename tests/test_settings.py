# -*- coding: utf-8 -*-
"""ZS Music Maker — tests for config/settings (ШАГ 007)."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from config import settings as S


@pytest.fixture(autouse=True)
def _clean_settings():
    S.reset_settings()
    yield
    S.reset_settings()


def test_defaults_sane():
    s = S.Settings.load()
    d = s.dump()
    assert s.vram_gb == 12.0
    assert s.ram_gb == 32.0
    assert s.timeout_sec == 3600
    assert d["root"] == str(S.ROOT)
    assert d["config_path"] == str(S.ROOT / ".env")


def test_env_override(monkeypatch):
    monkeypatch.setenv("ZSMM_VRAM_GB", "16")
    monkeypatch.setenv("ZSMM_RAM_GB", "64")
    monkeypatch.setenv("ZSMM_TIMEOUT_SEC", "7200")
    monkeypatch.setenv("ZSMM_PREFER_GPU", "0")
    s = S.Settings.load()
    assert s.vram_gb == 16.0
    assert s.ram_gb == 64.0
    assert s.timeout_sec == 7200
    assert s.prefer_gpu is False
    assert s.loaded_from_env is True


def test_dotenv_file_override(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# test\nZSMM_VRAM_GB=20\nZSMM_BEAT_OUTPUT_DIR=/tmp/custom_beats\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("ZSMM_VRAM_GB", raising=False)
    s = S.Settings.load(env_path=env_file)
    assert s.vram_gb == 20.0
    assert str(s.beats_dir) == "/tmp/custom_beats"


def test_os_environ_beats_dotenv(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("ZSMM_VRAM_GB=8\n", encoding="utf-8")
    monkeypatch.setenv("ZSMM_VRAM_GB", "24")  # env сильнее .env
    s = S.Settings.load(env_path=env_file)
    assert s.vram_gb == 24.0


def test_get_settings_singleton():
    a = S.get_settings()
    b = S.get_settings()
    assert a is b


def test_invalid_values_fall_back_to_default(monkeypatch):
    monkeypatch.setenv("ZSMM_VRAM_GB", "not-a-number")
    s = S.Settings.load()
    assert s.vram_gb == 12.0
