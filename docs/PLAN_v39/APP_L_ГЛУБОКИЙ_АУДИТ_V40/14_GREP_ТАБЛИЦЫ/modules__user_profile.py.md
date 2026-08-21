# grep-таблицы `modules/user_profile.py`

## `import` — 4 совпадений
```
   14 | import json
   15 | import time
   16 | from pathlib import Path
  131 |         from modules.voice_convert import vault_summary
```

## `print` — 1 совпадений
```
  157 |     print(json.dumps(get_profile(), indent=2, ensure_ascii=False))
```

## `except` — 2 совпадений
```
   50 |     except Exception:
  144 |     except Exception as e:
```

## `try` — 2 совпадений
```
   44 |     try:
  130 |     try:
```

## `def` — 15 совпадений
```
   37 | def get_profile() -> dict:
   54 | def save_profile(p: dict) -> None:
   61 | def update(**kwargs) -> dict:
   69 | def is_first_run() -> bool:
   73 | def mark_onboarded() -> dict:
   77 | def set_artist_name(name: str) -> dict:
   83 | def get_artist_name() -> str:
   87 | def set_quality_mode(mode: str) -> dict:
   94 | def add_to_history(entry: dict) -> None:
  102 | def get_history(limit: int = 20) -> list:
  106 | def add_favorite_theme(theme: str) -> dict:
  117 | def add_favorite_preset(preset_key: str) -> dict:
  128 | def sync_voice_progress() -> dict:
  148 | def save_last_settings(settings: dict) -> None:
  152 | def get_last_settings() -> dict:
```

## `return` — 17 совпадений
```
   43 |         return p
   49 |         return p
   51 |         return dict(DEFAULT_PROFILE)
   66 |     return p
   70 |     return get_profile().get("first_run", True)
   74 |     return update(first_run=False)
   80 |     return update(artist_name=name)
   84 |     return get_profile().get("artist_name") or "ZSMM Artist"
   91 |     return update(quality_mode=mode)
  103 |     return list(reversed(get_profile().get("history", [])))[:limit]
  108 |         return {"error": "пусто"}
  114 |     return {"ok": True, "themes": p["favorite_themes"]}
  119 |         return {"error": "пусто"}
  125 |     return {"ok": True, "presets": p["favorite_presets"]}
  138 |         return {
  145 |         return {"error": str(e)}
  153 |     return get_profile().get("last_settings", {})
```

## `if` — 7 совпадений
```
   38 |     if not PROFILE_FILE.exists():
   89 |     if mode not in ("fast", "quality", "max"):
  107 |     if not theme:
  110 |     if theme not in p["favorite_themes"]:
  118 |     if not preset_key:
  121 |     if preset_key not in p["favorite_presets"]:
  156 | if __name__ == "__main__":
```

## `for` — 2 совпадений
```
   47 |         for k, v in DEFAULT_PROFILE.items():
   63 |     for k, v in kwargs.items():
```

## `open` — 1 совпадений
```
   45 |         p = json.load(open(PROFILE_FILE, "r", encoding="utf-8"))
```
