# grep-таблицы `modules/onboarding_tour.py`

## `import` — 5 совпадений
```
   10 | from __future__ import annotations
   12 | import json
   13 | import logging
   14 | from pathlib import Path
   15 | from typing import Any
```

## `print` — 4 совпадений
```
  204 |         print(f"\n=== Шаг {i+1}/{len(TOUR_STEPS)}: {step['title']} ===")
  205 |         print(step["text"])
  207 |             print(f"  → элемент интерфейса: {step['anchor']}")
  209 |     print("\nТур завершён.")
```

## `except` — 2 совпадений
```
   36 |     except Exception as e:
  166 |         except Exception:
```

## `try` — 2 совпадений
```
   29 |     try:
  164 |         try:
```

## `def` — 9 совпадений
```
   20 | def _tour_state_path() -> Path:
  162 | def load_state() -> dict[str, Any]:
  171 | def save_state(state: dict[str, Any]) -> None:
  177 | def should_show() -> bool:
  181 | def steps() -> list[dict[str, Any]]:
  185 | def get_step(idx: int) -> dict[str, Any] | None:
  191 | def mark_done() -> None:
  195 | def reset() -> None:
  199 | def run_console_demo() -> None:
```

## `return` — 7 совпадений
```
   38 |     return new
  165 |             return json.loads(TOUR_STATE.read_text(encoding="utf-8"))
  168 |     return {"tour_done": False, "last_step": 0}
  178 |     return not load_state().get("tour_done", False)
  182 |     return list(TOUR_STEPS)
  187 |         return TOUR_STEPS[idx]
  188 |     return None
```

## `if` — 6 совпадений
```
   31 |         if not new.exists():
   33 |                 if cand.exists() and cand.resolve() != new.resolve():
  163 |     if TOUR_STATE.exists():
  186 |     if 0 <= idx < len(TOUR_STEPS):
  206 |         if step.get("anchor"):
  212 | if __name__ == "__main__":
```

## `for` — 2 совпадений
```
   32 |             for cand in (old_root, old_cwd):
  203 |     for i, step in enumerate(TOUR_STEPS):
```
