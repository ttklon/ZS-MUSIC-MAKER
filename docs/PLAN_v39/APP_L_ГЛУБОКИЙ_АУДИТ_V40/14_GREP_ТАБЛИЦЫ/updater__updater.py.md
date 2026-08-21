# grep-таблицы `updater/updater.py`

## `import` — 13 совпадений
```
   22 | from __future__ import annotations
   24 | import hashlib
   25 | import json
   26 | import os
   27 | import shutil
   28 | import subprocess
   29 | import sys
   30 | import time
   31 | import zipfile
   32 | from pathlib import Path
   33 | from typing import Any
  444 |         import urllib.request as urlreq
  454 |     import argparse
```

## `print` — 6 совпадений
```
  348 |             print(f"[updater] пользовательские данные сохранены: {', '.join(restored)}")
  466 |         print(
  480 |         print(json.dumps(r, indent=2, ensure_ascii=False))
  484 |         print(json.dumps(r, indent=2, ensure_ascii=False))
  487 |         print(json.dumps(list_backups(), indent=2))
  490 |         print(json.dumps(check_updates(args.check), indent=2))
```

## `except` — 15 совпадений
```
  117 |         except Exception:
  148 |         except Exception:
  202 |     except zipfile.BadZipFile:
  239 |                 except Exception:
  255 |         except Exception:
  278 |     except Exception as e:
  287 |     except Exception as e:
  324 |     except Exception as e:
  349 |     except Exception as e:
  375 |         except subprocess.TimeoutExpired:
  384 |         except Exception:
  394 |     except Exception:
  424 |             except Exception:
  438 |     except Exception as e:
  448 |     except Exception as e:
```

## `try` — 14 совпадений
```
  114 |         try:
  136 |         try:
  199 |     try:
  237 |                 try:
  252 |         try:
  272 |     try:
  282 |     try:
  321 |     try:
  327 |     try:
  360 |         try:
  389 |     try:
  408 |     try:
  421 |             try:
  443 |     try:
```

## `def` — 17 совпадений
```
   36 | def program_dir() -> Path:
   55 | def user_data_dir() -> Path:
   68 | def backup_dir() -> Path:
   74 | def staging_dir() -> Path:
   99 | def _stash_user_data(prog: Path, stg: Path) -> dict[str, Path]:
  123 | def _restore_user_data(prog: Path, moved: dict[str, Path]) -> list[str]:
  153 | def ensure_user_dirs() -> None:
  169 | def compute_sha256(path: Path) -> str:
  177 | def verify_zip(zip_path: Path, expected_sha256: str | None = None) -> dict[str, Any]:
  223 | def make_backup(reason: str = "pre_update") -> Path | None:
  245 | def prune_old_backups(keep: int = 3) -> list[Path]:
  260 | def list_backups() -> list[dict[str, Any]]:
  270 | def migrate_settings(old_path: Path, new_path: Path) -> dict[str, Any]:
  298 | def install_from_zip(
  399 | def rollback_last() -> dict[str, Any]:
  442 | def check_updates(release_url: str) -> dict[str, Any]:
  453 | def main() -> int:
```

## `raise` — 1 совпадений
```
  497 |     raise SystemExit(main())
```

## `return` — 43 совпадений
```
   39 |         return Path(env)
   48 |         return root
   51 |         return Path(pf) / "ZS Music Maker"
   52 |     return root
   58 |         return Path(env)
   61 |         return Path(appdata) / "ZS Music Maker"
   63 |         return Path.home() / "Library" / "Application Support" / "ZS Music Maker"
   65 |     return Path(xdg) / "zsmm"
   71 |     return d
   77 |     return d
  120 |     return moved
  150 |     return restored
  174 |     return h.hexdigest()
  182 |         return result
  186 |         return result
  189 |         return result
  196 |             return result
  204 |         return result
  217 |         return result
  220 |     return result
  226 |         return None
  242 |     return dst
  257 |     return removed
  262 |     return [
  295 |     return {"ok": len(conflicts) == 0, "conflicts": conflicts}
  306 |         return {
  315 |         return {"ok": False, "stage": "backup", "error": "backup failed"}
  325 |         return {"ok": False, "stage": "extract", "error": str(e), "backup": str(bak)}
  351 |         return {
  368 |                 return {
  377 |             return {
  396 |     return {"ok": True, "version": ver, "backup": str(bak)}
  405 |         return {"ok": False, "error": "no backups"}
  437 |         return {"ok": True, "restored_from": str(last), "user_data_preserved": restored}
  439 |         return {"ok": False, "error": str(e)}
  449 |         return {"ok": False, "reason": str(e)}
  450 |     return {"ok": True, "data": data}
  477 |         return 0
  481 |         return 0 if r.get("ok") else 1
  485 |         return 0 if r.get("ok") else 1
  488 |         return 0
  491 |         return 0
  493 |     return 0
```

## `if` — 42 совпадений
```
   38 |     if env:
   47 |     if (root / "main.py").exists():
   49 |     if sys.platform == "win32":
   57 |     if env:
   59 |     if sys.platform == "win32":
   62 |     if sys.platform == "darwin":
  110 |         if not src.exists():
  137 |             if stash.is_dir():
  144 |                 if dst.exists():
  180 |     if not p.exists():
  184 |     if result["size"] < 1024:
  187 |     if result["size"] > 5 * 1024**3:
  193 |     if expected_sha256:
  194 |         if sha.lower() != expected_sha256.lower():
  215 |     if not (has_main and has_version and has_modules):
  225 |     if not src.exists():
  231 |             if "updater/backup" in root.replace("\\", "/"):
  233 |             if "__pycache__" in root:
  275 |             if old_path.exists()
  290 |     if conflicts:
  305 |     if not v.get("ok"):
  314 |     if bak is None:
  318 |     if stg.exists():
  331 |             if item.name == "updater":
  333 |             if item.is_dir():
  338 |             if item.name == ".user_stash":  # это наши же сохранённые данные, не копируем как часть дистрибутива
  341 |             if item.is_dir():
  347 |         if restored:
  359 |     if smoke_test:
  366 |             if r.returncode != 0:
  390 |         if ver_p.exists():
  404 |     if not backups:
  412 |         if stash_root.exists():
  417 |             if not src.exists():
  427 |             if item.name in ("updater", ".rollback_stash"):
  429 |             if item.is_dir():
  465 |     if args.info:
  478 |     if args.install:
  482 |     if args.rollback:
  486 |     if args.list_backups:
  489 |     if args.check:
  496 | if __name__ == "__main__":
```

## `for` — 12 совпадений
```
  108 |     for rel in USER_PRESERVED:
  133 |     for rel, stash in moved.items():
  156 |     for sub in (
  172 |         for chunk in iter(lambda: f.read(8192), b""):
  230 |         for root, dirs, files in os.walk(src):
  235 |             for f in files:
  251 |     for old in backups[keep:]:
  264 |         for p in sorted(
  330 |         for item in prog.iterdir():
  337 |         for item in stg.iterdir():
  415 |         for rel in USER_PRESERVED:
  426 |         for item in prog.iterdir():
```

## `with` — 7 совпадений
```
  171 |     with open(path, "rb") as f:
  200 |         with zipfile.ZipFile(str(p), "r") as z:
  229 |     with zipfile.ZipFile(str(dst), "w", zipfile.ZIP_DEFLATED) as z:
  292 |         with open(log_p, "a", encoding="utf-8") as f:
  322 |         with zipfile.ZipFile(str(zip_p), "r") as z:
  433 |         with zipfile.ZipFile(str(last), "r") as z:
  446 |         with urlreq.urlopen(release_url, timeout=15) as resp:
```

## `subprocess` — 2 совпадений
```
  361 |             r = subprocess.run(
  375 |         except subprocess.TimeoutExpired:
```

## `open` — 2 совпадений
```
  171 |     with open(path, "rb") as f:
  292 |         with open(log_p, "a", encoding="utf-8") as f:
```
