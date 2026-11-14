# -*- coding: utf-8 -*-
"""
tools/hit_factory.py — CLI обёртка для фабрики хитов.

Использование:
    python -m tools.hit_factory --count 5 --genre trap
    python tools/hit_factory.py --count 5 --evolve --min-score 68
"""
from modules.hit_factory.generator import _cli  # noqa: F401

if __name__ == "__main__":
    raise SystemExit(_cli())
