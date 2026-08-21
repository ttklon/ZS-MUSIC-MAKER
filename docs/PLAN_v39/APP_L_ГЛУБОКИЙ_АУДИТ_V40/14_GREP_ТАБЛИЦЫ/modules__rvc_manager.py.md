# grep-таблицы `modules/rvc_manager.py`

## `import` — 17 совпадений
```
   17 | from __future__ import annotations
   19 | import json
   20 | import shutil
   21 | import subprocess
   22 | import sys
   23 | import threading
   24 | import time
   25 | from collections.abc import Callable
   26 | from dataclasses import asdict, dataclass
   27 | from pathlib import Path
   74 |         import torch
   88 |         import torch_directml as dml
  103 |         import torch
  141 |             import rvc_python  # noqa: F401
  221 |         from modules import voice_convert
  277 |                 import rvc_python  # noqa
  419 |         from rvc_python.infer import infer_file
```

## `print` — 4 совпадений
```
  136 |         print(f"[rvc_manager] {msg}")
  448 |         print(f"[rvc_manager.infer] rvc-python failed: {e}")
  478 |     print(
  481 |     print(f"State: {json.dumps(_load_state(), ensure_ascii=False, indent=2)}")
```

## `except` — 15 совпадений
```
   49 |         except Exception:
   84 |     except Exception:
   99 |     except Exception:
  113 |     except Exception:
  144 |         except ImportError:
  173 |     except FileNotFoundError:
  175 |     except subprocess.CalledProcessError as e:
  177 |     except Exception as e:
  216 |             except Exception:
  233 |                 except Exception:
  299 |             except ImportError:
  322 |         except Exception as e:
  360 |                     except Exception:
  434 |     except ImportError:
  447 |     except Exception as e:
```

## `try` — 12 совпадений
```
   47 |         try:
   73 |     try:
   87 |     try:
  102 |     try:
  140 |         try:
  163 |     try:
  214 |             try:
  230 |                 try:
  262 |         try:
  276 |             try:
  349 |                     try:
  418 |     try:
```

## `def` — 17 совпадений
```
   45 | def _load_state() -> dict:
   54 | def _save_state(s: dict) -> None:
   69 | def detect_backend() -> RVCBackend:
  125 | def ensure_fork(
  133 |     def _p(msg: str):
  203 |     def __init__(self, backend: RVCBackend | None = None):
  209 |     def on_progress(self, cb: Callable[[TrainingJob], None]) -> None:
  212 |     def _emit(self):
  219 |     def _dataset_ready(self, voice_name: str) -> Path:
  237 |     def train(
  260 |     def _run(self):
  333 |     def _run_with_progress(self, cmd: list[str], job: TrainingJob):
  366 |     def _train_via_fork(self, fork_dir: Path, job: TrainingJob):
  396 | def infer(
  454 | def _fallback_pitch(input_wav: str, out_path: str, pitch_shift: int) -> str:
  467 | def get_state(voice_name: str = "my_voice") -> dict:
  472 | def is_trained(voice_name: str = "my_voice") -> bool:
```

## `class` — 3 совпадений
```
   60 | class RVCBackend:
  184 | class TrainingJob:
  196 | class RVCTrainer:
```

## `raise` — 10 совпадений
```
  269 |                 raise RuntimeError("voice_vault пуст. Запиши минимум 5 минут голоса.")
  308 |                     raise RuntimeError(
  364 |             raise RuntimeError(f"training subprocess exit={ret}")
  379 |                 raise RuntimeError(f"train.py не найден в {fork_dir}")
  414 |         raise RuntimeError("RVC model is not available; refusing pitch-shift fallback")
  433 |             raise RuntimeError("RVC output file is empty or too small")
  441 |                 raise RuntimeError(
  444 |         raise RuntimeError(
  449 |         raise RuntimeError(
  460 |     raise RuntimeError(
```

## `return` — 15 совпадений
```
   48 |             return json.load(open(STATE_FILE, "r", encoding="utf-8"))
   50 |             return {}
   51 |     return {}
   83 |             return b
   98 |         return b
  112 |             return b
  121 |     return b
  150 |         return FORKS_DIR / "rvc-python"
  159 |         return target
  179 |     return target
  235 |         return ds
  258 |         return job
  431 |             return str(out_path)
  469 |     return _load_state().get(voice_name, {})
  473 |     return (MODELS_DIR / voice_name / f"{voice_name}.pth").exists()
```

## `if` — 21 совпадений
```
   46 |     if STATE_FILE.exists():
   76 |         if torch.cuda.is_available():
  105 |         if hasattr(torch.version, "hip") and torch.version.hip is not None:
  134 |         if on_progress:
  138 |     if fork_name == "rvc-python":
  152 |     if fork_name not in AMD_FORKS:
  157 |     if target.exists() and (target / ".git").exists():
  229 |             if src and Path(src).exists():
  268 |             if not files:
  296 |                 if job.device == "cpu":
  301 |                 if self.backend.fork != "rvc-python":
  314 |             if model_path.exists():
  348 |                 if token in line:
  363 |         if ret != 0:
  373 |         if not train_py.exists():
  376 |             if candidates:
  413 |     if not model_path.exists():
  430 |         if out_path.exists() and out_path.stat().st_size > 1000:
  436 |         if backend.fork != "rvc-python":
  438 |             if fork_dir.exists():
  476 | if __name__ == "__main__":
```

## `for` — 5 совпадений
```
   33 | for p in (MODELS_DIR, FORKS_DIR):
  213 |         for cb in self._listeners:
  227 |         for e in idx:
  344 |         for line in proc.stdout:
  347 |             for token in ("Epoch ", "epoch="):
```

## `subprocess` — 5 совпадений
```
  165 |         subprocess.run(
  175 |     except subprocess.CalledProcessError as e:
  335 |         proc = subprocess.Popen(
  337 |             stdout=subprocess.PIPE,
  338 |             stderr=subprocess.STDOUT,
```

## `open` — 1 совпадений
```
   48 |             return json.load(open(STATE_FILE, "r", encoding="utf-8"))
```
