# -*- coding: utf-8 -*-
"""
modules/voice_recording/capability.py — честный отчёт о возможности записи.

`real_recording_possible` истинно только когда есть и бэкенд, и numpy, и
хотя бы одно входное устройство. Пустой список устройств — это BLOCKED, а не
«наверное, работает».
"""

from __future__ import annotations

from typing import Any

from modules.voice_recording.state import SD_OK, _np, _sd


def capability_report() -> dict[str, Any]:
    devices = []
    device_query_error = None
    if SD_OK:
        try:
            devs = _sd.query_devices()
            devices = [
                {"name": d.get("name", ""), "max_in": d.get("max_input_channels", 0)}
                for d in devs
                if d.get("max_input_channels", 0) > 0
            ]
        except Exception as error:
            device_query_error = f"{type(error).__name__}: {error}"
    return {
        "sounddevice_available": SD_OK,
        "numpy_available": _np is not None,
        "input_devices_found": len(devices),
        "devices": devices[:10],
        "device_query_error": device_query_error,
        "real_recording_possible": SD_OK and _np is not None and len(devices) > 0,
    }
