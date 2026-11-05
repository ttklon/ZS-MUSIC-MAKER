# -*- coding: utf-8 -*-
"""`python -m modules.voice_recording` — печать отчёта о возможности записи."""

from __future__ import annotations

import json

from modules.voice_recording.capability import capability_report

if __name__ == "__main__":
    print(json.dumps(capability_report(), indent=2))
