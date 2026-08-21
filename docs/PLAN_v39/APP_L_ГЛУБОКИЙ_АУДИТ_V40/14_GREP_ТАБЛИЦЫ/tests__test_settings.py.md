# grep-таблицы `tests/test_settings.py`

## `import` — 5 совпадений
```
    3 | from __future__ import annotations
    5 | import os
    6 | from pathlib import Path
    8 | import pytest
   10 | from config import settings as S
```

## `def` — 7 совпадений
```
   14 | def _clean_settings():
   20 | def test_defaults_sane():
   30 | def test_env_override(monkeypatch):
   43 | def test_dotenv_file_override(tmp_path, monkeypatch):
   55 | def test_os_environ_beats_dotenv(monkeypatch, tmp_path):
   63 | def test_get_settings_singleton():
   69 | def test_invalid_values_fall_back_to_default(monkeypatch):
```

## `assert` — 15 совпадений
```
   23 |     assert s.vram_gb == 12.0
   24 |     assert s.ram_gb == 32.0
   25 |     assert s.timeout_sec == 3600
   26 |     assert d["root"] == str(S.ROOT)
   27 |     assert d["config_path"] == str(S.ROOT / ".env")
   36 |     assert s.vram_gb == 16.0
   37 |     assert s.ram_gb == 64.0
   38 |     assert s.timeout_sec == 7200
   39 |     assert s.prefer_gpu is False
   40 |     assert s.loaded_from_env is True
   51 |     assert s.vram_gb == 20.0
   52 |     assert str(s.beats_dir) == "/tmp/custom_beats"
   60 |     assert s.vram_gb == 24.0
   66 |     assert a is b
   72 |     assert s.vram_gb == 12.0
```

## `path_home` — 2 совпадений
```
   46 |         "# test\nZSMM_VRAM_GB=20\nZSMM_BEAT_OUTPUT_DIR=/tmp/custom_beats\n",
   52 |     assert str(s.beats_dir) == "/tmp/custom_beats"
```
