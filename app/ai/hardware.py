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
        threads = os.cpu_count() or 1
        try:
            affinity = psutil.Process().cpu_affinity()
            if affinity:
                threads = len(affinity)
        except Exception:
            logging.getLogger(__name__).debug("CPU affinity unavailable", exc_info=True)
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


def _windows_adapters() -> list[dict[str, str]]:
    """Discover installed names without treating WMI AdapterRAM as reliable VRAM."""
    import json
    import platform
    import subprocess

    if platform.system() != "Windows":
        return []
    script = ("[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
              "Get-CimInstance Win32_VideoController | "
              "Select-Object Name,PNPDeviceID | ConvertTo-Json -Compress")
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True, timeout=5, check=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        data = json.loads(result.stdout.decode("utf-8-sig"))
        items = data if isinstance(data, list) else [data]
        return [{"name": str(item.get("Name") or "Unknown GPU"),
                 "vendor": _vendor(str(item.get("Name") or ""), str(item.get("PNPDeviceID") or "")),
                 "source": "windows_cim"} for item in items if isinstance(item, dict)]
    except Exception:
        logging.getLogger(__name__).debug("Windows GPU enumeration unavailable", exc_info=True)
        return []



def _dxgi_adapters() -> list[dict]:
    """DXGI dedicated VRAM on Windows (physical capacity, not free/model usable)."""
    import ctypes
    import platform
    import uuid

    if platform.system() != "Windows":
        return []
    try:
        class LUID(ctypes.Structure):
            _fields_ = [("low", ctypes.c_uint32), ("high", ctypes.c_int32)]

        class DESC(ctypes.Structure):
            _fields_ = [("description", ctypes.c_wchar * 128), ("vendor", ctypes.c_uint32),
                        ("device", ctypes.c_uint32), ("subsystem", ctypes.c_uint32),
                        ("revision", ctypes.c_uint32), ("dedicated", ctypes.c_size_t),
                        ("dedicated_system", ctypes.c_size_t), ("shared", ctypes.c_size_t),
                        ("luid", LUID), ("flags", ctypes.c_uint32)]

        def method(ptr, index, restype, *types):
            table = ctypes.cast(ptr, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
            return ctypes.WINFUNCTYPE(restype, ctypes.c_void_p, *types)(table[index])

        factory = ctypes.c_void_p()
        iid = ctypes.create_string_buffer(uuid.UUID("770aae78-f26f-4dba-a829-253c83d1b387").bytes_le)
        dxgi = ctypes.WinDLL("dxgi")
        create = dxgi.CreateDXGIFactory1
        create.argtypes = (ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p))
        create.restype = ctypes.c_int32
        if create(ctypes.byref(iid), ctypes.byref(factory)) < 0 or not factory.value:
            return []
        results = []
        try:
            enum = method(factory, 12, ctypes.c_int32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_void_p))
            for index in range(32):
                adapter = ctypes.c_void_p()
                if enum(factory, index, ctypes.byref(adapter)) < 0 or not adapter.value:
                    break
                try:
                    desc = DESC()
                    get_desc = method(adapter, 10, ctypes.c_int32, ctypes.POINTER(DESC))
                    if get_desc(adapter, ctypes.byref(desc)) < 0 or desc.flags & 2:
                        continue
                    name = desc.description.strip() or "Unknown GPU"
                    vendor = {0x1002: "amd", 0x10DE: "nvidia", 0x8086: "intel"}.get(desc.vendor, "unknown")
                    capacity = round(desc.dedicated / (1024 ** 3), 2) if desc.dedicated else None
                    results.append({"name": name, "vendor": vendor, "source": "dxgi",
                                    "total_vram_gib": capacity})
                finally:
                    method(adapter, 2, ctypes.c_uint32)(adapter)
        finally:
            method(factory, 2, ctypes.c_uint32)(factory)
        return results
    except Exception:
        logging.getLogger(__name__).debug("DXGI GPU enumeration unavailable", exc_info=True)
        return []

def _vendor(name: str, device_id: str = "") -> str:
    text = (name + " " + device_id).lower()
    if "nvidia" in text or "ven_10de" in text:
        return "nvidia"
    if any(item in text for item in ("radeon", "amd", "ven_1002", "ven_1022")):
        return "amd"
    if "intel" in text or "ven_8086" in text:
        return "intel"
    return "unknown"


def _torch_device() -> dict:
    """The actual default PyTorch device, not a prediction of model compatibility."""
    try:
        import torch
        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            rocm = bool(getattr(getattr(torch, "version", None), "hip", None))
            total = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
            try:
                free = torch.cuda.mem_get_info(0)[0] / (1024 ** 3)
            except Exception:
                free = None
            return {"name": name, "vendor": _vendor(name), "backend": "rocm" if rocm else "cuda",
                    "total_vram_gib": round(total, 2),
                    "free_vram_gib": round(free, 2) if free is not None else None,
                    "source": "pytorch", "index": 0}
    except Exception:
        logging.getLogger(__name__).debug("PyTorch GPU unavailable", exc_info=True)
    return {}


def _directml_devices() -> list[dict]:
    try:
        import torch_directml as dml
        return [{"name": dml.device_name(i), "vendor": _vendor(dml.device_name(i)),
                 "source": "torch_directml", "index": i} for i in range(dml.device_count())]
    except Exception:
        logging.getLogger(__name__).debug("DirectML enumeration unavailable", exc_info=True)
        return []


def available_memory_gib() -> float | None:
    try:
        import psutil
        return round(psutil.virtual_memory().available / (1024 ** 3), 2)
    except Exception:
        logging.getLogger(__name__).debug("free RAM unavailable", exc_info=True)
        return None


def detect_system(disk_path=None) -> dict:
    """Measurements on this machine. Installed GPU != usable backend != working model."""
    import platform
    import shutil
    from pathlib import Path

    budget = detect_budget()
    torch_device = _torch_device()
    adapters = _dxgi_adapters()
    for item in _windows_adapters():
        if not any(a["name"].casefold() == item["name"].casefold() for a in adapters):
            adapters.append(item)
    directml = _directml_devices()
    if torch_device and not any(a["name"] == torch_device["name"] for a in adapters):
        adapters.append({k: torch_device[k] for k in ("name", "vendor", "source")})
    for item in directml:
        if not any(a["name"] == item["name"] for a in adapters):
            adapters.append({k: item[k] for k in ("name", "vendor", "source")})
    try:
        disk = round(shutil.disk_usage(str(disk_path or Path(__file__).resolve().parents[2])).free / (1024 ** 3), 2)
    except Exception:
        logging.getLogger(__name__).debug("free disk unavailable", exc_info=True)
        disk = None
    return {
        "os": platform.system(), "os_version": platform.release(), "architecture": platform.machine(),
        "cpu_name": platform.processor() or "unknown", "cpu_threads": budget["cpu_threads"],
        "cpu_cores": budget["cpu_cores"], "ram_total_gib": budget["ram_gb"],
        "ram_available_gib": available_memory_gib(), "disk_free_gib": disk,
        "gpus": adapters, "pytorch_device": torch_device or None, "directml_devices": directml,
        "default_backend": torch_device.get("backend", "cpu"),
        "notice": "Hardware detection does not verify model weights, compatibility or inference.",
    }


def assert_llama_memory(key: str, spec: dict, layers: int) -> None:
    """Conservative host-RAM floor; estimates cannot guarantee inference succeeds."""
    free_ram = available_memory_gib()
    required_ram = 2.0 if layers in (-1, 999) else float(spec.get("ram_est_gb", 0.0)) + 1.0
    if free_ram is None or free_ram < required_ram:
        raise RuntimeError(
            f"Insufficient or unknown free RAM for {key}: {free_ram} GiB available; "
            f"conservative estimate {required_ram:.1f} GiB. Free memory or use a smaller model."
        )
