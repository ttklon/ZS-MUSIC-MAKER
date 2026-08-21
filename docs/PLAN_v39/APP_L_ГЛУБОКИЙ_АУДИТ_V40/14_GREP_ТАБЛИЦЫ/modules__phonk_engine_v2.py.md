# grep-таблицы `modules/phonk_engine_v2.py`

## `import` — 6 совпадений
```
   12 | import numpy as np
   13 | import soundfile as sf
   14 | from app.plugins.base import PluginChain
   15 | from app.plugins.advanced import PhonkDistortion, AntiAINeuroObfuscator
   16 | from modules.phonk_engine import generate_cowbell
   17 | from modules.musical_intelligence import MusicalIntelligence
```

## `def` — 3 совпадений
```
   20 |     def __init__(self, sr: int = 44100, drive_db: float = 25.0, obfuscation: float = 0.3):
   27 |     def generate_808(self, freq: float, duration: float, glide_to: float = None):
   47 |     def create_drift_track(self, project_id: str, bpm: int, key_root: str, mode: str, out_path: str, duration_sec: float = 30.0):
```

## `class` — 1 совпадений
```
   19 | class PhonkEngineV2:
```

## `return` — 2 совпадений
```
   45 |         return (wave * env).astype(np.float32)
   93 |         return out_path
```

## `if` — 4 совпадений
```
   31 |         if glide_to:
   57 |         if not chords_list:
   83 |                 if b_end <= total_samples:
   95 | if __name__ == "__main__":
```

## `for` — 2 совпадений
```
   62 |         for i in range(0, total_samples - self.sr, step_samples * 16):
   78 |             for j in range(4):
```

## `np` — 13 совпадений
```
   29 |         t = np.linspace(0, duration, int(self.sr * duration), endpoint=False)
   33 |             freqs = np.linspace(freq, glide_to, len(t))
   34 |             phase = 2 * np.pi * np.cumsum(freqs) / self.sr
   35 |             wave = np.sin(phase)
   37 |             wave = np.sin(2 * np.pi * freq * t)
   40 |         wave += 0.5 * np.sin(4 * np.pi * freq * t)
   41 |         wave += 0.25 * np.sin(6 * np.pi * freq * t)
   44 |         env = np.exp(-t * 5.0)
   45 |         return (wave * env).astype(np.float32)
   50 |         track = np.zeros((total_samples, 2), dtype=np.float32)
   71 |             bass_stereo = np.stack([bass, bass], axis=1)
   80 |                 bell_stereo = np.stack([bell, bell], axis=1)
   90 |         track = track / (np.max(np.abs(track)) + 1e-9) * 0.9
```

## `sf` — 1 совпадений
```
   92 |         sf.write(out_path, track, self.sr)
```
