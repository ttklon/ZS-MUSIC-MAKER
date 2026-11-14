# -*- coding: utf-8 -*-
"""
modules.hit_factory — Автономная фабрика хитов ZS Music Maker.

Бесплатно, нероншно, как человек. Тонкий эволюционный слой поверх
классического DSP-пайплайна (run_full_pipeline).

Публичный API:
    from modules.hit_factory import HitFactory, quick_hit
    hit = quick_hit(theme="лето, тачки, движ", genre="trap", seed=42)
    factory = HitFactory(min_score=68, evolve=True)
    batch = factory.make_batch(count=5)

CLI:
    python hitmaker.py --count 5
    python -m modules.hit_factory --count 5 --genre phonk
    python main.py --hit-factory --count 3
"""
from __future__ import annotations

from modules.hit_factory.generator import HitFactory, quick_hit

__all__ = ["HitFactory", "quick_hit"]
