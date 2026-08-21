# grep-таблицы `modules/voice_synth.py`

## `import` — 10 совпадений
```
   13 | import os
   14 | from pathlib import Path
   24 |         import torch
   35 |         import torchaudio
   49 |         from TTS.api import TTS
   68 |         import soundfile as sf
   69 |         from bark import SAMPLE_RATE, generate_audio
   82 |         import pyttsx3
   97 |         from gtts import gTTS
  136 |         import time as _t
```

## `print` — 9 совпадений
```
   40 |         print(f"[voice_synth.silero] {e}")
   59 |         print(f"[voice_synth.xtts] {e}")
   75 |         print(f"[voice_synth.bark] {e}")
   90 |         print(f"[voice_synth.pyttsx3] {e}")
  103 |         print(f"[voice_synth.gtts] {e}")
  167 |         print("[voice_synth] ALL engines failed/unavailable — honest empty return")
  172 |         print(f"[voice_synth] unknown engine={engine}, fallback silero")
  185 |     print("[voice_synth] no engine produced a file — honest empty return")
  195 |     print(f"WAV: {r}, exists: {os.path.exists(r)}")
```

## `except` — 7 совпадений
```
   39 |     except Exception as e:
   58 |     except Exception as e:
   74 |     except Exception as e:
   89 |     except Exception as e:
  102 |     except Exception as e:
  130 |     except Exception:
  159 |         except Exception:
```

## `try` — 7 совпадений
```
   23 |     try:
   48 |     try:
   67 |     try:
   81 |     try:
   96 |     try:
  128 |     try:
  157 |         try:
```

## `def` — 7 совпадений
```
   21 | def _synth_silero(text: str, out_path: str, speaker: str = "aidar") -> bool:
   44 | def _synth_xtts(
   63 | def _synth_bark(
   79 | def _synth_pyttsx3(text: str, out_path: str) -> bool:
   94 | def _synth_gtts(text: str, out_path: str) -> bool:
  107 | def synth(
  156 |     def _produced() -> bool:
```

## `return` — 18 совпадений
```
   38 |         return True
   41 |         return False
   57 |         return True
   60 |         return False
   73 |         return True
   76 |         return False
   88 |             return True
   91 |     return False
  101 |         return os.path.exists(out_path) and os.path.getsize(out_path) > 100
  104 |         return False
  126 |         return ""
  158 |             return os.path.exists(out_path) and os.path.getsize(out_path) > 100
  160 |             return False
  166 |                 return out_path
  168 |         return ""
  177 |         return out_path
  183 |                 return out_path
  186 |     return ""
```

## `if` — 11 совпадений
```
   54 |         if speaker_wav and os.path.exists(speaker_wav):
   87 |         if os.path.exists(out_path) and os.path.getsize(out_path) > 100:
  125 |     if not text or not text.strip():
  135 |     if not out_name:
  162 |     if engine == "auto":
  165 |             if engines[e]() and _produced():
  171 |     if not fn:
  176 |     if ok and _produced():
  181 |         if backup != engine:
  182 |             if engines[backup]() and _produced():
  189 | if __name__ == "__main__":
```

## `for` — 2 совпадений
```
  164 |         for e in ("silero", "xtts", "bark", "pyttsx3", "gtts"):
  180 |     for backup in ("silero", "pyttsx3", "gtts"):
```

## `sf` — 1 совпадений
```
   72 |         sf.write(out_path, audio, SAMPLE_RATE)
```
