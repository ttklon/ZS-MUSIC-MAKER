# -*- coding: utf-8 -*-
"""
safe_import.py — Graceful-imports helper для ZS Music Maker v4.
Позволяет UI и пайплайну переживать отсутствие тяжёлых зависимостей.
"""
import importlib
import logging

log = logging.getLogger("zsmm.safe_import")


def safe_import(module_name: str, package: str = None, silent: bool = False):
    """
    Импортирует модуль, при ошибке возвращает None (не бросает).
    Использование:
        librosa = safe_import("librosa")
        if librosa is None:
            return {"error": "librosa не установлен"}
    """
    try:
        return importlib.import_module(module_name, package)
    except Exception as e:
        if not silent:
            log.warning(f"[safe_import] '{module_name}' недоступен: {e}")
        return None


def require(*module_names: str) -> dict:
    """
    Проверяет доступность списка модулей.
    Возвращает {"missing": [...], "available": [...]}.
    """
    missing, available = [], []
    for m in module_names:
        if safe_import(m, silent=True) is None:
            missing.append(m)
        else:
            available.append(m)
    return {"missing": missing, "available": available,
            "ok": len(missing) == 0}


def diagnostics() -> dict:
    """Полная диагностика окружения — какие библиотеки доступны."""
    groups = {
        "core": ["numpy", "scipy", "librosa", "soundfile", "pydub", "requests"],
        "ui": ["gradio"],
        "audio_gen": ["torch", "torchaudio", "audiocraft"],
        "voice_synth": ["bark", "TTS", "pyttsx3"],
        "voice_convert": ["rvc_python"],
        "stems": ["demucs"],
        "transcribe": ["faster_whisper"],
        "mastering": ["matchering"],
        "record": ["sounddevice"],
        "acceleration": ["torch_directml"],
    }
    result = {}
    for group, mods in groups.items():
        result[group] = require(*mods)
    return result


if __name__ == "__main__":
    import json
    print(json.dumps(diagnostics(), ensure_ascii=False, indent=2))
