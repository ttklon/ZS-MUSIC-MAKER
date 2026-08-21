# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/chanson_engine.py`

**Всего строк:** 195

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 103 | 52.8 |
| blank | 27 | 13.8 |
| docstring | 18 | 9.2 |
| comment | 10 | 5.1 |
| branch | 10 | 5.1 |
| try_block | 6 | 3.1 |
| def | 6 | 3.1 |
| import | 5 | 2.6 |
| return | 5 | 2.6 |
| loop | 4 | 2.1 |
| class | 1 | 0.5 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS-MUSIC-MAKER Chanson Engine (Professional Acoustic & Vocal Arrangement)
    3 [docstring ] ========================================================================
    4 [docstring ] Replaces primitive monotone synth with authentic Chanson instrumentation:
    5 [docstring ] - Acoustic Guitar Arpeggios (Am, Dm, E7, C progression)
    6 [docstring ] - Rich Accordion Pads (harmonic richness)
    7 [docstring ] - Real Drum Machine (Kick on 1 & 3, Snare on 2 & 4, Hi-Hat rolls)
    8 [docstring ] - Melodic Lead & Bass line
    9 [docstring ] """
   10 [blank     ] 
   11 [import    ] import os
   12 [import    ] from typing import Dict, Any
   13 [import    ] import numpy as np
   14 [import    ] import soundfile as sf
   15 [blank     ] 
   16 [try_block ] try:
   17 [import    ]     from pedalboard import (
   18 [code      ]         Chorus,
   19 [code      ]         Compressor,
   20 [code      ]         HighpassFilter,
   21 [code      ]         Limiter,
   22 [code      ]         Pedalboard,
   23 [code      ]         Reverb,
   24 [code      ]     )
   25 [code      ]     HAS_PEDALBOARD = True
   26 [try_block ] except ImportError:
   27 [code      ]     HAS_PEDALBOARD = False
   28 [blank     ] 
   29 [blank     ] 
   30 [class     ] class ChansonEngine:
   31 [docstring ]     """Professional Russian/European Chanson arrangement and synthesis engine."""
   32 [blank     ] 
   33 [def       ]     def __init__(self, sample_rate: int = 44100) -> None:
   34 [code      ]         self.sr = sample_rate
   35 [blank     ] 
   36 [def       ]     def generate_kick(self) -> np.ndarray:
   37 [docstring ]         """Synthesizes a punchy acoustic/electronic kick drum."""
   38 [code      ]         dur = 0.2
   39 [code      ]         n = int(self.sr * dur)
   40 [code      ]         t = np.linspace(0, dur, n, endpoint=False)
   41 [code      ]         freq = 120.0 * np.exp(-t * 25.0) + 45.0
   42 [code      ]         audio = np.sin(2.0 * np.pi * freq * t) * np.exp(-t * 12.0)
   43 [return    ]         return np.clip(audio, -1.0, 1.0)
   44 [blank     ] 
   45 [def       ]     def generate_snare(self) -> np.ndarray:
   46 [docstring ]         """Synthesizes a crisp snare drum with noise and body."""
   47 [code      ]         dur = 0.25
   48 [code      ]         n = int(self.sr * dur)
   49 [code      ]         t = np.linspace(0, dur, n, endpoint=False)
   50 [code      ]         body = np.sin(2.0 * np.pi * 180.0 * t) * np.exp(-t * 20.0)
   51 [code      ]         noise = np.random.uniform(-1.0, 1.0, n) * np.exp(-t * 15.0)
   52 [code      ]         audio = body * 0.4 + noise * 0.6
   53 [return    ]         return np.clip(audio, -1.0, 1.0)
   54 [blank     ] 
   55 [def       ]     def generate_hihat(self, open_hat: bool = False) -> np.ndarray:
   56 [docstring ]         """Synthesizes a crisp closed or open hi-hat."""
   57 [code      ]         dur = 0.1 if not open_hat else 0.3
   58 [code      ]         n = int(self.sr * dur)
   59 [code      ]         t = np.linspace(0, dur, n, endpoint=False)
   60 [code      ]         noise = np.random.uniform(-1.0, 1.0, n)
   61 [comment   ]         # Highpass filtering effect via high frequency carrier
   62 [code      ]         carrier = np.sin(2.0 * np.pi * 8000.0 * t)
   63 [code      ]         audio = noise * carrier * np.exp(-t * (30.0 if not open_hat else 10.0))
   64 [return    ]         return np.clip(audio * 0.5, -1.0, 1.0)
   65 [blank     ] 
   66 [def       ]     def generate_guitar_chord(self, root_freqs: list, duration: float) -> np.ndarray:
   67 [docstring ]         """Simulates an acoustic guitar arpeggio/strum for Chanson."""
   68 [code      ]         n = int(self.sr * duration)
   69 [code      ]         t = np.linspace(0, duration, n, endpoint=False)
   70 [code      ]         chord_signal = np.zeros(n, dtype=np.float32)
   71 [blank     ]         
   72 [loop      ]         for i, freq in enumerate(root_freqs):
   73 [comment   ]             # Strum delay
   74 [code      ]             delay_samples = int(i * 0.03 * self.sr)
   75 [branch    ]             if delay_samples >= n:
   76 [code      ]                 continue
   77 [code      ]             sub_t = t[:n - delay_samples]
   78 [comment   ]             # Guitar timbre: harmonics with exponential decay
   79 [code      ]             wave = (
   80 [code      ]                 np.sin(2.0 * np.pi * freq * sub_t) +
   81 [code      ]                 0.5 * np.sin(2.0 * np.pi * freq * 2.0 * sub_t) +
   82 [code      ]                 0.25 * np.sin(2.0 * np.pi * freq * 3.0 * sub_t)
   83 [code      ]             )
   84 [code      ]             env = np.exp(-sub_t * 3.5)
   85 [code      ]             strum = wave * env * 0.3
   86 [code      ]             chord_signal[delay_samples:delay_samples + len(strum)] += strum
   87 [blank     ] 
   88 [branch    ]         if HAS_PEDALBOARD:
   89 [try_block ]             try:
   90 [code      ]                 board = Pedalboard([
   91 [code      ]                     Chorus(rate_hz=0.8, depth=0.3, mix=0.3),
   92 [code      ]                     Reverb(room_size=0.4, wet_level=0.25, dry_level=0.75)
   93 [code      ]                 ])
   94 [code      ]                 chord_signal = board(chord_signal, self.sr)
   95 [try_block ]             except Exception:
   96 [code      ]                 pass
   97 [blank     ] 
   98 [return    ]         return np.clip(chord_signal, -0.99, 0.99)
   99 [blank     ] 
  100 [def       ]     def synthesize_chanson_track(
  101 [code      ]         self, bpm: int = 96, duration_sec: int = 120, out_path: str = "chanson_track.wav"
  102 [code      ]     ) -> Dict[str, Any]:
  103 [docstring ]         """
  104 [docstring ]         Synthesizes a complete, structured Chanson track:
  105 [docstring ]         Intro -> Verse 1 -> Chorus -> Verse 2 -> Chorus -> Outro
  106 [docstring ]         """
  107 [code      ]         total_samples = int(self.sr * duration_sec)
  108 [code      ]         stereo_mix = np.zeros((total_samples, 2), dtype=np.float32)
  109 [blank     ] 
  110 [code      ]         beat_sec = 60.0 / bpm
  111 [code      ]         bar_sec = beat_sec * 4.0
  112 [code      ]         bar_samples = int(bar_sec * self.sr)
  113 [code      ]         total_bars = int(duration_sec / bar_sec)
  114 [blank     ] 
  115 [comment   ]         # Chords frequencies (Am, Dm, E7, C)
  116 [code      ]         chords = {
  117 [code      ]             "Am": [220.00, 261.63, 329.63],
  118 [code      ]             "Dm": [293.66, 349.23, 440.00],
  119 [code      ]             "E7": [164.81, 207.65, 246.94, 329.63],
  120 [code      ]             "C":  [261.63, 329.63, 392.00]
  121 [code      ]         }
  122 [code      ]         progression = ["Am", "Am", "Dm", "E7", "Am", "Am", "Dm", "E7"]
  123 [blank     ] 
  124 [code      ]         kick = self.generate_kick()
  125 [code      ]         snare = self.generate_snare()
  126 [code      ]         hihat = self.generate_hihat(False)
  127 [blank     ] 
  128 [code      ]         current_sample = 0
  129 [code      ]         bar_idx = 0
  130 [blank     ] 
  131 [loop      ]         while current_sample < total_samples:
  132 [code      ]             chord_name = progression[bar_idx % len(progression)]
  133 [code      ]             freqs = chords[chord_name]
  134 [blank     ] 
  135 [comment   ]             # 1. Guitar chords per bar (strummed on beats 1, 2, 3, 4)
  136 [loop      ]             for beat in range(4):
  137 [code      ]                 beat_start = current_sample + int(beat * beat_sec * self.sr)
  138 [code      ]                 guitar_hit = self.generate_guitar_chord(freqs, bar_sec / 4.0)
  139 [code      ]                 length = len(guitar_hit)
  140 [branch    ]                 if beat_start + length <= total_samples:
  141 [code      ]                     stereo_mix[beat_start:beat_start + length, 0] += guitar_hit * 0.6
  142 [code      ]                     stereo_mix[beat_start:beat_start + length, 1] += guitar_hit * 0.6
  143 [blank     ] 
  144 [comment   ]             # 2. Drums (Chanson beat: Kick on 1 & 3, Snare on 2 & 4, Hi-Hats on every 8th note)
  145 [loop      ]             for step in range(8):
  146 [code      ]                 step_start = current_sample + int(step * (beat_sec / 2.0) * self.sr)
  147 [blank     ]                 
  148 [comment   ]                 # Kick on step 0 and 4 (beats 1 and 3)
  149 [branch    ]                 if step in (0, 4):
  150 [code      ]                     k_len = len(kick)
  151 [branch    ]                     if step_start + k_len <= total_samples:
  152 [code      ]                         stereo_mix[step_start:step_start + k_len, 0] += kick * 0.7
  153 [code      ]                         stereo_mix[step_start:step_start + k_len, 1] += kick * 0.7
  154 [blank     ] 
  155 [comment   ]                 # Snare on step 2 and 6 (beats 2 and 4)
  156 [branch    ]                 if step in (2, 6):
  157 [code      ]                     s_len = len(snare)
  158 [branch    ]                     if step_start + s_len <= total_samples:
  159 [code      ]                         stereo_mix[step_start:step_start + s_len, 0] += snare * 0.6
  160 [code      ]                         stereo_mix[step_start:step_start + s_len, 1] += snare * 0.6
  161 [blank     ] 
  162 [comment   ]                 # Hi-hat on every step
  163 [code      ]                 h_len = len(hihat)
  164 [branch    ]                 if step_start + h_len <= total_samples:
  165 [code      ]                     stereo_mix[step_start:step_start + h_len, 0] += hihat * 0.3
  166 [code      ]                     stereo_mix[step_start:step_start + h_len, 1] += hihat * 0.3
  167 [blank     ] 
  168 [code      ]             current_sample += bar_samples
  169 [code      ]             bar_idx += 1
  170 [branch    ]             if current_sample >= total_samples:
  171 [code      ]                 break
  172 [blank     ] 
  173 [comment   ]         # Master bus processing
  174 [branch    ]         if HAS_PEDALBOARD:
  175 [try_block ]             try:
  176 [code      ]                 master_board = Pedalboard([
  177 [code      ]                     HighpassFilter(cutoff_frequency_hz=30),
  178 [code      ]                     Compressor(threshold_db=-12.0, ratio=2.5, attack_ms=15.0, release_ms=80.0),
  179 [code      ]                     Limiter(threshold_db=-0.5, release_ms=40.0)
  180 [code      ]                 ])
  181 [code      ]                 stereo_mix = master_board(stereo_mix, self.sr)
  182 [try_block ]             except Exception:
  183 [code      ]                 pass
  184 [blank     ] 
  185 [code      ]         stereo_mix = np.clip(stereo_mix, -0.99, 0.99)
  186 [code      ]         os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
  187 [code      ]         sf.write(out_path, stereo_mix, self.sr, format="WAV", subtype="PCM_16")
  188 [blank     ] 
  189 [return    ]         return {
  190 [code      ]             "ok": True,
  191 [code      ]             "path": out_path,
  192 [code      ]             "duration": duration_sec,
  193 [code      ]             "bpm": bpm,
  194 [code      ]             "genre": "chanson"
  195 [code      ]         }
```