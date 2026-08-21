# grep-таблицы `ui/karaoke_recorder.py`

## `import` — 15 совпадений
```
   12 | from __future__ import annotations
   14 | import json
   15 | import os
   16 | import time
   17 | from pathlib import Path
   27 |         import numpy as np
   28 |         import soundfile as sf
   57 |         import platform
   60 |             import winsound
   67 |             import subprocess
   88 |         import numpy as np
   89 |         import sounddevice as sd
   90 |         import soundfile as sf
  107 |         from modules.voice_convert import add_recording
  145 |         from modules.voice_convert import vault_summary
```

## `print` — 5 совпадений
```
   45 |         print(f"[karaoke.metronome] {e}")
   72 |         print(f"[karaoke.play_backing_track] {e}")
   97 |     print(f"[karaoke] Запись {duration_sec} сек в стиле '{style}' — ПОЕХАЛИ!")
  153 |     print(json.dumps(get_progress(), ensure_ascii=False, indent=2))
  154 |     print("Метроном для BPM=140:", build_metronome(140, duration_sec=4))
```

## `except` — 5 совпадений
```
   44 |     except Exception as e:
   71 |     except Exception as e:
   91 |     except ImportError:
  118 |     except Exception:
  148 |     except Exception as e:
```

## `try` — 5 совпадений
```
   26 |     try:
   56 |     try:
   87 |     try:
  106 |     try:
  144 |     try:
```

## `def` — 5 совпадений
```
   24 | def build_metronome(bpm: int, duration_sec: int = 8, sr: int = 44100) -> str:
   49 | def play_backing_track(track_path: str, in_headphones: bool = True) -> bool:
   76 | def record_with_backing(
  124 | def karaoke_ui(
  142 | def get_progress() -> dict:
```

## `return` — 10 совпадений
```
   43 |         return out
   46 |         return ""
   55 |         return False
   70 |         return True
   73 |         return False
   92 |         return {"error": "sounddevice не установлен"}
  121 |     return {"ok": True, "path": str(out), "style": style, "duration_sec": duration_sec}
  134 |     return {
  147 |         return vault_summary()
  149 |         return {"error": str(e)}
```

## `if` — 5 совпадений
```
   36 |             if i + click_dur >= n:
   54 |     if not track_path or not os.path.exists(track_path):
   59 |         if platform.system() == "Windows":
   94 |     if backing_path and os.path.exists(backing_path):
  152 | if __name__ == "__main__":
```

## `for` — 1 совпадений
```
   35 |         for i in range(0, n, beat_samples):
```

## `subprocess` — 2 совпадений
```
   52 |     (playAsync), на других системах — через subprocess.
   69 |             subprocess.Popen(["aplay", track_path], stderr=subprocess.DEVNULL)
```

## `np` — 3 совпадений
```
   31 |         y = np.zeros(n, dtype="float32")
   38 |             t = np.linspace(0, 1, click_dur)
   39 |             click = np.sin(2 * np.pi * 1200 * t) * np.exp(-t * 30) * 0.5
```

## `sf` — 2 совпадений
```
   42 |         sf.write(out, y, sr)
  103 |     sf.write(str(out), audio.squeeze(), sr)
```
