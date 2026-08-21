# -*- coding: utf-8 -*-
"""ZS Music Maker - tools/pull_ai_models.py (v38)
  python tools/pull_ai_models.py --list | --all | --model <role>
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.ai.registry import MODEL_REGISTRY  # noqa: E402


def _pull_gguf(key):
    spec = MODEL_REGISTRY[key]
    dest = ROOT / "models" / "llm"
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / spec["file"]
    if target.exists():
        print(f"[skip] {key}: already at {target}"); return True
    try:
        from huggingface_hub import hf_hub_download
    except Exception as e:
        print(f"[err] huggingface_hub: {e}"); return False
    try:
        print(f"[pull] {key} <- {spec['hf_repo']}/{spec['file']}")
        p = hf_hub_download(repo_id=spec["hf_repo"], filename=spec["file"],
                            local_dir=str(dest), local_dir_use_symlinks=False)
        print(f"       -> {p}"); return True
    except Exception as e:
        print(f"[err] {key}: {e}"); return False


def _pull_hf(key):
    spec = MODEL_REGISTRY[key]
    repo = spec.get("hf_repo")
    if not repo or repo == "user_supplied":
        print(f"[skip] {key}: user-supplied"); return True
    try:
        from huggingface_hub import snapshot_download
        print(f"[pull] {key} <- {repo}")
        print(f"       -> {snapshot_download(repo_id=repo)}")
        return True
    except Exception as e:
        print(f"[err] {key}: {e}"); return False


def _pull_demucs(key):
    try:
        from demucs.pretrained import get_model
        print("[pull] demucs htdemucs ..."); get_model("htdemucs"); return True
    except Exception as e:
        print(f"[err] {key}: {e}"); return False


def pull(key):
    spec = MODEL_REGISTRY[key]
    eng = spec["engine"]
    if eng == "llama_cpp":
        return _pull_gguf(key)
    if eng == "demucs":
        return _pull_demucs(key)
    if eng in ("audiocraft_musicgen", "xtts_v2", "faster_whisper", "clap", "diffusers"):
        return _pull_hf(key)
    if eng == "rvc":
        (ROOT / "models" / "rvc").mkdir(parents=True, exist_ok=True)
        print(f"[note] {key}: drop your .pth into models/rvc/"); return True
    if eng in ("matchering_plus", "essentia_or_librosa"):
        print(f"[skip] {key}: pip-only"); return True
    print(f"[warn] unknown engine: {eng}"); return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model"); ap.add_argument("--list", action="store_true")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    if args.list:
        for k, v in MODEL_REGISTRY.items():
            print(f"  {k:20s} {v['engine']:22s} VRAM~{v.get('vram_est_gb', 0)} GB - {v['role']}")
        return
    if args.model:
        pull(args.model); return
    if args.all or not sys.stdin.isatty():
        for k in MODEL_REGISTRY:
            pull(k)
        return
    print("See --list / --all / --model <name>.")


if __name__ == "__main__":
    main()
