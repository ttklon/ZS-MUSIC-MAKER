# -*- coding: utf-8 -*-
"""app/ai/weights.py — локальная проверка весов до обращения к сети.

Модели в проекте грузятся лениво и, если весов нет, `get_pretrained` /
`from_pretrained` тихо идут в HuggingFace. На машине без интернета это
выглядит как «зависший рендер», а с интернетом — как скачивание на гигабайты,
о котором пользователь не просил.

Правило: перед загрузкой проверяем каталог `data/ai_models/<role>`. Нет весов
— `FileNotFoundError` с готовой командой. Скачивание разрешается только явной
переменной `ZSMM_ALLOW_MODEL_DOWNLOAD=1`.
"""

from __future__ import annotations

import os
from pathlib import Path

ALLOW_DOWNLOAD_ENV = "ZSMM_ALLOW_MODEL_DOWNLOAD"
_TRUE = ("1", "true", "yes", "on")
_WEIGHT_SUFFIXES = (
    ".bin", ".safetensors", ".pt", ".pth", ".ckpt", ".gguf", ".onnx", ".npz", ".model",
)


def download_allowed() -> bool:
    """Разрешена ли неявная загрузка весов (по умолчанию — нет)."""
    return os.environ.get(ALLOW_DOWNLOAD_ENV, "").strip().lower() in _TRUE


def weights_hint(role: str, models_dir: Path) -> str:
    """Готовая инструкция: что положить и куда, без «погугли сам»."""
    return (
        f"локальные веса для роли '{role}' не найдены в {Path(models_dir) / role}. "
        f"Положите файл модели в этот каталог или выполните "
        f"`python tools/pull_ai_models.py --role {role}`; "
        f"разрешить автоматическую загрузку: {ALLOW_DOWNLOAD_ENV}=1"
    )


def has_local_weights(role: str, models_dir: Path) -> bool:
    """Есть ли в каталоге роли хоть один файл весов."""
    folder = Path(models_dir) / role
    if not folder.is_dir():
        return False
    for path in folder.rglob("*"):
        if path.is_file() and (path.suffix.lower() in _WEIGHT_SUFFIXES or path.name.endswith(".json")):
            return True
    return False


def ensure_local_weights(role: str, models_dir: Path) -> Path | None:
    """Preflight перед сетевым вызовом загрузчика.

    Возвращает путь к каталогу весов, `None` — если весов нет, но загрузка
    разрешена пользователем. Иначе бросает `FileNotFoundError` с инструкцией.
    """
    folder = Path(models_dir) / role
    if folder.is_dir() and any(folder.iterdir()):
        return folder
    if download_allowed():
        return None
    raise FileNotFoundError(weights_hint(role, models_dir))
