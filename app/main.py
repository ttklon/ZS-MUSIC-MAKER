# -*- coding: utf-8 -*-
"""Современная точка входа desktop-режима."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    import main as root_main
    return int(root_main.main() or 0)


if __name__ == "__main__":
    raise SystemExit(main())
