# -*- coding: utf-8 -*-
"""
ZS Music Maker — model_manager.py (GOD MODE)
========================================================================
Автоматическое управление нейросетевыми моделями.
Решает проблему "Модельного Голода" и "Уязвимой Десериализации".
"""

import os
import logging
from pathlib import Path
from app.core.security_utils import download_file, safe_hash
from app.core.logger import app_logger

# v34 FIX (P2.8): torch больше не импортируется на верхнем уровне.
# Раньше `import app.core.model_manager` (core-слой!) мгновенно падал на
# машине без torch — это роняло install.py (шаг 5) и весь core import-граф.
# torch нужен ТОЛЬКО для load_torch_model → ленивый импорт внутри метода.

class ModelManager:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parents[2] / "models"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        # Маппинг моделей и их источников (примеры)
        self.registry = {
            "whisper_tiny": {
                "url": "https://openaipublic.azureedge.net/main/whisper/models/6514702301534eab811cb7871f6610179f57213b63d17d07e318e0d12c61d2/tiny.pt",
                "path": "whisper/tiny.pt",
                "expected_hash": "6514702301534eab811cb7871f6610179f57213b63d17d07e318e0d12c61d2"
            }
        }

    def ensure_model(self, model_id: str) -> str:
        """Проверяет наличие модели и скачивает её при необходимости."""
        if model_id not in self.registry:
            app_logger.warning(f"Model {model_id} not in registry, assuming local path.")
            return str(self.base_dir / model_id)

        info = self.registry[model_id]
        target_path = self.base_dir / info["path"]
        
        if not target_path.exists():
            app_logger.info(f"Downloading model {model_id}...")
            if not download_file(info["url"], str(target_path)):
                raise RuntimeError(f"Failed to download model {model_id}")
        
        return str(target_path)

    def load_torch_model(self, model_id: str, map_location="cpu"):
        """Безопасная загрузка PyTorch модели (weights_only=True)."""
        try:
            import torch
        except ImportError as e:
            raise RuntimeError(
                "PyTorch не установлен — загрузка нейромоделей недоступна. "
                "Установите: pip install torch (или запустите install.py)"
            ) from e
        path = self.ensure_model(model_id)
        app_logger.info(f"Safely loading model: {model_id}")
        # B614 FIX: weights_only=True
        return torch.load(path, map_location=map_location, weights_only=True)

# Глобальный менеджер
models = ModelManager()
