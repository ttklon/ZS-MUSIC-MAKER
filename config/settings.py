# -*- coding: utf-8 -*-
"""
ZS Music Maker — config/settings.py (v39.5, ШАГ 007 PLAN_v39)
========================================================================
Единый загрузчик конфигурации вместо разбросанных констант.

Порядок приоритета значения:
    1. переменная окружения (os.environ)
    2. строка в .env (корень проекта)
    3. дефолт из dataclass

Никакого python-dotenv — собственный минимальный парсер `KEY=VALUE`
(комментарии # и кавычки поддерживаются). .env.example остаётся шаблоном.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]


def _parse_dotenv(path: Path) -> dict[str, str]:
    """Минимальный парсер .env: KEY=VALUE, #комментарии, кавычки."""
    out: dict[str, str] = {}
    if not path.exists():
        return out
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k = k.strip()
            if not k:
                continue
            out[k] = v.strip().strip('"').strip("'")
    except OSError as e:  # noqa: BLE001
        print(f"[settings] cannot read {path}: {e}")
    return out


def _as_bool(value, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def _as_int(value, default: int) -> int:
    if value is None:
        return default
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def _as_float(value, default: float) -> float:
    if value is None:
        return default
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


@dataclass
class Settings:
    """Полный набор настроек приложения (все пути — от ROOT)."""

    root: Path = ROOT
    output_dir: Path = ROOT / "output"
    models_dir: Path = ROOT / "models"
    user_dir: Path = ROOT / "data"
    beats_dir: Path = ROOT / "output" / "beats"
    logs_dir: Path = ROOT / "output" / "logs"
    vault_dir: Path = ROOT / "voice_vault"
    vram_gb: float = 12.0
    ram_gb: float = 32.0
    cpu_threads: int = 40
    prefer_gpu: bool = True
    timeout_sec: int = 3600
    no_checkpoints: bool = False
    language: str = "ru"
    config_path: Path = ROOT / ".env"
    loaded_from_env: bool = False

    @classmethod
    def load(cls, env_path: Optional[Path] = None) -> "Settings":
        """Собирает Settings из .env + окружения (приоритет: env > .env > дефолт)."""
        env_path = env_path or ROOT / ".env"
        dot = _parse_dotenv(env_path)

        def get(key: str, default=None):
            return os.environ.get(key, dot.get(key, default))

        root = ROOT
        out_dir = Path(str(get("ZSMM_OUTPUT_DIR") or root / "output"))
        user_dir = Path(str(get("ZSMM_USER_DIR") or root / "data"))
        s = cls(
            root=root,
            output_dir=out_dir,
            models_dir=Path(str(get("ZSMM_MODELS_DIR") or root / "models")),
            user_dir=user_dir,
            beats_dir=Path(str(get("ZSMM_BEAT_OUTPUT_DIR") or out_dir / "beats")),
            logs_dir=Path(str(get("ZSMM_LOGS_DIR") or out_dir / "logs")),
            vault_dir=Path(str(get("ZSMM_VAULT_DIR") or root / "voice_vault")),
            vram_gb=_as_float(get("ZSMM_VRAM_GB"), 12.0),
            ram_gb=_as_float(get("ZSMM_RAM_GB"), 32.0),
            cpu_threads=_as_int(get("ZSMM_CPU_THREADS"), 40),
            prefer_gpu=_as_bool(get("ZSMM_PREFER_GPU"), True),
            timeout_sec=_as_int(get("ZSMM_TIMEOUT_SEC"), 3600),
            no_checkpoints=str(get("ZSMM_NO_CHECKPOINTS")) == "1",
            language=str(get("ZSMM_LANGUAGE") or "ru").lower().split("-", 1)[0],
            config_path=env_path,
            loaded_from_env=bool(dot) or any(
                k.startswith("ZSMM_") for k in os.environ
            ),
        )
        return s

    def dump(self) -> dict:
        """Плоский словарь для отчёта/health. Пути — относительно ROOT."""
        d = {
            "root": str(self.root),
            "output_dir": str(self.output_dir),
            "models_dir": str(self.models_dir),
            "user_dir": str(self.user_dir),
            "beats_dir": str(self.beats_dir),
            "logs_dir": str(self.logs_dir),
            "vault_dir": str(self.vault_dir),
            "vram_gb": self.vram_gb,
            "ram_gb": self.ram_gb,
            "cpu_threads": self.cpu_threads,
            "prefer_gpu": self.prefer_gpu,
            "timeout_sec": self.timeout_sec,
            "no_checkpoints": self.no_checkpoints,
            "language": self.language,
            "config_path": str(self.config_path),
            "loaded_from_env": self.loaded_from_env,
        }
        return d


# --- Singleton (ленивый; reset_settings для тестов) -------------------------
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-local settings snapshot until explicitly reset."""
    return Settings.load()


def reset_settings() -> None:
    """Сбрасывает кэш настроек (используется тестами)."""
    get_settings.cache_clear()
