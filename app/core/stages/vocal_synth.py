# -*- coding: utf-8 -*-
"""
app/core/stages/vocal_synth.py — правила чернового вокала (без TTS-движков).

Вынесено из `vocal.py`, потому что файл упёрся в лимит 400 строк, а эти
функции — про политику, а не про конвейер:

  * `_no_neural_tts`  — честный отказ, когда нейро-TTS нет;
  * `_system_tts_allowed` — включать ли системный голос Windows.

`pyttsx3` звучит как «виндовский» голос, а заказчик просил обратное, поэтому
он не является ступенью по умолчанию: только явный `ZSMM_ALLOW_SYSTEM_TTS=1`.
"""

from __future__ import annotations

import os
from typing import Any


def _no_neural_tts() -> dict[str, Any]:
    """Честный отказ вместо системного голоса Windows.

    `pyttsx3` звучит как «виндовский» голос, а заказчик просил обратное.
    Поэтому без нейро-TTS вокала нет: человек получает причину и действие,
    а не суррогат, который потом стыдно слушать.
    """
    return {
        "ok": False,
        "blocked": True,
        "engine": "BLOCKED",
        "fallback_used": False,
        "reason": "нет нейро-TTS (silero/XTTS/bark): системный голос Windows "
                  "не используется — запиши свой голос и включи RVC",
        "action": "запись в разделе «Вокал» → RVC, либо bootstrap --online (XTTS)",
        "system_tts_available": "ZSMM_ALLOW_SYSTEM_TTS=1",
    }


def _system_tts_allowed() -> bool:
    """Системный TTS — только по явному opt-in: он не звучит как живой голос."""
    return os.environ.get("ZSMM_ALLOW_SYSTEM_TTS", "").strip() in ("1", "true", "yes")
