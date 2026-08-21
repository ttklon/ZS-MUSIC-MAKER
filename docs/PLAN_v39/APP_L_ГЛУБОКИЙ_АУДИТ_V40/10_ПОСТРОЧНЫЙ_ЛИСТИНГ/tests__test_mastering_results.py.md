# ПОСТРОЧНЫЙ ЛИСТИНГ: `tests/test_mastering_results.py`

**Всего строк:** 43

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 16 | 37.2 |
| blank | 8 | 18.6 |
| docstring | 6 | 14.0 |
| import | 6 | 14.0 |
| comment | 3 | 7.0 |
| stmt | 3 | 7.0 |
| def | 1 | 2.3 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] Mastering results validation (F1, F4)
    3 [docstring ] ====================================
    4 [docstring ] Verifies that the mastering engine produces valid, high-quality audio.
    5 [docstring ] """
    6 [blank     ] 
    7 [import    ] import sys
    8 [import    ] from pathlib import Path
    9 [import    ] import numpy as np
   10 [import    ] import soundfile as sf
   11 [blank     ] 
   12 [code      ] sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
   13 [import    ] from modules.pro_audio_dsp import ProAudioDSP  # pylint: disable=wrong-import-position
   14 [import    ] from tests.test_audio_quality import (  # pylint: disable=wrong-import-position
   15 [code      ]     validate_audio_file,
   16 [code      ] )
   17 [blank     ] 
   18 [blank     ] 
   19 [def       ] def test_pro_mastering_quality_output(tmp_path: Path) -> None:
   20 [docstring ]     """Verifies that ProAudioDSP produces non-clipping, normalized audio."""
   21 [code      ]     sr = 44100
   22 [code      ]     duration = 3.0
   23 [code      ]     time_vec = np.linspace(0, duration, int(sr * duration))
   24 [comment   ]     # Very quiet raw audio to test normalization
   25 [code      ]     audio = np.sin(2 * np.pi * 100 * time_vec) * 0.05 + 0.01
   26 [blank     ] 
   27 [code      ]     in_file = tmp_path / "raw.wav"
   28 [code      ]     out_file = tmp_path / "mastered.wav"
   29 [code      ]     sf.write(str(in_file), audio, sr)
   30 [blank     ] 
   31 [code      ]     res = ProAudioDSP.apply_mastering_chain(
   32 [code      ]         str(in_file), str(out_file), target_lufs=-7.0
   33 [code      ]     )
   34 [stmt      ]     assert res["ok"] is True
   35 [blank     ] 
   36 [comment   ]     # Validate the mastered file
   37 [code      ]     validate_audio_file(str(out_file), expected_duration=duration)
   38 [blank     ] 
   39 [comment   ]     # Verify normalization (should be loud)
   40 [code      ]     data, _ = sf.read(str(out_file))
   41 [code      ]     peak = np.max(np.abs(data))
   42 [stmt      ]     assert peak > 0.6, f"Mastering failed to normalize adequately. Peak: {peak}"
   43 [stmt      ]     assert peak <= 1.0, "Mastering caused clipping!"
```