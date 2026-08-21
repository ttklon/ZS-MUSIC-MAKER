# grep-таблицы `tests/test_pro_audio_dsp.py`

## `import` — 5 совпадений
```
    5 | from pathlib import Path
    6 | import sys
    7 | import numpy as np
    8 | import soundfile as sf
   11 | from modules.pro_audio_dsp import ProAudioDSP  # pylint: disable=wrong-import-position
```

## `def` — 2 совпадений
```
   14 | def test_stereo_phase_alignment() -> None:
   27 | def test_mastering_chain(tmp_path: Path) -> None:
```

## `assert` — 5 совпадений
```
   23 |     assert aligned.shape == stereo.shape
   24 |     assert not np.isnan(aligned).any()
   45 |     assert res["ok"] is True
   46 |     assert Path(out_file).exists()
   49 |     assert np.max(np.abs(out_data)) <= 1.0
```

## `np` — 9 совпадений
```
   17 |     t = np.linspace(0, 1, sr)
   18 |     left = np.sin(2 * np.pi * 440 * t)
   19 |     right = np.sin(2 * np.pi * 440 * t + 0.1)
   20 |     stereo = np.stack([left, right], axis=1)
   24 |     assert not np.isnan(aligned).any()
   30 |     t = np.linspace(0, 2, sr * 2)
   32 |         np.stack(
   33 |             [np.sin(2 * np.pi * 220 * t), np.cos(2 * np.pi * 220 * t)], axis=1
   49 |     assert np.max(np.abs(out_data)) <= 1.0
```

## `sf` — 2 совпадений
```
   40 |     sf.write(str(in_file), audio, sr)
   48 |     out_data, _ = sf.read(str(out_file))
```
