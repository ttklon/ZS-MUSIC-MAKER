# grep-таблицы `modules/expert_mode_v11.py`

## `import` — 7 совпадений
```
    8 | from __future__ import annotations
   10 | import json
   11 | import os
   12 | import sys
   13 | from dataclasses import asdict, dataclass, field, fields
   14 | from typing import Any
  290 |     import tempfile
```

## `print` — 2 совпадений
```
   19 |         print(msg)
  324 |     print("expert_mode_v11 self-test:", "OK" if _self_test() else "FAIL")
```

## `except` — 1 совпадений
```
   20 |     except UnicodeEncodeError:
```

## `try` — 1 совпадений
```
   18 |     try:
```

## `def` — 15 совпадений
```
   17 | def _safe_print(msg):
  138 |     def to_flat_dict(self) -> dict[str, Any]:
  157 |     def to_dict(self):
  160 |     def save(self, path):
  167 |     def load(cls, path):
  172 |     def from_dict(cls, raw):
  173 |         def _build(dc_cls, data):
  196 | def validate(cfg):
  226 | def preset_default():
  230 | def preset_phonk_car():
  243 | def preset_hyperpop_tiktok():
  256 | def preset_trap_summer():
  275 | def apply_preset(name):
  280 | def merge_with_wizard_state(wizard_state, expert):
  289 | def _self_test():
```

## `class` — 9 совпадений
```
   25 | class ExpertBeat:
   37 | class ExpertLyrics:
   53 | class ExpertVoice:
   68 | class ExpertMix:
   80 | class ExpertMaster:
   91 | class ExpertMusicGen:
  102 | class ExpertAntiNeuro:
  112 | class ExpertRender:
  126 | class ExpertConfig:
```

## `return` — 16 совпадений
```
  155 |         return out
  158 |         return asdict(self)
  164 |         return path
  169 |             return cls.from_dict(json.load(f))
  175 |                 return dc_cls()
  180 |             return dc_cls(**kw)
  182 |         return cls(
  223 |     return {"errors": errors, "warnings": warnings}
  227 |     return ExpertConfig()
  240 |     return c
  253 |     return c
  264 |     return c
  277 |     return fn()
  283 |         return wizard_state
  286 |     return merged
  320 |     return ok
```

## `if` — 17 совпадений
```
  174 |             if not isinstance(data, dict):
  178 |                 if fld.name in data:
  198 |     if cfg.render.length_sec < 60:
  200 |     if cfg.render.length_sec > 400:
  202 |     if cfg.beat.bpm_override is not None:
  203 |         if not (40 <= cfg.beat.bpm_override <= 220):
  205 |     if not (0 <= cfg.beat.swing_percent <= 60):
  207 |     if cfg.voice.rvc_epochs < 10:
  209 |     if cfg.voice.rvc_epochs > 1000:
  211 |     if not (-60 <= cfg.master.target_lufs <= 0):
  213 |     if cfg.master.true_peak_max_db > 0:
  215 |     if cfg.anti_neuro.preset not in ("gentle", "standard", "aggressive"):
  217 |     if cfg.render.quality_mode not in ("fast", "quality", "max"):
  219 |     if cfg.voice.mode not in ("rap", "sing", "mix"):
  221 |     if cfg.musicgen.variant not in ("auto", "small", "medium", "large"):
  281 |     if not expert.enabled:
  323 | if __name__ == "__main__":
```

## `for` — 3 совпадений
```
  143 |         for sn, sec in [
  153 |             for fld in fields(sec):
  177 |             for fld in fields(dc_cls):
```

## `with` — 3 совпадений
```
  162 |         with open(path, "w", encoding="utf-8") as f:
  168 |         with open(path, encoding="utf-8") as f:
  296 |     with tempfile.TemporaryDirectory() as tmp:
```

## `todo` — 1 совпадений
```
  306 |     bad.anti_neuro.preset = "xxx"
```

## `open` — 2 совпадений
```
  162 |         with open(path, "w", encoding="utf-8") as f:
  168 |         with open(path, encoding="utf-8") as f:
```
