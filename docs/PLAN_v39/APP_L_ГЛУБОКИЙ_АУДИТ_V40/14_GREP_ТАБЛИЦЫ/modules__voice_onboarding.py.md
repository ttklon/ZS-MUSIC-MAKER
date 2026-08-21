# grep-таблицы `modules/voice_onboarding.py`

## `import` — 8 совпадений
```
   21 | from __future__ import annotations
   23 | import json
   24 | import time
   25 | from dataclasses import asdict, dataclass, field
   26 | from pathlib import Path
   27 | from typing import Any
  185 |         from modules import voice_recording as vr
  248 |         from modules import voice_recording as vr
```

## `print` — 12 совпадений
```
  238 |     print("=" * 64)
  239 |     print("ZS Music Maker — Voice Onboarding (5 минут)")
  240 |     print("=" * 64)
  242 |     print(f"План: {len(plan)} шагов, всего {PLAN['total']} сек.")
  243 |     print(f"  — фонемный текст: {PLAN['phoneme_text']}s ({len(PHONEME_SCRIPT)} фраз)")
  244 |     print(f"  — 8 стилей × 15s: {PLAN['styles_total']}s")
  245 |     print(f"  — караоке: {PLAN['karaoke']}s")
  246 |     print()
  253 |     print("[capability]", json.dumps(cap, ensure_ascii=False))
  256 |         print("⚠️  Микрофон недоступен. Реальная запись НЕВОЗМОЖНА в этой среде.")
  262 |     print(f"✓ manifest saved: {MANIFEST}")
  268 |         print("[voice_onboarding] exit=1 (plan-only: mic unavailable)")
```

## `except` — 3 совпадений
```
  174 |         except Exception:
  186 |     except Exception:
  251 |     except Exception as e:
```

## `try` — 3 совпадений
```
  172 |         try:
  184 |     try:
  247 |     try:
```

## `def` — 10 совпадений
```
   94 |     def as_dict(self) -> dict[str, Any]:
  109 |     def as_dict(self) -> dict[str, Any]:
  113 | def build_plan() -> list[OnboardingStep]:
  152 | def compute_phoneme_coverage(texts: list[str]) -> dict[str, Any]:
  170 | def _load_manifest() -> dict[str, Any]:
  179 | def _save_manifest(m: dict[str, Any]) -> None:
  183 | def record_step(step: OnboardingStep, mode: str = "auto") -> OnboardingStep:
  204 | def compute_progress(steps: list[OnboardingStep]) -> OnboardingProgress:
  231 | def is_ready_for_rvc() -> bool:
  237 | def run_cli() -> int:
```

## `class` — 2 совпадений
```
   79 | class OnboardingStep:
   99 | class OnboardingProgress:
```

## `raise` — 1 совпадений
```
  274 |     raise SystemExit(run_cli())
```

## `return` — 12 совпадений
```
   95 |         return asdict(self)
  110 |         return asdict(self)
  149 |     return steps
  162 |     return {
  173 |             return json.loads(MANIFEST.read_text(encoding="utf-8"))
  176 |     return {"steps": [], "started_at": None, "completed_at": None}
  188 |         return step
  201 |     return step
  219 |     return OnboardingProgress(
  234 |     return compute_progress(steps).ready_for_rvc
  269 |         return 1
  270 |     return 0
```

## `if` — 8 совпадений
```
  156 |             if ch in RUS_PHONEMES:
  171 |     if MANIFEST.exists():
  191 |     if cap.get("real_recording_possible") and mode == "auto":
  194 |         if info.get("ok"):
  197 |             if out.get("ok"):
  255 |     if not mic_ok:
  267 |     if not mic_ok:
  273 | if __name__ == "__main__":
```

## `for` — 4 совпадений
```
  116 |     for i, text in enumerate(PHONEME_SCRIPT, 1):
  127 |     for st in STYLES:
  154 |     for t in texts:
  155 |         for ch in t.lower():
```

## `sleep` — 1 совпадений
```
  195 |             time.sleep(step.target_sec)
```
