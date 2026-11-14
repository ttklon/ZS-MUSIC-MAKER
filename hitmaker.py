#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hitmaker.py — Однострочный лаунчер фабрики хитов.

Полностью бесплатно, нероншно, как человек.

Примеры:
    python hitmaker.py                          # 1 случайный хит
    python hitmaker.py --count 5                # 5 хитов батчем
    python hitmaker.py --genre trap --theme "ночь, деньги, движ" --count 3
    python hitmaker.py --count 10 --evolve --min-score 68 --duration 90
    python hitmaker.py --seed 42 --genre drift_phonk  # детерминизм

Результат: output/hits/<project_id>/master.wav + hit_report.json
Документация: docs/HIT_FACTORY_PLAN.md
"""
from __future__ import annotations

from modules.hit_factory.generator import _cli

if __name__ == "__main__":
    raise SystemExit(_cli())
