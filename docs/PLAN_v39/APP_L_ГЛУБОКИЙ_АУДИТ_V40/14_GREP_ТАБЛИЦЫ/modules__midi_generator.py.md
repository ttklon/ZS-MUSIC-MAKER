# grep-таблицы `modules/midi_generator.py`

## `import` — 4 совпадений
```
   23 | import os
   24 | import random
   31 |     import mido  # type: ignore
   32 |     from mido import Message, MidiFile, MidiTrack  # type: ignore
```

## `print` — 5 совпадений
```
  138 |             print(f"[midi_generator] drum error: {e}")
  196 |             print(f"[midi_generator] melody error: {e}")
  202 |     print("Status:", gen.get_status())
  203 |     print(f"Drum MIDI: {gen.generate_drum_pattern('techno', 128)!r}")
  204 |     print(f"Melody MIDI: {gen.generate_melody_pattern('techno', 'A', 'minor', 128)!r}")
```

## `except` — 3 совпадений
```
   34 | except Exception:  # pragma: no cover
  137 |         except Exception as e:
  195 |         except Exception as e:
```

## `try` — 3 совпадений
```
   30 | try:
   74 |         try:
  159 |         try:
```

## `def` — 5 совпадений
```
   43 |     def __init__(self, output_dir: str = "output/midi"):
   48 |     def _ensure_dir(self) -> None:
   54 |     def get_status() -> dict:
   65 |     def generate_drum_pattern(self, genre: str, bpm: int) -> str:
  144 |     def generate_melody_pattern(
```

## `class` — 1 совпадений
```
   40 | class MIDIGenerator:
```

## `return` — 7 совпадений
```
   56 |         return {
   72 |             return ""  # BLOCKED: mido not installed (honest, non-fatal)
  136 |             return out_path
  139 |             return ""
  157 |             return ""  # BLOCKED: mido not installed
  194 |             return out_path
  197 |             return ""
```

## `if` — 10 совпадений
```
   49 |         if not self._dir_ready:
   71 |         if not _HAS_MIDO:
   86 |             if "techno" in g or "house" in g:
   89 |                     if i % 4 == 0:
   98 |                     if i in (0, 6, 10):
  111 |                     if i == 0 or i == 10:
  124 |                     if i in (0, 8):
  156 |         if not _HAS_MIDO:
  166 |             if (mode or "minor").lower().startswith("min"):
  200 | if __name__ == "__main__":
```

## `for` — 5 совпадений
```
   88 |                 for i in range(16):
   97 |                 for i in range(16):
  110 |                 for i in range(16):
  123 |                 for i in range(16):
  183 |             for step in range(16):
```
