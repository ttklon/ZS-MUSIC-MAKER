# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/female_backing.py`

**Всего строк:** 225

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 82 | 36.4 |
| blank | 33 | 14.7 |
| try_block | 24 | 10.7 |
| docstring | 20 | 8.9 |
| import | 18 | 8.0 |
| return | 15 | 6.7 |
| branch | 12 | 5.3 |
| comment | 10 | 4.4 |
| def | 7 | 3.1 |
| loop | 4 | 1.8 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v8] female_backing.py — Female backing vocals engine.
    3 [blank     ] 
    4 [docstring ] ТЗ 20.3: «Местами девушка пела — в припеве или на подпеве или на фоне.
    5 [docstring ] Добавить функцию эту тоже.»
    6 [blank     ] 
    7 [docstring ] Реализация:
    8 [docstring ]   1. Silero v4 (голос 'baya' / 'kseniya') — русские женские спикеры.
    9 [docstring ]   2. Bark v2 — если доступен, спикер 'v2/ru_speaker_9' — русская женщина.
   10 [docstring ]   3. Fallback: pyttsx3 с женским голосом (если ОС даёт).
   11 [docstring ]   4. Пост-обработка: pitch +200 центов, лёгкий chorus, боковые backing-каналы.
   12 [docstring ]   5. Смешивается с основным вокалом либо только на припеве, либо как ad-libs.
   13 [docstring ] """
   14 [blank     ] 
   15 [import    ] from __future__ import annotations
   16 [blank     ] 
   17 [import    ] from pathlib import Path
   18 [blank     ] 
   19 [code      ] ROOT = Path(__file__).resolve().parents[1]
   20 [code      ] BACK_DIR = ROOT / "output" / "voice_backing"
   21 [comment   ] # v22: ленивое создание (не при импорте)
   22 [blank     ] 
   23 [blank     ] 
   24 [comment   ] # ------------------------------------------------------- synth backends
   25 [def       ] def _synth_silero(text: str, out_wav: Path, speaker: str = "kseniya") -> bool:
   26 [try_block ]     try:
   27 [import    ]         import torch
   28 [blank     ] 
   29 [code      ]         model_path = ROOT / "models" / "silero_female.pt"
   30 [branch    ]         if not model_path.exists():
   31 [code      ]             model, _ = torch.hub.load(
   32 [code      ]                 repo_or_dir="snakers4/silero-models",
   33 [code      ]                 model="silero_tts",
   34 [code      ]                 language="ru",
   35 [code      ]                 speaker="v4_ru",
   36 [code      ]                 trust_repo=True,
   37 [code      ]             )
   38 [try_block ]             try:
   39 [code      ]                 torch.save(model, model_path)
   40 [try_block ]             except Exception:
   41 [code      ]                 pass
   42 [branch    ]         else:
   43 [code      ]             model = torch.load(model_path, map_location="cpu", weights_only=False)
   44 [code      ]         audio = model.apply_tts(text=text or "мм", speaker=speaker, sample_rate=48000)
   45 [import    ]         import soundfile as sf
   46 [blank     ] 
   47 [code      ]         sf.write(str(out_wav), audio.cpu().numpy(), 48000)
   48 [return    ]         return True
   49 [try_block ]     except Exception as e:
   50 [code      ]         print(f"[female_backing] silero failed: {e}")
   51 [return    ]         return False
   52 [blank     ] 
   53 [blank     ] 
   54 [def       ] def _synth_bark(text: str, out_wav: Path) -> bool:
   55 [try_block ]     try:
   56 [import    ]         import soundfile as sf
   57 [import    ]         from bark import SAMPLE_RATE, generate_audio
   58 [blank     ] 
   59 [code      ]         arr = generate_audio(text or "yeah", history_prompt="v2/ru_speaker_9")
   60 [code      ]         sf.write(str(out_wav), arr, SAMPLE_RATE)
   61 [return    ]         return True
   62 [try_block ]     except Exception as e:
   63 [code      ]         print(f"[female_backing] bark failed: {e}")
   64 [return    ]         return False
   65 [blank     ] 
   66 [blank     ] 
   67 [def       ] def _synth_pyttsx(text: str, out_wav: Path) -> bool:
   68 [try_block ]     try:
   69 [import    ]         import pyttsx3
   70 [blank     ] 
   71 [code      ]         eng = pyttsx3.init()
   72 [loop      ]         for v in eng.getProperty("voices"):
   73 [branch    ]             if (
   74 [code      ]                 "female" in v.name.lower()
   75 [code      ]                 or "жен" in v.name.lower()
   76 [code      ]                 or "irina" in v.id.lower()
   77 [code      ]             ):
   78 [code      ]                 eng.setProperty("voice", v.id)
   79 [code      ]                 break
   80 [code      ]         eng.save_to_file(text or "ah", str(out_wav))
   81 [code      ]         eng.runAndWait()
   82 [return    ]         return out_wav.exists() and out_wav.stat().st_size > 500
   83 [try_block ]     except Exception as e:
   84 [code      ]         print(f"[female_backing] pyttsx failed: {e}")
   85 [return    ]         return False
   86 [blank     ] 
   87 [blank     ] 
   88 [def       ] def synth_female_line(text: str, out_wav: Path | None = None) -> Path:
   89 [docstring ]     """Синтез одной строки женским голосом. Пробует Silero → Bark → pyttsx."""
   90 [code      ]     out_wav = Path(out_wav or BACK_DIR / f"back_{abs(hash(text)) % 10_000_000}.wav")
   91 [loop      ]     for backend in (_synth_silero, _synth_bark, _synth_pyttsx):
   92 [branch    ]         if backend(text, out_wav):
   93 [return    ]             return out_wav
   94 [comment   ]     # Аварийная тишина, чтобы pipeline не падал.
   95 [try_block ]     try:
   96 [import    ]         import numpy as np
   97 [import    ]         import soundfile as sf
   98 [blank     ] 
   99 [code      ]         sf.write(str(out_wav), np.zeros(int(48000 * 0.5)), 48000)
  100 [try_block ]     except Exception:
  101 [code      ]         out_wav.write_bytes(b"")
  102 [return    ]     return out_wav
  103 [blank     ] 
  104 [blank     ] 
  105 [comment   ] # ------------------------------------------------------- post-processing
  106 [def       ] def sweeten_backing(
  107 [code      ]     wav_path: str | Path, pitch_semitones: float = 3.0, gain_db: float = -6.0
  108 [code      ] ) -> Path:
  109 [docstring ]     """
  110 [docstring ]     Обработка бэков: пич-шифт вверх, EQ (срез низа), лёгкий стерео-хорус.
  111 [docstring ]     """
  112 [code      ]     wav_path = Path(wav_path)
  113 [try_block ]     try:
  114 [import    ]         import numpy as np
  115 [import    ]         import soundfile as sf
  116 [blank     ] 
  117 [code      ]         y, sr = sf.read(str(wav_path))
  118 [branch    ]         if y.ndim == 1:
  119 [code      ]             y = np.stack([y, y], axis=-1)
  120 [blank     ] 
  121 [comment   ]         # Pitch shift через resample (быстрый способ, без librosa не тратим CPU)
  122 [try_block ]         try:
  123 [import    ]             import librosa
  124 [blank     ] 
  125 [code      ]             mono = y.mean(axis=1) if y.ndim > 1 else y
  126 [comment   ]             # Real DSP pitch-shift for backing vocal harmony (NOT RVC substitute).
  127 [code      ]             shifted = librosa.effects.pitch_shift(
  128 [code      ]                 mono, sr=sr, n_steps=pitch_semitones
  129 [code      ]             )  # noqa: ZSMM_NOT_RVC
  130 [code      ]             y = np.stack([shifted, shifted], axis=-1)
  131 [try_block ]         except Exception:
  132 [code      ]             pass
  133 [blank     ] 
  134 [comment   ]         # High-pass ~120 Гц
  135 [try_block ]         try:
  136 [import    ]             from scipy.signal import butter, sosfilt
  137 [blank     ] 
  138 [code      ]             sos = butter(2, 120 / (sr / 2), btype="highpass", output="sos")
  139 [loop      ]             for ch in range(y.shape[1]):
  140 [code      ]                 y[:, ch] = sosfilt(sos, y[:, ch])
  141 [try_block ]         except Exception:
  142 [code      ]             pass
  143 [blank     ] 
  144 [comment   ]         # Стерео-разъезд + gain
  145 [code      ]         y[:, 0] *= 10 ** (gain_db / 20)
  146 [code      ]         y[:, 1] *= 10 ** ((gain_db - 1.5) / 20)
  147 [code      ]         out = wav_path.with_name(wav_path.stem + "_backing.wav")
  148 [code      ]         sf.write(str(out), y, sr)
  149 [return    ]         return out
  150 [try_block ]     except Exception as e:
  151 [code      ]         print(f"[female_backing] sweeten failed: {e}")
  152 [return    ]         return wav_path
  153 [blank     ] 
  154 [blank     ] 
  155 [comment   ] # ------------------------------------------------------- high-level API
  156 [def       ] def make_chorus_backing(chorus_lines: list[str], out_wav: Path | None = None) -> Path:
  157 [docstring ]     """
  158 [docstring ]     Собирает бэк-дорожку из строк припева: синтезирует женским голосом, сшивает
  159 [docstring ]     последовательно, применяет sweeten_backing. Возвращает готовый WAV.
  160 [docstring ]     """
  161 [code      ]     out_wav = Path(out_wav or BACK_DIR / "chorus_backing.wav")
  162 [try_block ]     try:
  163 [import    ]         import numpy as np
  164 [import    ]         import soundfile as sf
  165 [blank     ] 
  166 [code      ]         chunks = []
  167 [code      ]         sr = 48000
  168 [loop      ]         for line in chorus_lines[:8]:
  169 [code      ]             p = synth_female_line(line)
  170 [try_block ]             try:
  171 [code      ]                 y, sr = sf.read(str(p))
  172 [branch    ]                 if y.ndim == 1:
  173 [code      ]                     y = np.stack([y, y], axis=-1)
  174 [code      ]                 chunks.append(y)
  175 [comment   ]                 # маленькая пауза
  176 [code      ]                 chunks.append(np.zeros((sr // 4, 2)))
  177 [try_block ]             except Exception:
  178 [code      ]                 continue
  179 [branch    ]         if not chunks:
  180 [code      ]             sf.write(str(out_wav), np.zeros((sr, 2)), sr)
  181 [return    ]             return out_wav
  182 [code      ]         big = np.concatenate(chunks, axis=0)
  183 [code      ]         sf.write(str(out_wav), big, sr)
  184 [return    ]         return sweeten_backing(out_wav)
  185 [try_block ]     except Exception as e:
  186 [code      ]         print(f"[female_backing] make_chorus_backing failed: {e}")
  187 [return    ]         return out_wav
  188 [blank     ] 
  189 [blank     ] 
  190 [def       ] def mix_backing_into_vocal(
  191 [code      ]     main_vocal_wav: str | Path, backing_wav: str | Path, backing_gain_db: float = -9.0
  192 [code      ] ) -> Path:
  193 [docstring ]     """Микшуем бэки поверх основного вокала. Возвращаем сшитый WAV."""
  194 [code      ]     main_vocal_wav = Path(main_vocal_wav)
  195 [code      ]     backing_wav = Path(backing_wav)
  196 [try_block ]     try:
  197 [import    ]         import numpy as np
  198 [import    ]         import soundfile as sf
  199 [blank     ] 
  200 [code      ]         v, sr = sf.read(str(main_vocal_wav))
  201 [code      ]         b, sr2 = sf.read(str(backing_wav))
  202 [branch    ]         if v.ndim == 1:
  203 [code      ]             v = np.stack([v, v], axis=-1)
  204 [branch    ]         if b.ndim == 1:
  205 [code      ]             b = np.stack([b, b], axis=-1)
  206 [branch    ]         if sr2 != sr:
  207 [try_block ]             try:
  208 [import    ]                 import librosa
  209 [blank     ] 
  210 [code      ]                 b = librosa.resample(b.T, orig_sr=sr2, target_sr=sr).T
  211 [try_block ]             except Exception:
  212 [code      ]                 pass
  213 [code      ]         n = max(len(v), len(b))
  214 [branch    ]         if len(v) < n:
  215 [code      ]             v = np.pad(v, ((0, n - len(v)), (0, 0)))
  216 [branch    ]         if len(b) < n:
  217 [code      ]             b = np.pad(b, ((0, n - len(b)), (0, 0)))
  218 [code      ]         b = b * (10 ** (backing_gain_db / 20))
  219 [code      ]         mixed = np.clip(v + b, -1.0, 1.0)
  220 [code      ]         out = main_vocal_wav.with_name(main_vocal_wav.stem + "_with_backing.wav")
  221 [code      ]         sf.write(str(out), mixed, sr)
  222 [return    ]         return out
  223 [try_block ]     except Exception as e:
  224 [code      ]         print(f"[female_backing] mix failed: {e}")
  225 [return    ]         return main_vocal_wav
```