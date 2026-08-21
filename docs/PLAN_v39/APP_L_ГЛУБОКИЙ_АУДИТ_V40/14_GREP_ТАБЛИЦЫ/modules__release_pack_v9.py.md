# grep-таблицы `modules/release_pack_v9.py`

## `import` — 6 совпадений
```
   22 | from __future__ import annotations
   24 | import json
   25 | import shutil
   26 | import time
   27 | from pathlib import Path
  161 |     import sys
```

## `print` — 2 совпадений
```
  164 |         print("usage: python release_pack_v9.py <release_dir>")
  180 |     print(json.dumps(r, indent=2))
```

## `except` — 1 совпадений
```
   37 |     except Exception:
```

## `try` — 1 совпадений
```
   33 |     try:
```

## `def` — 4 совпадений
```
   32 | def _safe_copy(src: str, dst: str) -> bool:
   41 | def _write_json(path: str, data: dict) -> None:
   48 | def _readme_text(payload: dict) -> str:
   75 | def build_release_v9(
```

## `return` — 4 совпадений
```
   36 |         return True
   38 |         return False
   72 |     return "\n".join(lines)
  151 |     return {
```

## `if` — 13 совпадений
```
  100 |     if Path(master_wav).exists() and not master_dst.exists():
  101 |         if _safe_copy(master_wav, str(master_dst)):
  105 |     if hit_report:
  108 |     if arrangement_plan:
  111 |     if style_fingerprint:
  114 |     if sample_manifest:
  117 |     if voice_manifest:
  122 |     if stand_wavs:
  125 |             if Path(path).exists() and _safe_copy(path, str(dst)):
  131 |     if tiktok_wavs:
  136 |             if Path(path).exists() and _safe_copy(path, str(dst)):
  160 | if __name__ == "__main__":
  163 |     if len(sys.argv) < 2:
```

## `for` — 3 совпадений
```
   60 |     for f in payload.get("files", []):
  123 |         for name, path in stand_wavs.items():
  134 |         for name, path in tiktok_wavs.items():
```

## `path_home` — 1 совпадений
```
  178 |         master_wav="/tmp/none.wav",
```
