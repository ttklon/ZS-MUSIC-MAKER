# ПОСТРОЧНЫЙ ЛИСТИНГ: `tests/test_audio_quality.py`

**Всего строк:** 102

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 37 | 36.3 |
| blank | 21 | 20.6 |
| docstring | 16 | 15.7 |
| import | 8 | 7.8 |
| comment | 8 | 7.8 |
| stmt | 7 | 6.9 |
| def | 4 | 3.9 |
| branch | 1 | 1.0 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] Professional Audio Quality Validation Suite (Category F)
    3 [docstring ] =======================================================
    4 [docstring ] Verifies peak levels, clipping, duration, and signal presence.
    5 [docstring ] """
    6 [blank     ] 
    7 [import    ] import os
    8 [import    ] from pathlib import Path
    9 [import    ] from typing import Optional
   10 [import    ] import numpy as np
   11 [import    ] import soundfile as sf
   12 [blank     ] 
   13 [blank     ] 
   14 [def       ] def validate_audio_file(
   15 [code      ]     path: str, expected_duration: Optional[float] = None, tolerance: float = 0.5
   16 [code      ] ) -> None:
   17 [docstring ]     """
   18 [docstring ]     Core validator for audio artifacts.
   19 [docstring ]     Checks:
   20 [docstring ]     1. File existence and readability.
   21 [docstring ]     2. No digital clipping (peaks <= 1.0).
   22 [docstring ]     3. Signal presence (RMS > 0).
   23 [docstring ]     4. Duration accuracy.
   24 [docstring ]     """
   25 [stmt      ]     assert os.path.exists(path), f"File not found: {path}"
   26 [code      ]     data, sr = sf.read(path)
   27 [blank     ] 
   28 [comment   ]     # 1. Check for clipping (with float precision awareness)
   29 [code      ]     peak = np.max(np.abs(data))
   30 [stmt      ]     assert peak <= 1.0001, f"Audio is clipping! Peak: {peak}"
   31 [blank     ] 
   32 [comment   ]     # 2. Check for silence
   33 [code      ]     rms = np.sqrt(np.mean(data**2))
   34 [stmt      ]     assert rms > 1e-4, f"Audio is too quiet or silent. RMS: {rms}"
   35 [blank     ] 
   36 [comment   ]     # 3. Check duration
   37 [branch    ]     if expected_duration:
   38 [code      ]         actual_duration = len(data) / sr
   39 [stmt      ]         assert abs(actual_duration - expected_duration) <= tolerance, (
   40 [code      ]             f"Duration mismatch: {actual_duration}s != {expected_duration}s"
   41 [code      ]         )
   42 [blank     ] 
   43 [blank     ] 
   44 [def       ] def test_placeholder_audio_quality(tmp_path: Path) -> None:
   45 [docstring ]     """Verifies the validator itself with a generated sine wave."""
   46 [code      ]     sr = 22050
   47 [code      ]     duration = 2.0
   48 [code      ]     time_vec = np.linspace(0, duration, int(sr * duration))
   49 [comment   ]     # Safe sine wave (no clipping)
   50 [code      ]     audio = np.sin(2 * np.pi * 440 * time_vec) * 0.8
   51 [blank     ] 
   52 [code      ]     path = tmp_path / "test.wav"
   53 [code      ]     sf.write(str(path), audio, sr)
   54 [blank     ] 
   55 [code      ]     validate_audio_file(str(path), expected_duration=duration)
   56 [blank     ] 
   57 [blank     ] 
   58 [def       ] def test_clipping_detection(tmp_path: Path) -> None:
   59 [docstring ]     """Verifies that the validator correctly identifies clipping."""
   60 [import    ]     import pytest  # pylint: disable=import-outside-toplevel
   61 [blank     ] 
   62 [code      ]     sr = 22050
   63 [comment   ]     # Create a signal that is clearly clipping
   64 [code      ]     audio = np.array([1.5, -1.5, 0.0], dtype=np.float32)
   65 [code      ]     path = tmp_path / "clipped.wav"
   66 [comment   ]     # Write as float to preserve clipping info for the test
   67 [code      ]     sf.write(str(path), audio, sr, subtype="FLOAT")
   68 [blank     ] 
   69 [stmt      ]     with pytest.raises(AssertionError, match="Audio is clipping"):
   70 [code      ]         validate_audio_file(str(path))
   71 [blank     ] 
   72 [blank     ] 
   73 [def       ] def test_beat_constructor_stereo_width(tmp_path: Path, monkeypatch) -> None:
   74 [docstring ]     """Синтезированный бит должен быть стерео и не сводиться к почти mono."""
   75 [import    ]     import random
   76 [blank     ] 
   77 [import    ]     from modules import beat_constructor
   78 [blank     ] 
   79 [comment   ]     # Фиксируем стохастические drum/noise-слои: границы теста не должны
   80 [comment   ]     # зависеть от случайного выбора хэтов или ghost-notes.
   81 [code      ]     np.random.seed(20260822)
   82 [code      ]     random.seed(20260822)
   83 [code      ]     monkeypatch.setattr(beat_constructor, "OUTPUT_DIR", str(tmp_path))
   84 [blank     ] 
   85 [code      ]     result = beat_constructor.BeatConstructor(
   86 [code      ]         bpm=130,
   87 [code      ]         groove={"hihat_density": 0.8, "swing": 0.1},
   88 [code      ]     ).build_track(
   89 [code      ]         duration_sec=5,
   90 [code      ]         include_intro=False,
   91 [code      ]         include_outro=False,
   92 [code      ]         out_name="stereo_regression.wav",
   93 [code      ]     )
   94 [blank     ] 
   95 [code      ]     output = Path(result["beat_path"])
   96 [code      ]     audio, _ = sf.read(output, always_2d=True)
   97 [code      ]     correlation = float(np.corrcoef(audio[:, 0], audio[:, 1])[0, 1])
   98 [blank     ] 
   99 [stmt      ]     assert audio.shape[1] == 2
  100 [stmt      ]     assert 0.3 <= correlation <= 0.98, (
  101 [code      ]         f"Stereo correlation must remain audible but non-mono; got {correlation:.3f}"
  102 [code      ]     )
```