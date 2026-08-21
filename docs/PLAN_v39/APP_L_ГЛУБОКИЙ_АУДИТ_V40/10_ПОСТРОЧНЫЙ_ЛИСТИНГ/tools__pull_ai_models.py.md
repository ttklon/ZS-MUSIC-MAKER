# ПОСТРОЧНЫЙ ЛИСТИНГ: `tools/pull_ai_models.py`

**Всего строк:** 91

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 36 | 39.6 |
| blank | 12 | 13.2 |
| branch | 11 | 12.1 |
| try_block | 8 | 8.8 |
| import | 7 | 7.7 |
| return | 6 | 6.6 |
| def | 5 | 5.5 |
| docstring | 3 | 3.3 |
| loop | 2 | 2.2 |
| comment | 1 | 1.1 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """ZS Music Maker - tools/pull_ai_models.py (v38)
    3 [docstring ]   python tools/pull_ai_models.py --list | --all | --model <role>
    4 [docstring ] """
    5 [import    ] from __future__ import annotations
    6 [import    ] import argparse, sys
    7 [import    ] from pathlib import Path
    8 [code      ] ROOT = Path(__file__).resolve().parents[1]
    9 [code      ] sys.path.insert(0, str(ROOT))
   10 [import    ] from app.ai.registry import MODEL_REGISTRY  # noqa: E402
   11 [blank     ] 
   12 [blank     ] 
   13 [def       ] def _pull_gguf(key):
   14 [code      ]     spec = MODEL_REGISTRY[key]
   15 [code      ]     dest = ROOT / "models" / "llm"
   16 [code      ]     dest.mkdir(parents=True, exist_ok=True)
   17 [code      ]     target = dest / spec["file"]
   18 [branch    ]     if target.exists():
   19 [code      ]         print(f"[skip] {key}: already at {target}"); return True
   20 [try_block ]     try:
   21 [import    ]         from huggingface_hub import hf_hub_download
   22 [try_block ]     except Exception as e:
   23 [code      ]         print(f"[err] huggingface_hub: {e}"); return False
   24 [try_block ]     try:
   25 [code      ]         print(f"[pull] {key} <- {spec['hf_repo']}/{spec['file']}")
   26 [code      ]         p = hf_hub_download(repo_id=spec["hf_repo"], filename=spec["file"],
   27 [code      ]                             local_dir=str(dest), local_dir_use_symlinks=False)
   28 [code      ]         print(f"       -> {p}"); return True
   29 [try_block ]     except Exception as e:
   30 [code      ]         print(f"[err] {key}: {e}"); return False
   31 [blank     ] 
   32 [blank     ] 
   33 [def       ] def _pull_hf(key):
   34 [code      ]     spec = MODEL_REGISTRY[key]
   35 [code      ]     repo = spec.get("hf_repo")
   36 [branch    ]     if not repo or repo == "user_supplied":
   37 [code      ]         print(f"[skip] {key}: user-supplied"); return True
   38 [try_block ]     try:
   39 [import    ]         from huggingface_hub import snapshot_download
   40 [code      ]         print(f"[pull] {key} <- {repo}")
   41 [code      ]         print(f"       -> {snapshot_download(repo_id=repo)}")
   42 [return    ]         return True
   43 [try_block ]     except Exception as e:
   44 [code      ]         print(f"[err] {key}: {e}"); return False
   45 [blank     ] 
   46 [blank     ] 
   47 [def       ] def _pull_demucs(key):
   48 [try_block ]     try:
   49 [import    ]         from demucs.pretrained import get_model
   50 [code      ]         print("[pull] demucs htdemucs ..."); get_model("htdemucs"); return True
   51 [try_block ]     except Exception as e:
   52 [code      ]         print(f"[err] {key}: {e}"); return False
   53 [blank     ] 
   54 [blank     ] 
   55 [def       ] def pull(key):
   56 [code      ]     spec = MODEL_REGISTRY[key]
   57 [code      ]     eng = spec["engine"]
   58 [branch    ]     if eng == "llama_cpp":
   59 [return    ]         return _pull_gguf(key)
   60 [branch    ]     if eng == "demucs":
   61 [return    ]         return _pull_demucs(key)
   62 [branch    ]     if eng in ("audiocraft_musicgen", "xtts_v2", "faster_whisper", "clap", "diffusers"):
   63 [return    ]         return _pull_hf(key)
   64 [branch    ]     if eng == "rvc":
   65 [code      ]         (ROOT / "models" / "rvc").mkdir(parents=True, exist_ok=True)
   66 [code      ]         print(f"[note] {key}: drop your .pth into models/rvc/"); return True
   67 [branch    ]     if eng in ("matchering_plus", "essentia_or_librosa"):
   68 [code      ]         print(f"[skip] {key}: pip-only"); return True
   69 [code      ]     print(f"[warn] unknown engine: {eng}"); return False
   70 [blank     ] 
   71 [blank     ] 
   72 [def       ] def main():
   73 [code      ]     ap = argparse.ArgumentParser()
   74 [code      ]     ap.add_argument("--model"); ap.add_argument("--list", action="store_true")
   75 [code      ]     ap.add_argument("--all", action="store_true")
   76 [code      ]     args = ap.parse_args()
   77 [branch    ]     if args.list:
   78 [loop      ]         for k, v in MODEL_REGISTRY.items():
   79 [code      ]             print(f"  {k:20s} {v['engine']:22s} VRAM~{v.get('vram_est_gb', 0)} GB - {v['role']}")
   80 [return    ]         return
   81 [branch    ]     if args.model:
   82 [code      ]         pull(args.model); return
   83 [branch    ]     if args.all or not sys.stdin.isatty():
   84 [loop      ]         for k in MODEL_REGISTRY:
   85 [code      ]             pull(k)
   86 [return    ]         return
   87 [code      ]     print("See --list / --all / --model <name>.")
   88 [blank     ] 
   89 [blank     ] 
   90 [branch    ] if __name__ == "__main__":
   91 [code      ]     main()
```