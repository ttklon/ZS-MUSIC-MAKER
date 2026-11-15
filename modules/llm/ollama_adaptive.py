"""Select an already installed text model conservatively; never download one."""
from __future__ import annotations

import logging
import re
from typing import Any

_GIB = 1024 ** 3
_FAMILIES = (("qwen3.5", 5), ("qwen3", 4), ("qwen2.5", 3),
             ("llama3.3", 2), ("llama3.1", 2), ("llama3.2", 2), ("gemma3", 1))


def choose_installed_model(models: list[dict[str, Any]], available_gib: float | None) -> dict[str, Any]:
    """Estimate CPU-load headroom from installed weight size; not an inference guarantee."""
    if available_gib is None:
        return {"model": None, "reason": "available RAM could not be measured"}
    candidates = []
    for model in models:
        if not isinstance(model, dict):
            continue
        name = str(model.get("name") or model.get("model") or "").strip()
        short_name = name.lower().split("/", 1)[-1]
        if any(part in short_name for part in ("embed", "coder", "-vl", "vision")):
            continue
        family = next((rank for prefix, rank in _FAMILIES
                       if short_name.startswith(prefix + ":") or short_name == prefix), 0)
        try:
            size = int(model.get("size") or 0) / _GIB
        except (TypeError, ValueError):
            continue
        if not family or size <= 0:
            continue
        estimate = size * 1.25 + 2.5  # RAM + context/headroom; conservative heuristic
        if estimate > available_gib:
            continue
        details = model.get("details") or {}
        params = str(details.get("parameter_size") or "") if isinstance(details, dict) else ""
        match = re.search(r"(\d+(?:\.\d+)?)\s*[bB]", params)
        parameters = float(match.group(1)) if match else size
        candidates.append((family, parameters, name, estimate))
    if not candidates:
        return {"model": None, "reason": "no known installed text model fits estimated free RAM"}
    family, parameters, name, estimate = max(candidates)
    return {"model": name, "reason": "installed model selected using a conservative RAM estimate",
            "estimated_ram_gib": round(estimate, 2), "available_ram_gib": available_gib}


def _installed(model: dict[str, Any], name: str) -> bool:
    """Есть ли модель на диске под этим именем (с тегом или без)."""
    short = str(model.get("name") or model.get("model") or "").lower()
    return short == name.lower() or short.split(":")[0] == name.lower().split(":")[0]


def prefer_installed(selection: dict[str, Any], models: list[dict[str, Any]], preferred: str) -> dict[str, Any]:
    """Отдать скачанную bootstrap-ом модель, если выбрать по RAM не удалось.

    Раньше адаптер рассматривал только «влезающие в RAM» модели: на машине с
    4 ГБ `qwen3:4b` отбрасывался, и человек, честно сделавший
    `--bootstrap --online`, всё равно получал `BLOCKED`. Отказ теперь честный и
    объяснённый (сколько нужно памяти), но сама попытка — есть: Ollama умеет
    выгружать модель в своп, и это её решение, а не наше.
    """
    if selection.get("model"):
        return selection
    for model in models:
        if isinstance(model, dict) and _installed(model, preferred):
            out = dict(selection)
            out.update({
                "model": preferred,
                "reason": "bootstrap model present but estimated RAM is tight; "
                          "attempting anyway (slow on CPU)",
                "installed_but_tight": True,
            })
            return out
    return selection


def _preferred_model() -> str:
    """Модель, которую ставит bootstrap: её и надо пробовать первой."""
    import os

    return (os.environ.get("ZSMM_OLLAMA_MODEL", "").strip()
            or os.environ.get("ZSMM_OLLAMA_PULL_MODEL", "").strip()
            or "qwen3:4b")


def discover_ollama_model(base_url: str) -> dict[str, Any]:
    from app.ai.hardware import available_memory_gib
    try:
        import requests
        response = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=2)
        response.raise_for_status()
        payload = response.json()
        models = payload.get("models") if isinstance(payload, dict) else None
        if not isinstance(models, list):
            return {"model": None, "reason": "invalid Ollama model list"}
        from modules.llm.ollama_adaptive import (  # локальный импорт: модуль грузится сам
            choose_installed_model, prefer_installed,
        )
        selection = choose_installed_model(models, available_memory_gib())
        preferred = _preferred_model()
        return prefer_installed(selection, models, preferred) if preferred else selection
    except Exception as exc:
        logging.getLogger(__name__).debug("Ollama model discovery failed", exc_info=True)
        return {"model": None, "reason": f"Ollama model discovery failed: {type(exc).__name__}: {exc}"}
