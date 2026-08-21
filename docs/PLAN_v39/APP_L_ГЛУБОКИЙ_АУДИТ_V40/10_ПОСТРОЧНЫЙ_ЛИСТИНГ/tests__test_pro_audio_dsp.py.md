# ПОСТРОЧНЫЙ ЛИСТИНГ: `tests/test_pro_audio_dsp.py`

**Всего строк:** 49

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 22 | 44.9 |
| blank | 10 | 20.4 |
| docstring | 5 | 10.2 |
| import | 5 | 10.2 |
| stmt | 5 | 10.2 |
| def | 2 | 4.1 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] Unit tests for ProAudioDSP adhering to Genspark / Claude Code rigorous standards.
    3 [docstring ] """
    4 [blank     ] 
    5 [import    ] from pathlib import Path
    6 [import    ] import sys
    7 [import    ] import numpy as np
    8 [import    ] import soundfile as sf
    9 [blank     ] 
   10 [code      ] sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
   11 [import    ] from modules.pro_audio_dsp import ProAudioDSP  # pylint: disable=wrong-import-position
   12 [blank     ] 
   13 [blank     ] 
   14 [def       ] def test_stereo_phase_alignment() -> None:
   15 [docstring ]     """Test stereo phase alignment and delay correction."""
   16 [code      ]     sr = 22050
   17 [code      ]     t = np.linspace(0, 1, sr)
   18 [code      ]     left = np.sin(2 * np.pi * 440 * t)
   19 [code      ]     right = np.sin(2 * np.pi * 440 * t + 0.1)
   20 [code      ]     stereo = np.stack([left, right], axis=1)
   21 [blank     ] 
   22 [code      ]     aligned = ProAudioDSP.align_stereo_phases(stereo)
   23 [stmt      ]     assert aligned.shape == stereo.shape
   24 [stmt      ]     assert not np.isnan(aligned).any()
   25 [blank     ] 
   26 [blank     ] 
   27 [def       ] def test_mastering_chain(tmp_path: Path) -> None:
   28 [docstring ]     """Test professional mastering pipeline and output file generation."""
   29 [code      ]     sr = 22050
   30 [code      ]     t = np.linspace(0, 2, sr * 2)
   31 [code      ]     audio = (
   32 [code      ]         np.stack(
   33 [code      ]             [np.sin(2 * np.pi * 220 * t), np.cos(2 * np.pi * 220 * t)], axis=1
   34 [code      ]         )
   35 [code      ]         * 0.5
   36 [code      ]     )
   37 [blank     ] 
   38 [code      ]     in_file = tmp_path / "test_in.wav"
   39 [code      ]     out_file = tmp_path / "test_out.wav"
   40 [code      ]     sf.write(str(in_file), audio, sr)
   41 [blank     ] 
   42 [code      ]     res = ProAudioDSP.apply_mastering_chain(
   43 [code      ]         str(in_file), str(out_file), target_lufs=-14.0
   44 [code      ]     )
   45 [stmt      ]     assert res["ok"] is True
   46 [stmt      ]     assert Path(out_file).exists()
   47 [blank     ] 
   48 [code      ]     out_data, _ = sf.read(str(out_file))
   49 [stmt      ]     assert np.max(np.abs(out_data)) <= 1.0
```