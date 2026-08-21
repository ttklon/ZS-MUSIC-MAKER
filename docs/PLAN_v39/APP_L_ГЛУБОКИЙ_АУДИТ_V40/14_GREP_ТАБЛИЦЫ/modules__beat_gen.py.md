# grep-таблицы `modules/beat_gen.py`

## `import` — 9 совпадений
```
   11 | import math
   12 | import os
   20 |         import torch
   25 |             import torch_directml  # noqa
   36 |     from audiocraft.models import MusicGen
   71 |     from audiocraft.data.audio import audio_write
   95 |     import torch
   96 |     import torchaudio
   97 |     from audiocraft.data.audio import audio_write
```

## `print` — 1 совпадений
```
  153 |     print(build_prompt(demo_style, user_extra="summer, cars, istanbul"))
```

## `except` — 2 совпадений
```
   28 |         except ImportError:
   31 |     except ImportError:
```

## `try` — 2 совпадений
```
   19 |     try:
   24 |         try:
```

## `def` — 6 совпадений
```
   18 | def _pick_device():
   35 | def _load_model(size: str = "small"):
   50 | def build_prompt(
   64 | def generate_texture(
   87 | def generate_beat(
  132 | def generate_from_samples(
```

## `return` — 9 совпадений
```
   23 |             return "cuda"
   27 |             return "dml"
   30 |         return "cpu"
   32 |         return "cpu"
   47 |     return model, device
   61 |     return base
   84 |     return out_path + ".wav"
  129 |     return out_path + ".wav"
  139 |     return generate_beat(
```

## `if` — 5 совпадений
```
   22 |         if torch.cuda.is_available():
   57 |     if samples_desc:
   59 |     if user_extra:
  105 |     if melody_ref and os.path.exists(melody_ref):
  147 | if __name__ == "__main__":
```

## `for` — 1 совпадений
```
  113 |     for i in range(n_chunks - 1):
```
