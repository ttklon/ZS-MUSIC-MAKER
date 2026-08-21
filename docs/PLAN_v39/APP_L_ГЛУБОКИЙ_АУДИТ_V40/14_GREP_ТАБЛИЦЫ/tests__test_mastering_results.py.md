# grep-таблицы `tests/test_mastering_results.py`

## `import` — 6 совпадений
```
    7 | import sys
    8 | from pathlib import Path
    9 | import numpy as np
   10 | import soundfile as sf
   13 | from modules.pro_audio_dsp import ProAudioDSP  # pylint: disable=wrong-import-position
   14 | from tests.test_audio_quality import (  # pylint: disable=wrong-import-position
```

## `def` — 1 совпадений
```
   19 | def test_pro_mastering_quality_output(tmp_path: Path) -> None:
```

## `assert` — 3 совпадений
```
   34 |     assert res["ok"] is True
   42 |     assert peak > 0.6, f"Mastering failed to normalize adequately. Peak: {peak}"
   43 |     assert peak <= 1.0, "Mastering caused clipping!"
```

## `np` — 3 совпадений
```
   23 |     time_vec = np.linspace(0, duration, int(sr * duration))
   25 |     audio = np.sin(2 * np.pi * 100 * time_vec) * 0.05 + 0.01
   41 |     peak = np.max(np.abs(data))
```

## `sf` — 2 совпадений
```
   29 |     sf.write(str(in_file), audio, sr)
   40 |     data, _ = sf.read(str(out_file))
```
