# -*- coding: utf-8 -*-
"""
ZS Music Maker — hardware_adapter.py (GOD MODE)
========================================================================
Автоматическая адаптация под слабое железо (baseline: 16GB RAM, RX 580, Xeon).
Устраняет риск Out-of-Memory при тяжелых вычислениях.
"""

import os
import platform
import psutil

class HardwareAdapter:
    @staticmethod
    def get_system_specs() -> dict:
        mem = psutil.virtual_memory()
        return {
            "os": f"{platform.system()} {platform.release()}",
            "cpu_count": os.cpu_count(),
            "total_ram_gb": round(mem.total / (1024**3), 2),
            "available_ram_gb": round(mem.available / (1024**3), 2),
            "low_memory_mode": mem.total < (17 * 1024**3) # Менее 17 ГБ RAM
        }

    @staticmethod
    def get_optimal_worker_count() -> int:
        specs = HardwareAdapter.get_system_specs()
        if specs["low_memory_mode"]:
            return max(1, specs["cpu_count"] // 4)
        return max(2, specs["cpu_count"] // 2)

    @staticmethod
    def check_memory_headroom() -> bool:
        mem = psutil.virtual_memory()
        return mem.percent < 85.0 # Если забито больше 85%, нужен power save

if __name__ == "__main__":
    print(HardwareAdapter.get_system_specs())
