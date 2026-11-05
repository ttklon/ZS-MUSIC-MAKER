"""Optional isolated rvc-python worker; no model or network access is implicit.

Invoked by the main process with an explicitly selected Python environment.
This process imports only its own environment, never the main application's
NumPy/PyTorch. It is also used by the in-process adapter for asset preflight.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import logging
import os
from pathlib import Path


def require_base_assets() -> None:
    """Block the 0.1.5 package's implicit network downloads on first use.

    Presence and size do not verify weight integrity or compatibility. Other
    versions may change their download behavior and are not supported here.
    """
    try:
        version = importlib.metadata.version("rvc-python")
        spec = importlib.util.find_spec("rvc_python")
    except (importlib.metadata.PackageNotFoundError, ImportError, ValueError) as exc:
        raise RuntimeError("rvc-python 0.1.5 is not installed in this Python environment") from exc
    if version != "0.1.5" or spec is None or not spec.origin:
        raise RuntimeError(f"unsupported rvc-python version or installation: {version}; need 0.1.5")
    folder = Path(spec.origin).resolve().parent / "base_model"
    names = ("hubert_base.pt", "rmvpe.pt", "rmvpe.onnx")
    missing = [name for name in names if not (folder / name).is_file() or (folder / name).stat().st_size == 0]
    if missing:
        raise RuntimeError("RVC auxiliary weights missing in " + str(folder) + ": " + ", ".join(missing)
                           + "; download separately from trusted sources before inference")


def select_device() -> str:
    """Use the worker's PyTorch, not the main environment's GPU detection."""
    preference = os.environ.get("ZSMM_RVC_DEVICE", "auto").strip().lower()
    if preference not in ("auto", "cpu"):
        raise RuntimeError("ZSMM_RVC_DEVICE must be auto or cpu")
    if preference == "cpu":
        return "cpu:0"
    try:
        import torch

        if torch.cuda.is_available() and torch.cuda.mem_get_info(0)[0] >= 4 * 1024**3:
            return "cuda:0"  # PyTorch HIP uses this API too.
    except Exception:
        logging.getLogger(__name__).debug("worker GPU detection unavailable", exc_info=True)
    return "cpu:0"


def run(input_path: str, output_path: str, model_path: str, index_path: str, pitch: int) -> None:
    require_base_assets()
    from rvc_python.infer import RVCInference

    device = select_device()
    print(f"RVC worker device: {device}", flush=True)
    model = RVCInference(device=device, model_path=model_path, index_path=index_path)
    try:
        model.set_params(f0up_key=pitch, f0method="rmvpe")
        model.infer_file(input_path, output_path)
    finally:
        model.unload_model()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an explicitly configured isolated RVC backend")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--index", default="")
    parser.add_argument("--pitch", type=int, default=0)
    args = parser.parse_args()
    run(args.input, args.output, args.model, args.index, args.pitch)
    return 0


if __name__ == "__main__":
    # -I keeps the sidecar's package environment separate. Load only this
    # standard-library helper by path, without adding the app to sys.path.
    from runpy import run_path

    cache_helper = Path(__file__).resolve().parents[2] / "app" / "core" / "numba_cache.py"
    isolated_numba_cache = run_path(str(cache_helper))["isolated_numba_cache"]
    with isolated_numba_cache():
        raise SystemExit(main())
