"""Автодетект железа: CUDA / DirectML / CPU + VRAM + режим full/fallback."""

from __future__ import annotations

import logging

import json
import platform
from dataclasses import asdict, dataclass


@dataclass
class HW:
    gpu_name: str = "CPU"
    vram_gb: float = 0.0
    backend: str = "cpu"  # "cuda" | "directml" | "cpu"
    ram_gb: float = 0.0
    cpu_name: str = ""
    os_name: str = ""
    mode: str = "fallback"  # "full" | "fallback"


def probe() -> HW:
    try:
        import psutil

        ram_gb = round(psutil.virtual_memory().total / 1e9, 1)
    except Exception:
        ram_gb = 0.0
    hw = HW(ram_gb=ram_gb, cpu_name=platform.processor(), os_name=platform.platform())

    # 1. CUDA
    try:
        import torch

        if torch.cuda.is_available():
            hw.gpu_name = torch.cuda.get_device_name(0)
            hw.vram_gb = round(
                torch.cuda.get_device_properties(0).total_memory / 1e9, 1
            )
            hw.backend = "cuda"
    except Exception:
        logging.getLogger(__name__).debug("ignored exception", exc_info=True)

    # 2. DirectML (AMD/Intel iGPU на Windows)
    if hw.backend == "cpu":
        try:
            import torch_directml as dml

            hw.gpu_name = (
                dml.device_name(0) if hasattr(dml, "device_name") else "DirectML GPU"
            )
            hw.vram_gb = 4.0  # оценочно — уточняется через DXGI
            hw.backend = "directml"
        except Exception:
            logging.getLogger(__name__).debug("ignored exception", exc_info=True)

    hw.mode = "full" if hw.vram_gb >= 10 else "fallback"
    return hw


def main():
    print(json.dumps(asdict(probe()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
