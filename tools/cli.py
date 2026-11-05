"""Minimal shared command-line contract for maintenance tools."""

from __future__ import annotations

import argparse
import sys


def help_or_error(description: str) -> bool:
    """Handle a no-option tool's CLI before it runs its workload.

    Returns ``False`` when invoked without arguments. ``--help``/``-h`` is
    served by argparse (exit 0); any other argument is rejected (exit 2).
    """
    if not sys.argv[1:]:
        return False
    parser = argparse.ArgumentParser(description=description)
    parser.parse_args()
    return True
