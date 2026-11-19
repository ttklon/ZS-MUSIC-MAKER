"""Load trusted local Silero packages before any network-enabled torch.hub call.

Silero v3/v4 packages use PackageImporter.load_pickle('tts_models', 'model')
(upstream src/silero/silero.py). These are executable model packages: accept
only trusted files. No repository code/config download is needed offline.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_IDS = frozenset({"v3_1_ru", "v4_ru"})


def _local_package(torch, model_id: str) -> Path | None:
    """Find an explicit package, project weights, or the existing hub cache."""
    configured = os.environ.get("ZSMM_SILERO_MODEL", "").strip()
    if configured:
        path = Path(configured).expanduser()
        if not path.is_file() or not path.stat().st_size:
            raise FileNotFoundError(f"configured Silero model is missing or empty: {path}")
        return path
    project = ROOT / "models" / "silero" / f"{model_id}.pt"
    if project.is_file() and project.stat().st_size:
        return project
    hub = Path(torch.hub.get_dir())
    # Search only the official repository's known package location, not arbitrary pickles.
    for repo in sorted(hub.glob("snakers4_silero-models_*")):
        path = repo / "src" / "silero" / "model" / f"{model_id}.pt"
        if path.is_file() and path.stat().st_size:
            return path
    return None


def load_silero(model_id: str = "v3_1_ru"):
    """Reuse local weights offline; downloading requires the central network opt-in."""
    if model_id not in MODEL_IDS:
        raise ValueError(f"unsupported Silero model: {model_id}")
    import torch
    from app.core.net_policy import network_allowed

    path = _local_package(torch, model_id)
    if path is not None:
        model = torch.package.PackageImporter(str(path)).load_pickle("tts_models", "model")
    elif network_allowed():
        model, _ = torch.hub.load(
            repo_or_dir="snakers4/silero-models", model="silero_tts",
            language="ru", speaker=model_id, trust_repo=True,
        )
    else:
        raise FileNotFoundError(
            f"Silero {model_id} weights unavailable offline; place trusted weights in "
            f"{ROOT / 'models' / 'silero' / (model_id + '.pt')} or set ZSMM_SILERO_MODEL; "
            "enable network access to download"
        )
    if not callable(getattr(model, "apply_tts", None)):
        raise ValueError("Silero package has no apply_tts method")
    model.to("cpu")
    return model
