"""Conservative local hardware detection for the AI model registry.

Values are measurements, not assumptions about the developer's computer.
Unknown GPU memory is represented as zero; explicit environment overrides are
available for platforms whose GPU APIs cannot expose VRAM.
"""
from __future__ import annotations

import logging
import os


def detect_budget() -> dict[str, float | int]:
    try:
        import psutil

        ram = psutil.virtual_memory().total / (1024 ** 3)
        threads = len(psutil.Process().cpu_affinity()) if hasattr(psutil.Process(), "cpu_affinity") else (os.cpu_count() or 1)
        cores = min(threads, psutil.cpu_count(logical=False) or threads)
    except Exception:
        ram, threads, cores = 0.0, os.cpu_count() or 1, os.cpu_count() or 1
    vram = 0.0
    try:
        import torch

        if torch.cuda.is_available():
            vram = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
    except Exception:
        logging.getLogger(__name__).debug("GPU backend unavailable", exc_info=True)
    return {"ram_gb": round(ram, 2), "vram_gb": round(vram, 2),
            "cpu_threads": max(1, int(threads)), "cpu_cores": max(1, int(cores))}


def whisper_weights_available(local_dir, use_gpu: bool) -> bool:
    """Check required CTranslate2 assets, locally or in the standard HF cache."""
    files = ("model.bin", "config.json", "tokenizer.json", "preprocessor_config.json")
    if all((local_dir / name).is_file() for name in files):
        return True
    repo = "Systran/faster-whisper-large-v3" if use_gpu else "Systran/faster-whisper-medium"
    try:
        from huggingface_hub import try_to_load_from_cache

        return all(isinstance(try_to_load_from_cache(repo, name), str) for name in files)
    except Exception:
        logging.getLogger(__name__).debug("Whisper cache unavailable", exc_info=True)
        return False
