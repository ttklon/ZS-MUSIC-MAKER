# ПОСТРОЧНЫЙ ЛИСТИНГ: `tests/test_settings.py`

**Всего строк:** 72

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 25 | 34.7 |
| blank | 17 | 23.6 |
| stmt | 15 | 20.8 |
| def | 7 | 9.7 |
| import | 5 | 6.9 |
| comment | 1 | 1.4 |
| docstring | 1 | 1.4 |
| decorator | 1 | 1.4 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """ZS Music Maker — tests for config/settings (ШАГ 007)."""
    3 [import    ] from __future__ import annotations
    4 [blank     ] 
    5 [import    ] import os
    6 [import    ] from pathlib import Path
    7 [blank     ] 
    8 [import    ] import pytest
    9 [blank     ] 
   10 [import    ] from config import settings as S
   11 [blank     ] 
   12 [blank     ] 
   13 [decorator ] @pytest.fixture(autouse=True)
   14 [def       ] def _clean_settings():
   15 [code      ]     S.reset_settings()
   16 [code      ]     yield
   17 [code      ]     S.reset_settings()
   18 [blank     ] 
   19 [blank     ] 
   20 [def       ] def test_defaults_sane():
   21 [code      ]     s = S.Settings.load()
   22 [code      ]     d = s.dump()
   23 [stmt      ]     assert s.vram_gb == 12.0
   24 [stmt      ]     assert s.ram_gb == 32.0
   25 [stmt      ]     assert s.timeout_sec == 3600
   26 [stmt      ]     assert d["root"] == str(S.ROOT)
   27 [stmt      ]     assert d["config_path"] == str(S.ROOT / ".env")
   28 [blank     ] 
   29 [blank     ] 
   30 [def       ] def test_env_override(monkeypatch):
   31 [code      ]     monkeypatch.setenv("ZSMM_VRAM_GB", "16")
   32 [code      ]     monkeypatch.setenv("ZSMM_RAM_GB", "64")
   33 [code      ]     monkeypatch.setenv("ZSMM_TIMEOUT_SEC", "7200")
   34 [code      ]     monkeypatch.setenv("ZSMM_PREFER_GPU", "0")
   35 [code      ]     s = S.Settings.load()
   36 [stmt      ]     assert s.vram_gb == 16.0
   37 [stmt      ]     assert s.ram_gb == 64.0
   38 [stmt      ]     assert s.timeout_sec == 7200
   39 [stmt      ]     assert s.prefer_gpu is False
   40 [stmt      ]     assert s.loaded_from_env is True
   41 [blank     ] 
   42 [blank     ] 
   43 [def       ] def test_dotenv_file_override(tmp_path, monkeypatch):
   44 [code      ]     env_file = tmp_path / ".env"
   45 [code      ]     env_file.write_text(
   46 [code      ]         "# test\nZSMM_VRAM_GB=20\nZSMM_BEAT_OUTPUT_DIR=/tmp/custom_beats\n",
   47 [code      ]         encoding="utf-8",
   48 [code      ]     )
   49 [code      ]     monkeypatch.delenv("ZSMM_VRAM_GB", raising=False)
   50 [code      ]     s = S.Settings.load(env_path=env_file)
   51 [stmt      ]     assert s.vram_gb == 20.0
   52 [stmt      ]     assert str(s.beats_dir) == "/tmp/custom_beats"
   53 [blank     ] 
   54 [blank     ] 
   55 [def       ] def test_os_environ_beats_dotenv(monkeypatch, tmp_path):
   56 [code      ]     env_file = tmp_path / ".env"
   57 [code      ]     env_file.write_text("ZSMM_VRAM_GB=8\n", encoding="utf-8")
   58 [code      ]     monkeypatch.setenv("ZSMM_VRAM_GB", "24")  # env сильнее .env
   59 [code      ]     s = S.Settings.load(env_path=env_file)
   60 [stmt      ]     assert s.vram_gb == 24.0
   61 [blank     ] 
   62 [blank     ] 
   63 [def       ] def test_get_settings_singleton():
   64 [code      ]     a = S.get_settings()
   65 [code      ]     b = S.get_settings()
   66 [stmt      ]     assert a is b
   67 [blank     ] 
   68 [blank     ] 
   69 [def       ] def test_invalid_values_fall_back_to_default(monkeypatch):
   70 [code      ]     monkeypatch.setenv("ZSMM_VRAM_GB", "not-a-number")
   71 [code      ]     s = S.Settings.load()
   72 [stmt      ]     assert s.vram_gb == 12.0
```