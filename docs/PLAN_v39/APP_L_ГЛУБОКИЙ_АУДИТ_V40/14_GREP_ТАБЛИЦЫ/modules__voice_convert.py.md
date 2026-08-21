# grep-таблицы `modules/voice_convert.py`

## `import` — 7 совпадений
```
   11 | import json
   12 | import shutil
   13 | from pathlib import Path
  129 |     from modules import rvc_manager
  153 |     from modules import rvc_manager
  166 |     from modules import rvc_manager
  195 |     from modules import rvc_manager
```

## `print` — 1 совпадений
```
  204 |     print(json.dumps(vault_summary(), indent=2, ensure_ascii=False))
```

## `except` — 2 совпадений
```
   53 |         except Exception:
   74 |     except Exception as e:
```

## `try` — 2 совпадений
```
   51 |         try:
   72 |     try:
```

## `def` — 12 совпадений
```
   21 | def _ensure_dirs():
   49 | def _load_index() -> list:
   58 | def _save_index(idx: list):
   65 | def add_recording(wav_path: str, meta: dict) -> dict:
   90 | def vault_summary() -> dict:
  115 | def rate_recording(index: int, quality_score: int) -> dict:
  125 | def train_rvc_model(
  146 | def incremental_finetune(voice_name: str = "my_voice", added_epochs: int = 20) -> dict:
  151 | def get_training_status(voice_name: str = "my_voice") -> dict:
  159 | def convert(
  173 | def polish_vocal(
  188 | def polish_vocal_offline(
```

## `return` — 14 совпадений
```
   52 |             return json.load(open(VOICE_INDEX, "r", encoding="utf-8"))
   54 |             return []
   55 |     return []
   75 |         return {"error": f"copy failed: {e}"}
   87 |     return entry
  103 |     return {
  118 |         return {"error": "индекс вне диапазона"}
  121 |     return {"ok": True, "entry": idx[index]}
  134 |     return {
  148 |     return train_rvc_model(voice_name, epochs=added_epochs, night_mode=False)
  155 |     return rvc_manager.get_state(voice_name)
  168 |     return rvc_manager.infer(
  183 |     return convert(
  198 |     return rvc_manager._fallback_pitch(
```

## `if` — 3 совпадений
```
   50 |     if VOICE_INDEX.exists():
  117 |     if index < 0 or index >= len(idx):
  203 | if __name__ == "__main__":
```

## `for` — 2 совпадений
```
   26 |     for d in (VAULT_DIR, MODELS_DIR, OUTPUT_DIR):
   95 |     for e in idx:
```

## `open` — 2 совпадений
```
   52 |             return json.load(open(VOICE_INDEX, "r", encoding="utf-8"))
   61 |         idx, open(VOICE_INDEX, "w", encoding="utf-8"), ensure_ascii=False, indent=2
```
