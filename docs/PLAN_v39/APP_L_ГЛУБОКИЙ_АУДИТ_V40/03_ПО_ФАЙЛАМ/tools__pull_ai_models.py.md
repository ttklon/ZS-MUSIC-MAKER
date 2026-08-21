# АУДИТ ФАЙЛА: `tools/pull_ai_models.py`

**LOC:** 91  |  **Размер:** 3069 байт  |  **Проблем:** 19  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 5 | `__future__.annotations` | from |
| 6 | `argparse` | import |
| 6 | `sys` | import |
| 7 | `pathlib.Path` | from |
| 10 | `app.ai.registry.MODEL_REGISTRY` | from |
| 21 | `huggingface_hub.hf_hub_download` | from |
| 39 | `huggingface_hub.snapshot_download` | from |
| 49 | `demucs.pretrained.get_model` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 13 | `_pull_gguf` | 17 | 3 | ❌ |
| 33 | `_pull_hf` | 11 | 3 | ❌ |
| 47 | `_pull_demucs` | 5 | 1 | ❌ |
| 55 | `pull` | 14 | 5 | ❌ |
| 72 | `main` | 15 | 6 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 16 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 19** — print() вместо logger

  ```
         17 |     target = dest / spec["file"]
         18 |     if target.exists():
  >>>    19 |         print(f"[skip] {key}: already at {target}"); return True
         20 |     try:
         21 |         from huggingface_hub import hf_hub_download
  ```

- **строка 23** — print() вместо logger

  ```
         21 |         from huggingface_hub import hf_hub_download
         22 |     except Exception as e:
  >>>    23 |         print(f"[err] huggingface_hub: {e}"); return False
         24 |     try:
         25 |         print(f"[pull] {key} <- {spec['hf_repo']}/{spec['file']}")
  ```

- **строка 25** — print() вместо logger

  ```
         23 |         print(f"[err] huggingface_hub: {e}"); return False
         24 |     try:
  >>>    25 |         print(f"[pull] {key} <- {spec['hf_repo']}/{spec['file']}")
         26 |         p = hf_hub_download(repo_id=spec["hf_repo"], filename=spec["file"],
         27 |                             local_dir=str(dest), local_dir_use_symlinks=False)
  ```

- **строка 28** — print() вместо logger

  ```
         26 |         p = hf_hub_download(repo_id=spec["hf_repo"], filename=spec["file"],
         27 |                             local_dir=str(dest), local_dir_use_symlinks=False)
  >>>    28 |         print(f"       -> {p}"); return True
         29 |     except Exception as e:
         30 |         print(f"[err] {key}: {e}"); return False
  ```

- **строка 30** — print() вместо logger

  ```
         28 |         print(f"       -> {p}"); return True
         29 |     except Exception as e:
  >>>    30 |         print(f"[err] {key}: {e}"); return False
         31 | 
         32 | 
  ```

- **строка 37** — print() вместо logger

  ```
         35 |     repo = spec.get("hf_repo")
         36 |     if not repo or repo == "user_supplied":
  >>>    37 |         print(f"[skip] {key}: user-supplied"); return True
         38 |     try:
         39 |         from huggingface_hub import snapshot_download
  ```

- **строка 40** — print() вместо logger

  ```
         38 |     try:
         39 |         from huggingface_hub import snapshot_download
  >>>    40 |         print(f"[pull] {key} <- {repo}")
         41 |         print(f"       -> {snapshot_download(repo_id=repo)}")
         42 |         return True
  ```

- **строка 41** — print() вместо logger

  ```
         39 |         from huggingface_hub import snapshot_download
         40 |         print(f"[pull] {key} <- {repo}")
  >>>    41 |         print(f"       -> {snapshot_download(repo_id=repo)}")
         42 |         return True
         43 |     except Exception as e:
  ```

- **строка 44** — print() вместо logger

  ```
         42 |         return True
         43 |     except Exception as e:
  >>>    44 |         print(f"[err] {key}: {e}"); return False
         45 | 
         46 | 
  ```

- **строка 50** — print() вместо logger

  ```
         48 |     try:
         49 |         from demucs.pretrained import get_model
  >>>    50 |         print("[pull] demucs htdemucs ..."); get_model("htdemucs"); return True
         51 |     except Exception as e:
         52 |         print(f"[err] {key}: {e}"); return False
  ```

- **строка 52** — print() вместо logger

  ```
         50 |         print("[pull] demucs htdemucs ..."); get_model("htdemucs"); return True
         51 |     except Exception as e:
  >>>    52 |         print(f"[err] {key}: {e}"); return False
         53 | 
         54 | 
  ```

- **строка 66** — print() вместо logger

  ```
         64 |     if eng == "rvc":
         65 |         (ROOT / "models" / "rvc").mkdir(parents=True, exist_ok=True)
  >>>    66 |         print(f"[note] {key}: drop your .pth into models/rvc/"); return True
         67 |     if eng in ("matchering_plus", "essentia_or_librosa"):
         68 |         print(f"[skip] {key}: pip-only"); return True
  ```

- **строка 68** — print() вместо logger

  ```
         66 |         print(f"[note] {key}: drop your .pth into models/rvc/"); return True
         67 |     if eng in ("matchering_plus", "essentia_or_librosa"):
  >>>    68 |         print(f"[skip] {key}: pip-only"); return True
         69 |     print(f"[warn] unknown engine: {eng}"); return False
         70 | 
  ```

- **строка 69** — print() вместо logger

  ```
         67 |     if eng in ("matchering_plus", "essentia_or_librosa"):
         68 |         print(f"[skip] {key}: pip-only"); return True
  >>>    69 |     print(f"[warn] unknown engine: {eng}"); return False
         70 | 
         71 | 
  ```

- **строка 79** — print() вместо logger

  ```
         77 |     if args.list:
         78 |         for k, v in MODEL_REGISTRY.items():
  >>>    79 |             print(f"  {k:20s} {v['engine']:22s} VRAM~{v.get('vram_est_gb', 0)} GB - {v['role']}")
         80 |         return
         81 |     if args.model:
  ```

- **строка 87** — print() вместо logger

  ```
         85 |             pull(k)
         86 |         return
  >>>    87 |     print("See --list / --all / --model <name>.")
         88 | 
         89 | 
  ```

### MISSING_DOCSTRING — 2 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 55** — public function 'pull' без docstring

  ```
         53 | 
         54 | 
  >>>    55 | def pull(key):
         56 |     spec = MODEL_REGISTRY[key]
         57 |     eng = spec["engine"]
  ```

- **строка 72** — public function 'main' без docstring

  ```
         70 | 
         71 | 
  >>>    72 | def main():
         73 |     ap = argparse.ArgumentParser()
         74 |     ap.add_argument("--model"); ap.add_argument("--list", action="store_true")
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 5** — import 'annotations' не используется в теле файла

  ```
          3 |   python tools/pull_ai_models.py --list | --all | --model <role>
          4 | """
  >>>     5 | from __future__ import annotations
          6 | import argparse, sys
          7 | from pathlib import Path
  ```
