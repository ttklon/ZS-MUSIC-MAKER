# grep-таблицы `app/core/orchestrator_v10_patch.py`

## `import` — 17 совпадений
```
   10 | from __future__ import annotations
   12 | import json
   13 | import logging
   14 | import time
   15 | from pathlib import Path
   16 | from typing import Any
   31 |         from modules import essentia_analyzer
   40 |         from modules import freesound_client
   49 |         from modules import matchering_master
   58 |         from modules import cover_art_gen
   67 |         from modules import phoneme_coverage
   76 |         from modules import hw_directml
   87 |         from modules import anti_neuro_v10
   96 |         from modules import lyric_vault_v10
  105 |         from modules import karaoke_engine
  114 |         from modules import onboarding_tour
  156 |         from modules import mixdown
```

## `print` — 1 совпадений
```
  226 |     print(json.dumps(r, ensure_ascii=False, indent=2))
```

## `except` — 15 совпадений
```
   35 |     except Exception as e:
   44 |     except Exception as e:
   53 |     except Exception as e:
   62 |     except Exception as e:
   71 |     except Exception as e:
   82 |     except Exception as e:
   91 |     except Exception as e:
  100 |     except Exception as e:
  109 |     except Exception as e:
  118 |     except Exception as e:
  151 |     except Exception as e:
  163 |     except Exception as e:
  177 |     except Exception as e:
  187 |     except Exception as e:
  193 |     except Exception as e:
```

## `try` — 15 совпадений
```
   30 |     try:
   39 |     try:
   48 |     try:
   57 |     try:
   66 |     try:
   75 |     try:
   86 |     try:
   95 |     try:
  104 |     try:
  113 |     try:
  146 |     try:
  155 |     try:
  169 |     try:
  181 |     try:
  191 |     try:
```

## `def` — 2 совпадений
```
   23 | def apply_v10_patch(orchestrator: Any) -> dict[str, Any]:
  125 | def full_v10_pipeline(
```

## `class` — 1 совпадений
```
  221 |     class Dummy:
```

## `return` — 2 совпадений
```
  122 |     return {"ok": True, "version": VERSION, "added": added, "count": len(added)}
  211 |     return {
```

## `if` — 2 совпадений
```
  170 |         if reference_wav and Path(reference_wav).exists():
  219 | if __name__ == "__main__":
```
