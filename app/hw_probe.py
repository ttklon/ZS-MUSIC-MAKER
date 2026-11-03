"""GUI-facing hardware view backed by the shared system detector."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass


@dataclass
class HW:
    gpu_name: str = "unknown"
    vram_gb: float = 0.0
    backend: str = "cpu"
    ram_gb: float = 0.0
    cpu_name: str = ""
    os_name: str = ""
    mode: str = "lite"
    ram_available_gb: float | None = None
    disk_free_gb: float | None = None
    vram_free_gb: float | None = None


def probe() -> HW:
    from app.core.hw_autodetect import detect

    profile = detect()
    system = profile["system"]
    gpu = profile["gpu"]
    return HW(gpu_name=gpu["name"], vram_gb=gpu["vram_gb"], backend=gpu["kind"],
              ram_gb=system["ram_total_gib"], cpu_name=system["cpu_name"],
              os_name=f"{system['os']} {system['os_version']}", mode=profile["mode"],
              ram_available_gb=system["ram_available_gib"], disk_free_gb=system["disk_free_gib"],
              vram_free_gb=gpu["vram_free_gb"])


def main():
    print(json.dumps(asdict(probe()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
