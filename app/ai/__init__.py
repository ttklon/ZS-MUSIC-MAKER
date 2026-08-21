# -*- coding: utf-8 -*-
"""ZS Music Maker - app/ai package (v38 AI CORE)
Единый AI-слой: все модули идут через registry + SequentialAIRunner."""
from app.ai.registry import registry, MODEL_REGISTRY, HardwareBudget  # noqa: F401
from app.ai.sequential_runner import SequentialAIRunner, AIStage  # noqa: F401
