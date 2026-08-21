# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/mastering_pro.py`

**Всего строк:** 188

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 81 | 43.1 |
| docstring | 27 | 14.4 |
| blank | 27 | 14.4 |
| comment | 12 | 6.4 |
| try_block | 12 | 6.4 |
| branch | 12 | 6.4 |
| import | 8 | 4.3 |
| def | 3 | 1.6 |
| return | 3 | 1.6 |
| stmt | 2 | 1.1 |
| raise | 1 | 0.5 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker — mastering_pro.py (GOD MODE Safe Fallback)
    3 [docstring ] ========================================================================
    4 [docstring ] Профессиональный мастеринг-движок с безопасными фоллбеками при
    5 [docstring ] отсутствии тяжелых библиотек (pyloudnorm, pedalboard).
    6 [blank     ] 
    7 [docstring ] v29 FIX (P1/P2):
    8 [docstring ]   * true-peak ceiling: после LUFS-нормализации возможна перегрузка
    9 [docstring ]     (pyloudnorm warning "Possible clipped samples"). Добавлен
   10 [docstring ]     post-normalization ceiling limiter (-1 dBTP mode для streaming).
   11 [docstring ]   * защита от NaN/Inf в аудио (могло убить mastered.wav).
   12 [docstring ]   * возвращаем реальные output_lufs и output_peak для честного отчёта
   13 [docstring ]     (не только input_lufs).
   14 [docstring ]   * mono → stereo up-mix через дублирование канала (раньше могли
   15 [docstring ]     получить (frames,1) и sf.write писал моно WAV, сбивая God Mode).
   16 [docstring ] """
   17 [blank     ] 
   18 [import    ] import os
   19 [import    ] import numpy as np
   20 [import    ] import soundfile as sf
   21 [blank     ] 
   22 [comment   ] # Безопасный импорт тяжелых библиотек
   23 [try_block ] try:
   24 [import    ]     import pyloudnorm as pyln
   25 [code      ]     HAS_PYLOUDNORM = True
   26 [try_block ] except ImportError:
   27 [code      ]     HAS_PYLOUDNORM = False
   28 [blank     ] 
   29 [try_block ] try:
   30 [import    ]     from pedalboard import (
   31 [code      ]         Chorus,
   32 [code      ]         Compressor,
   33 [code      ]         Distortion,
   34 [code      ]         HighpassFilter,
   35 [code      ]         Limiter,
   36 [code      ]         Pedalboard,
   37 [code      ]     )
   38 [import    ]     from pedalboard.io import AudioFile
   39 [code      ]     HAS_PEDALBOARD = True
   40 [try_block ] except ImportError:
   41 [code      ]     HAS_PEDALBOARD = False
   42 [blank     ] 
   43 [blank     ] 
   44 [def       ] def _sanitize(x: np.ndarray) -> np.ndarray:
   45 [docstring ]     """NaN/Inf → 0 (защита от gain-blow-up при пустых буферах)."""
   46 [branch    ]     if not np.isfinite(x).all():
   47 [code      ]         x = np.nan_to_num(x, nan=0.0, posinf=0.99, neginf=-0.99)
   48 [return    ]     return x
   49 [blank     ] 
   50 [blank     ] 
   51 [def       ] def _apply_ceiling(x: np.ndarray, ceiling_db: float = -1.0) -> np.ndarray:
   52 [docstring ]     """
   53 [docstring ]     Простой look-ahead-free peak ceiling.
   54 [docstring ]     Если pedalboard.Limiter отработал в цепи — это дублирующая страховка
   55 [docstring ]     против post-LUFS overshoot (pyloudnorm.normalize.loudness может
   56 [docstring ]     вывести пики > 1.0 после gain).
   57 [docstring ]     """
   58 [code      ]     ceiling = 10.0 ** (ceiling_db / 20.0)  # -1 dB → ~0.891
   59 [code      ]     peak = float(np.max(np.abs(x))) if x.size else 0.0
   60 [branch    ]     if peak > ceiling and peak > 0:
   61 [code      ]         x = x * (ceiling / peak)
   62 [return    ]     return x
   63 [blank     ] 
   64 [blank     ] 
   65 [def       ] def process_mastering(input_wav: str, output_wav: str, vocal_path: str = None, target_lufs: float = -14.0):
   66 [docstring ]     """
   67 [docstring ]     Профессиональный мастеринг трека с автоматическими фоллбеками.
   68 [docstring ]     Если передан vocal_path, вокал подмешивается к биту перед мастерингом.
   69 [blank     ] 
   70 [docstring ]     v29: добавлен true-peak ceiling (-1 dBTP) и honest output-метрики.
   71 [docstring ]     """
   72 [code      ]     global HAS_PEDALBOARD, HAS_PYLOUDNORM
   73 [branch    ]     if not os.path.exists(input_wav):
   74 [raise     ]         raise FileNotFoundError(f"Input wav not found: {input_wav}")
   75 [blank     ] 
   76 [comment   ]     # v26: Сведение вокала и бита если нужно
   77 [branch    ]     if vocal_path and os.path.exists(vocal_path):
   78 [try_block ]         try:
   79 [import    ]             from pydub import AudioSegment
   80 [code      ]             beat = AudioSegment.from_file(input_wav)
   81 [code      ]             vocal = AudioSegment.from_file(vocal_path)
   82 [comment   ]             # Базовое сведение
   83 [code      ]             combined = beat.overlay(vocal)
   84 [code      ]             temp_mix = output_wav.replace(".wav", "_temp_mix.wav")
   85 [code      ]             combined.export(temp_mix, format="wav")
   86 [code      ]             input_wav = temp_mix
   87 [try_block ]         except Exception as e:
   88 [code      ]             print(f"[mastering_pro] Mix failed: {e}")
   89 [blank     ] 
   90 [code      ]     mastered = None
   91 [code      ]     samplerate = 44100
   92 [code      ]     audio_to_norm = None
   93 [code      ]     engine = "unknown"
   94 [blank     ] 
   95 [branch    ]     if HAS_PEDALBOARD:
   96 [try_block ]         try:
   97 [stmt      ]             with AudioFile(input_wav) as f:
   98 [code      ]                 audio = f.read(f.frames)
   99 [code      ]                 samplerate = f.samplerate
  100 [blank     ] 
  101 [code      ]             board = Pedalboard([
  102 [code      ]                 HighpassFilter(cutoff_frequency_hz=30),
  103 [code      ]                 Distortion(drive_db=2.0),
  104 [code      ]                 Compressor(threshold_db=-18, ratio=2.0, attack_ms=5.0, release_ms=50.0),
  105 [code      ]                 Chorus(rate_hz=0.1, depth=0.1, centre_delay_ms=7.0, feedback=0.0, mix=0.15),
  106 [code      ]                 Limiter(threshold_db=-1.0, release_ms=100.0),  # v29: -1 dBTP streaming ceiling
  107 [code      ]             ])
  108 [code      ]             mastered = board(audio, samplerate)
  109 [code      ]             audio_to_norm = mastered.T
  110 [code      ]             engine = "pedalboard_pro_safe"
  111 [try_block ]         except Exception as e:
  112 [code      ]             print(f"[mastering_pro] Pedalboard execution error: {e}, falling back to numpy/soundfile")
  113 [code      ]             HAS_PEDALBOARD = False
  114 [blank     ] 
  115 [branch    ]     if not HAS_PEDALBOARD:
  116 [code      ]         audio_data, samplerate = sf.read(input_wav, always_2d=True)
  117 [comment   ]         # audio_data is (frames, channels), convert to (channels, frames) for consistency
  118 [code      ]         mastered = audio_data.T
  119 [code      ]         audio_to_norm = audio_data
  120 [code      ]         engine = "numpy_rms_safe"
  121 [blank     ] 
  122 [code      ]     audio_to_norm = _sanitize(np.asarray(audio_to_norm))
  123 [blank     ] 
  124 [comment   ]     # Нормализация громкости
  125 [code      ]     input_lufs = -20.0
  126 [branch    ]     if HAS_PYLOUDNORM:
  127 [try_block ]         try:
  128 [code      ]             meter = pyln.Meter(samplerate)
  129 [code      ]             input_lufs = meter.integrated_loudness(audio_to_norm)
  130 [comment   ]             # v29: подавляем ClippingWarning — мы всё равно снизим потом ceiling'ом
  131 [import    ]             import warnings
  132 [stmt      ]             with warnings.catch_warnings():
  133 [code      ]                 warnings.simplefilter("ignore")
  134 [code      ]                 mastered = pyln.normalize.loudness(audio_to_norm, input_lufs, target_lufs)
  135 [code      ]             mastered = mastered.T  # back to (channels, frames)
  136 [try_block ]         except Exception as e:
  137 [code      ]             print(f"[mastering_pro] pyloudnorm error: {e}, using RMS fallback")
  138 [code      ]             HAS_PYLOUDNORM = False
  139 [blank     ] 
  140 [branch    ]     if not HAS_PYLOUDNORM:
  141 [comment   ]         # Простой RMS-фоллбек нормализации
  142 [code      ]         current_rms = np.sqrt(np.mean(mastered ** 2)) + 1e-12
  143 [code      ]         target_rms = 10.0 ** (target_lufs / 20.0)
  144 [code      ]         gain = target_rms / current_rms
  145 [code      ]         mastered = mastered * min(gain, 5.0)  # ограничение усиления
  146 [blank     ] 
  147 [code      ]     mastered = _sanitize(np.asarray(mastered))
  148 [blank     ] 
  149 [comment   ]     # v29: true-peak ceiling -1 dBTP (streaming/AES стенд, страховка после LUFS)
  150 [code      ]     mastered = _apply_ceiling(mastered, ceiling_db=-1.0)
  151 [blank     ] 
  152 [comment   ]     # Финальный soft clip (страховка на случай числовых артефактов)
  153 [code      ]     mastered = np.clip(mastered, -0.99, 0.99)
  154 [blank     ] 
  155 [comment   ]     # Приведение к (frames, channels) для sf.write
  156 [branch    ]     if mastered.ndim == 2 and mastered.shape[0] < mastered.shape[1]:
  157 [code      ]         mastered = mastered.T
  158 [blank     ] 
  159 [comment   ]     # v29: моно → стерео (God Mode ожидает стерео мастер)
  160 [branch    ]     if mastered.ndim == 1:
  161 [code      ]         mastered = np.stack([mastered, mastered], axis=1)
  162 [branch    ]     elif mastered.ndim == 2 and mastered.shape[1] == 1:
  163 [code      ]         mastered = np.concatenate([mastered, mastered], axis=1)
  164 [blank     ] 
  165 [code      ]     os.makedirs(os.path.dirname(output_wav) or ".", exist_ok=True)
  166 [code      ]     sf.write(output_wav, mastered, samplerate, format="WAV", subtype="PCM_16")
  167 [blank     ] 
  168 [comment   ]     # v29: honest output metrics
  169 [code      ]     output_peak_db = 20.0 * np.log10(float(np.max(np.abs(mastered))) + 1e-12)
  170 [code      ]     output_lufs = None
  171 [branch    ]     if HAS_PYLOUDNORM:
  172 [try_block ]         try:
  173 [code      ]             meter = pyln.Meter(samplerate)
  174 [code      ]             output_lufs = float(meter.integrated_loudness(mastered))
  175 [try_block ]         except Exception:
  176 [code      ]             output_lufs = None
  177 [blank     ] 
  178 [return    ]     return {
  179 [code      ]         "ok": True,
  180 [code      ]         "path": output_wav,
  181 [code      ]         "engine": engine,
  182 [code      ]         "input_lufs": round(float(input_lufs), 2),
  183 [code      ]         "target_lufs": target_lufs,
  184 [code      ]         "output_lufs": round(output_lufs, 2) if output_lufs is not None else None,
  185 [code      ]         "output_peak_db": round(float(output_peak_db), 2),
  186 [code      ]         "channels": int(mastered.shape[1]) if mastered.ndim == 2 else 1,
  187 [code      ]         "sample_rate": int(samplerate),
  188 [code      ]     }
```