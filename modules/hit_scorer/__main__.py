# -*- coding: utf-8 -*-
"""CLI: `python -m modules.hit_scorer <master.wav> [out.json]`."""

from __future__ import annotations

import json
import sys

from modules.hit_scorer import score_track


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print("usage: python -m modules.hit_scorer <master.wav> [out.json]")
        return 1
    report = score_track(args[0], out_json=args[1] if len(args) > 1 else None)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
