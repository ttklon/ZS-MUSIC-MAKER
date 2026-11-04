"""Run pytest with a private Numba cache for this interpreter process."""
from __future__ import annotations

import sys

from app.core.numba_cache import isolated_numba_cache


def main() -> int:
    with isolated_numba_cache():
        import pytest
        return int(pytest.main(sys.argv[1:]))


if __name__ == "__main__":
    raise SystemExit(main())
