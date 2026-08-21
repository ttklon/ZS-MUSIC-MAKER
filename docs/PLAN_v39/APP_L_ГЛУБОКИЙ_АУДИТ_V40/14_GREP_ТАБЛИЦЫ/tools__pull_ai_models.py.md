# grep-таблицы `tools/pull_ai_models.py`

## `import` — 7 совпадений
```
    5 | from __future__ import annotations
    6 | import argparse, sys
    7 | from pathlib import Path
   10 | from app.ai.registry import MODEL_REGISTRY  # noqa: E402
   21 |         from huggingface_hub import hf_hub_download
   39 |         from huggingface_hub import snapshot_download
   49 |         from demucs.pretrained import get_model
```

## `print` — 16 совпадений
```
   19 |         print(f"[skip] {key}: already at {target}"); return True
   23 |         print(f"[err] huggingface_hub: {e}"); return False
   25 |         print(f"[pull] {key} <- {spec['hf_repo']}/{spec['file']}")
   28 |         print(f"       -> {p}"); return True
   30 |         print(f"[err] {key}: {e}"); return False
   37 |         print(f"[skip] {key}: user-supplied"); return True
   40 |         print(f"[pull] {key} <- {repo}")
   41 |         print(f"       -> {snapshot_download(repo_id=repo)}")
   44 |         print(f"[err] {key}: {e}"); return False
   50 |         print("[pull] demucs htdemucs ..."); get_model("htdemucs"); return True
   52 |         print(f"[err] {key}: {e}"); return False
   66 |         print(f"[note] {key}: drop your .pth into models/rvc/"); return True
   68 |         print(f"[skip] {key}: pip-only"); return True
   69 |     print(f"[warn] unknown engine: {eng}"); return False
   79 |             print(f"  {k:20s} {v['engine']:22s} VRAM~{v.get('vram_est_gb', 0)} GB - {v['role']}")
   87 |     print("See --list / --all / --model <name>.")
```

## `except` — 4 совпадений
```
   22 |     except Exception as e:
   29 |     except Exception as e:
   43 |     except Exception as e:
   51 |     except Exception as e:
```

## `try` — 4 совпадений
```
   20 |     try:
   24 |     try:
   38 |     try:
   48 |     try:
```

## `def` — 5 совпадений
```
   13 | def _pull_gguf(key):
   33 | def _pull_hf(key):
   47 | def _pull_demucs(key):
   55 | def pull(key):
   72 | def main():
```

## `return` — 6 совпадений
```
   42 |         return True
   59 |         return _pull_gguf(key)
   61 |         return _pull_demucs(key)
   63 |         return _pull_hf(key)
   80 |         return
   86 |         return
```

## `if` — 11 совпадений
```
   18 |     if target.exists():
   36 |     if not repo or repo == "user_supplied":
   58 |     if eng == "llama_cpp":
   60 |     if eng == "demucs":
   62 |     if eng in ("audiocraft_musicgen", "xtts_v2", "faster_whisper", "clap", "diffusers"):
   64 |     if eng == "rvc":
   67 |     if eng in ("matchering_plus", "essentia_or_librosa"):
   77 |     if args.list:
   81 |     if args.model:
   83 |     if args.all or not sys.stdin.isatty():
   90 | if __name__ == "__main__":
```

## `for` — 2 совпадений
```
   78 |         for k, v in MODEL_REGISTRY.items():
   84 |         for k in MODEL_REGISTRY:
```
