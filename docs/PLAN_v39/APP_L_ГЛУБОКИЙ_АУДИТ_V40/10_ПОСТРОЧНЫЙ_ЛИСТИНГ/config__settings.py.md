# ПОСТРОЧНЫЙ ЛИСТИНГ: `config/settings.py`

**Всего строк:** 158

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 70 | 44.3 |
| blank | 25 | 15.8 |
| docstring | 16 | 10.1 |
| return | 14 | 8.9 |
| def | 9 | 5.7 |
| branch | 7 | 4.4 |
| try_block | 6 | 3.8 |
| import | 5 | 3.2 |
| comment | 2 | 1.3 |
| decorator | 2 | 1.3 |
| loop | 1 | 0.6 |
| class | 1 | 0.6 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """
    3 [docstring ] ZS Music Maker — config/settings.py (v39.5, ШАГ 007 PLAN_v39)
    4 [docstring ] ========================================================================
    5 [docstring ] Единый загрузчик конфигурации вместо разбросанных констант.
    6 [blank     ] 
    7 [docstring ] Порядок приоритета значения:
    8 [docstring ]     1. переменная окружения (os.environ)
    9 [docstring ]     2. строка в .env (корень проекта)
   10 [docstring ]     3. дефолт из dataclass
   11 [blank     ] 
   12 [docstring ] Никакого python-dotenv — собственный минимальный парсер `KEY=VALUE`
   13 [docstring ] (комментарии # и кавычки поддерживаются). .env.example остаётся шаблоном.
   14 [docstring ] """
   15 [import    ] from __future__ import annotations
   16 [blank     ] 
   17 [import    ] import os
   18 [import    ] from dataclasses import dataclass
   19 [import    ] from pathlib import Path
   20 [import    ] from typing import Optional
   21 [blank     ] 
   22 [code      ] ROOT = Path(__file__).resolve().parents[1]
   23 [blank     ] 
   24 [blank     ] 
   25 [def       ] def _parse_dotenv(path: Path) -> dict[str, str]:
   26 [docstring ]     """Минимальный парсер .env: KEY=VALUE, #комментарии, кавычки."""
   27 [code      ]     out: dict[str, str] = {}
   28 [branch    ]     if not path.exists():
   29 [return    ]         return out
   30 [try_block ]     try:
   31 [loop      ]         for raw in path.read_text(encoding="utf-8").splitlines():
   32 [code      ]             line = raw.strip()
   33 [branch    ]             if not line or line.startswith("#") or "=" not in line:
   34 [code      ]                 continue
   35 [code      ]             k, _, v = line.partition("=")
   36 [code      ]             k = k.strip()
   37 [branch    ]             if not k:
   38 [code      ]                 continue
   39 [code      ]             out[k] = v.strip().strip('"').strip("'")
   40 [try_block ]     except OSError as e:  # noqa: BLE001
   41 [code      ]         print(f"[settings] cannot read {path}: {e}")
   42 [return    ]     return out
   43 [blank     ] 
   44 [blank     ] 
   45 [def       ] def _as_bool(value, default: bool = False) -> bool:
   46 [branch    ]     if value is None:
   47 [return    ]         return default
   48 [return    ]     return str(value).strip().lower() in ("1", "true", "yes", "on")
   49 [blank     ] 
   50 [blank     ] 
   51 [def       ] def _as_int(value, default: int) -> int:
   52 [branch    ]     if value is None:
   53 [return    ]         return default
   54 [try_block ]     try:
   55 [return    ]         return int(float(str(value).strip()))
   56 [try_block ]     except (TypeError, ValueError):
   57 [return    ]         return default
   58 [blank     ] 
   59 [blank     ] 
   60 [def       ] def _as_float(value, default: float) -> float:
   61 [branch    ]     if value is None:
   62 [return    ]         return default
   63 [try_block ]     try:
   64 [return    ]         return float(str(value).strip())
   65 [try_block ]     except (TypeError, ValueError):
   66 [return    ]         return default
   67 [blank     ] 
   68 [blank     ] 
   69 [decorator ] @dataclass
   70 [class     ] class Settings:
   71 [docstring ]     """Полный набор настроек приложения (все пути — от ROOT)."""
   72 [blank     ] 
   73 [code      ]     root: Path = ROOT
   74 [code      ]     output_dir: Path = ROOT / "output"
   75 [code      ]     models_dir: Path = ROOT / "models"
   76 [code      ]     user_dir: Path = ROOT / "data"
   77 [code      ]     beats_dir: Path = ROOT / "output" / "beats"
   78 [code      ]     logs_dir: Path = ROOT / "output" / "logs"
   79 [code      ]     vault_dir: Path = ROOT / "voice_vault"
   80 [code      ]     vram_gb: float = 12.0
   81 [code      ]     ram_gb: float = 32.0
   82 [code      ]     cpu_threads: int = 40
   83 [code      ]     prefer_gpu: bool = True
   84 [code      ]     timeout_sec: int = 3600
   85 [code      ]     no_checkpoints: bool = False
   86 [code      ]     config_path: Path = ROOT / ".env"
   87 [code      ]     loaded_from_env: bool = False
   88 [blank     ] 
   89 [decorator ]     @classmethod
   90 [def       ]     def load(cls, env_path: Optional[Path] = None) -> "Settings":
   91 [docstring ]         """Собирает Settings из .env + окружения (приоритет: env > .env > дефолт)."""
   92 [code      ]         env_path = env_path or ROOT / ".env"
   93 [code      ]         dot = _parse_dotenv(env_path)
   94 [blank     ] 
   95 [def       ]         def get(key: str, default=None):
   96 [return    ]             return os.environ.get(key, dot.get(key, default))
   97 [blank     ] 
   98 [code      ]         root = ROOT
   99 [code      ]         out_dir = Path(str(get("ZSMM_OUTPUT_DIR") or root / "output"))
  100 [code      ]         user_dir = Path(str(get("ZSMM_USER_DIR") or root / "data"))
  101 [code      ]         s = cls(
  102 [code      ]             root=root,
  103 [code      ]             output_dir=out_dir,
  104 [code      ]             models_dir=Path(str(get("ZSMM_MODELS_DIR") or root / "models")),
  105 [code      ]             user_dir=user_dir,
  106 [code      ]             beats_dir=Path(str(get("ZSMM_BEAT_OUTPUT_DIR") or out_dir / "beats")),
  107 [code      ]             logs_dir=Path(str(get("ZSMM_LOGS_DIR") or out_dir / "logs")),
  108 [code      ]             vault_dir=Path(str(get("ZSMM_VAULT_DIR") or root / "voice_vault")),
  109 [code      ]             vram_gb=_as_float(get("ZSMM_VRAM_GB"), 12.0),
  110 [code      ]             ram_gb=_as_float(get("ZSMM_RAM_GB"), 32.0),
  111 [code      ]             cpu_threads=_as_int(get("ZSMM_CPU_THREADS"), 40),
  112 [code      ]             prefer_gpu=_as_bool(get("ZSMM_PREFER_GPU"), True),
  113 [code      ]             timeout_sec=_as_int(get("ZSMM_TIMEOUT_SEC"), 3600),
  114 [code      ]             no_checkpoints=str(get("ZSMM_NO_CHECKPOINTS")) == "1",
  115 [code      ]             config_path=env_path,
  116 [code      ]             loaded_from_env=bool(dot) or any(
  117 [code      ]                 k.startswith("ZSMM_") for k in os.environ
  118 [code      ]             ),
  119 [code      ]         )
  120 [return    ]         return s
  121 [blank     ] 
  122 [def       ]     def dump(self) -> dict:
  123 [docstring ]         """Плоский словарь для отчёта/health. Пути — относительно ROOT."""
  124 [code      ]         d = {
  125 [code      ]             "root": str(self.root),
  126 [code      ]             "output_dir": str(self.output_dir),
  127 [code      ]             "models_dir": str(self.models_dir),
  128 [code      ]             "user_dir": str(self.user_dir),
  129 [code      ]             "beats_dir": str(self.beats_dir),
  130 [code      ]             "logs_dir": str(self.logs_dir),
  131 [code      ]             "vault_dir": str(self.vault_dir),
  132 [code      ]             "vram_gb": self.vram_gb,
  133 [code      ]             "ram_gb": self.ram_gb,
  134 [code      ]             "cpu_threads": self.cpu_threads,
  135 [code      ]             "prefer_gpu": self.prefer_gpu,
  136 [code      ]             "timeout_sec": self.timeout_sec,
  137 [code      ]             "no_checkpoints": self.no_checkpoints,
  138 [code      ]             "config_path": str(self.config_path),
  139 [code      ]             "loaded_from_env": self.loaded_from_env,
  140 [code      ]         }
  141 [return    ]         return d
  142 [blank     ] 
  143 [blank     ] 
  144 [comment   ] # --- Singleton (ленивый; reset_settings для тестов) -------------------------
  145 [code      ] _settings: Optional[Settings] = None
  146 [blank     ] 
  147 [blank     ] 
  148 [def       ] def get_settings() -> Settings:
  149 [code      ]     global _settings
  150 [branch    ]     if _settings is None:
  151 [code      ]         _settings = Settings.load()
  152 [return    ]     return _settings
  153 [blank     ] 
  154 [blank     ] 
  155 [def       ] def reset_settings() -> None:
  156 [docstring ]     """Сбрасывает кэш настроек (используется тестами)."""
  157 [code      ]     global _settings
  158 [code      ]     _settings = None
```