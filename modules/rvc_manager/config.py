# -*- coding: utf-8 -*-
"""
modules/rvc_manager/config.py — пути, состояние и известные AMD-форки RVC.

Здесь только расположение моделей/форков и чтение-запись `rvc_state.json`.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = ROOT / "models" / "rvc"
FORKS_DIR = ROOT / "models" / "rvc_forks"
STATE_FILE = ROOT / "models" / "rvc" / "rvc_state.json"
for _path in (MODELS_DIR, FORKS_DIR):
    _path.mkdir(parents=True, exist_ok=True)

# Известные AMD-совместимые форки RVC (только open-source, MIT/AGPL-3.0)
AMD_FORKS = {
    "applio": "https://github.com/IAHispano/Applio.git",
    "mangio": "https://github.com/Mangio621/Mangio-RVC-Fork.git",
    "rvc-webui": "https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git",
}


# ---------------------------------------------------------------- state
def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.load(open(STATE_FILE, "r", encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_state(s: dict) -> None:
    STATE_FILE.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
