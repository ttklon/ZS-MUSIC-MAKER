# grep-таблицы `tests/test_audio_quality.py`

## `import` — 8 совпадений
```
    7 | import os
    8 | from pathlib import Path
    9 | from typing import Optional
   10 | import numpy as np
   11 | import soundfile as sf
   60 |     import pytest  # pylint: disable=import-outside-toplevel
   75 |     import random
   77 |     from modules import beat_constructor
```

## `def` — 4 совпадений
```
   14 | def validate_audio_file(
   44 | def test_placeholder_audio_quality(tmp_path: Path) -> None:
   58 | def test_clipping_detection(tmp_path: Path) -> None:
   73 | def test_beat_constructor_stereo_width(tmp_path: Path, monkeypatch) -> None:
```

## `if` — 1 совпадений
```
   37 |     if expected_duration:
```

## `with` — 1 совпадений
```
   69 |     with pytest.raises(AssertionError, match="Audio is clipping"):
```

## `assert` — 6 совпадений
```
   25 |     assert os.path.exists(path), f"File not found: {path}"
   30 |     assert peak <= 1.0001, f"Audio is clipping! Peak: {peak}"
   34 |     assert rms > 1e-4, f"Audio is too quiet or silent. RMS: {rms}"
   39 |         assert abs(actual_duration - expected_duration) <= tolerance, (
   99 |     assert audio.shape[1] == 2
  100 |     assert 0.3 <= correlation <= 0.98, (
```

## `np` — 7 совпадений
```
   29 |     peak = np.max(np.abs(data))
   33 |     rms = np.sqrt(np.mean(data**2))
   48 |     time_vec = np.linspace(0, duration, int(sr * duration))
   50 |     audio = np.sin(2 * np.pi * 440 * time_vec) * 0.8
   64 |     audio = np.array([1.5, -1.5, 0.0], dtype=np.float32)
   81 |     np.random.seed(20260822)
   97 |     correlation = float(np.corrcoef(audio[:, 0], audio[:, 1])[0, 1])
```

## `sf` — 4 совпадений
```
   26 |     data, sr = sf.read(path)
   53 |     sf.write(str(path), audio, sr)
   67 |     sf.write(str(path), audio, sr, subtype="FLOAT")
   96 |     audio, _ = sf.read(output, always_2d=True)
```
