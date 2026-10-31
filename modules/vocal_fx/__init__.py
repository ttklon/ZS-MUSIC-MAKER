# -*- coding: utf-8 -*-
"""
modules/vocal_fx — вокальные эффекты (double-tracking + delay throw).

Классические студийные приёмы на честном DSP (numpy + soundfile):

  * `apply_vocal_double` — детюн ±8 центов и микро-растяжение, тихо под основой;
  * `apply_delay_throw`  — эхо-бросок на конце фразы, заполняет паузу;
  * `process_vocal`      — clean → double → throw → `{ok, path, stages, ...}`;
  * `capability_report`  — доступен ли DSP на этой машине.

Раскладка: `dsp` (примитивы), `double`, `throw`, `pipeline` (склейка).
"""

from modules.vocal_fx.double import VocalFxResult, apply_vocal_double  # noqa: F401
from modules.vocal_fx.pipeline import capability_report, process_vocal  # noqa: F401
from modules.vocal_fx.throw import apply_delay_throw  # noqa: F401

__all__ = [
    "VocalFxResult",
    "apply_delay_throw",
    "apply_vocal_double",
    "capability_report",
    "process_vocal",
]
