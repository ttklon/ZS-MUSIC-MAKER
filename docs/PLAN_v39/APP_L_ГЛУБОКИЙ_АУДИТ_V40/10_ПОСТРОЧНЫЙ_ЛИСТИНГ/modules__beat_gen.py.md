# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/beat_gen.py`

**Всего строк:** 153

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 82 | 53.6 |
| blank | 24 | 15.7 |
| docstring | 11 | 7.2 |
| import | 9 | 5.9 |
| return | 9 | 5.9 |
| def | 6 | 3.9 |
| branch | 6 | 3.9 |
| try_block | 4 | 2.6 |
| comment | 1 | 0.7 |
| loop | 1 | 0.7 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [3b] beat_gen.py — MusicGen Texture Engine (пониженная роль)
    3 [docstring ] На RX 580 4GB используется ТОЛЬКО для:
    4 [docstring ]   • атмосферы, этнических фоновых текстур
    5 [docstring ]   • переходных FX, интро/аутро пэдов
    6 [docstring ]   • набросков альтернативного хука
    7 [docstring ]   • мелодических "затравок"
    8 [docstring ] Основной бит делает beat_constructor.py (сэмпл-ориентированный).
    9 [docstring ] """
   10 [blank     ] 
   11 [import    ] import math
   12 [import    ] import os
   13 [blank     ] 
   14 [code      ] OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "beats")
   15 [comment   ] # v22: ленивое создание (не при импорте)
   16 [blank     ] 
   17 [blank     ] 
   18 [def       ] def _pick_device():
   19 [try_block ]     try:
   20 [import    ]         import torch
   21 [blank     ] 
   22 [branch    ]         if torch.cuda.is_available():
   23 [return    ]             return "cuda"
   24 [try_block ]         try:
   25 [import    ]             import torch_directml  # noqa
   26 [blank     ] 
   27 [return    ]             return "dml"
   28 [try_block ]         except ImportError:
   29 [code      ]             pass
   30 [return    ]         return "cpu"
   31 [try_block ]     except ImportError:
   32 [return    ]         return "cpu"
   33 [blank     ] 
   34 [blank     ] 
   35 [def       ] def _load_model(size: str = "small"):
   36 [import    ]     from audiocraft.models import MusicGen
   37 [blank     ] 
   38 [code      ]     device = _pick_device()
   39 [code      ]     model_name = {
   40 [code      ]         "small": "facebook/musicgen-small",
   41 [code      ]         "melody": "facebook/musicgen-melody",
   42 [code      ]         "medium": "facebook/musicgen-medium",
   43 [code      ]     }.get(size, "facebook/musicgen-small")
   44 [code      ]     model = MusicGen.get_pretrained(
   45 [code      ]         model_name, device="cpu" if device == "dml" else device
   46 [code      ]     )
   47 [return    ]     return model, device
   48 [blank     ] 
   49 [blank     ] 
   50 [def       ] def build_prompt(
   51 [code      ]     style_vector: dict, user_extra: str = "", samples_desc: str = ""
   52 [code      ] ) -> str:
   53 [code      ]     tags = ", ".join(style_vector.get("vibe_tags", []))
   54 [code      ]     bpm = style_vector.get("target_bpm", 128)
   55 [code      ]     mode = style_vector.get("target_mode", "minor")
   56 [code      ]     base = f"{tags}, {bpm} BPM, {mode} key, distorted 808, memphis cowbell, oriental saz melody, aggressive, drift phonk"
   57 [branch    ]     if samples_desc:
   58 [code      ]         base += f", uses samples: {samples_desc}"
   59 [branch    ]     if user_extra:
   60 [code      ]         base += f", {user_extra}"
   61 [return    ]     return base
   62 [blank     ] 
   63 [blank     ] 
   64 [def       ] def generate_texture(
   65 [code      ]     prompt: str,
   66 [code      ]     duration_sec: int = 15,
   67 [code      ]     size: str = "small",
   68 [code      ]     out_name: str = "texture.wav",
   69 [code      ] ) -> str:
   70 [docstring ]     """Генерирует короткую текстуру/FX/пад (для вставки в бит)."""
   71 [import    ]     from audiocraft.data.audio import audio_write
   72 [blank     ] 
   73 [code      ]     model, device = _load_model(size)
   74 [code      ]     model.set_generation_params(duration=duration_sec)
   75 [code      ]     out = model.generate([prompt], progress=True)
   76 [code      ]     out_path = os.path.join(OUTPUT_DIR, out_name.replace(".wav", ""))
   77 [code      ]     audio_write(
   78 [code      ]         out_path,
   79 [code      ]         out[0].cpu(),
   80 [code      ]         model.sample_rate,
   81 [code      ]         strategy="loudness",
   82 [code      ]         loudness_compressor=True,
   83 [code      ]     )
   84 [return    ]     return out_path + ".wav"
   85 [blank     ] 
   86 [blank     ] 
   87 [def       ] def generate_beat(
   88 [code      ]     prompt: str,
   89 [code      ]     duration_sec: int = 90,
   90 [code      ]     melody_ref: str = None,
   91 [code      ]     size: str = "small",
   92 [code      ]     out_name: str = "beat.wav",
   93 [code      ] ) -> str:
   94 [docstring ]     """Полная генерация через MusicGen с continuation stitching (для мощных GPU)."""
   95 [import    ]     import torch
   96 [import    ]     import torchaudio
   97 [import    ]     from audiocraft.data.audio import audio_write
   98 [blank     ] 
   99 [code      ]     model, device = _load_model(size)
  100 [code      ]     chunk = 30
  101 [code      ]     n_chunks = math.ceil(duration_sec / chunk)
  102 [code      ]     model.set_generation_params(duration=chunk)
  103 [blank     ] 
  104 [code      ]     all_wavs = []
  105 [branch    ]     if melody_ref and os.path.exists(melody_ref):
  106 [code      ]         wav_ref, sr_ref = torchaudio.load(melody_ref)
  107 [code      ]         wav_ref = wav_ref.mean(dim=0, keepdim=True)
  108 [code      ]         out = model.generate_with_chroma([prompt], wav_ref[None], sr_ref, progress=True)
  109 [branch    ]     else:
  110 [code      ]         out = model.generate([prompt], progress=True)
  111 [code      ]     all_wavs.append(out[0].cpu())
  112 [blank     ] 
  113 [loop      ]     for i in range(n_chunks - 1):
  114 [code      ]         prev = all_wavs[-1]
  115 [code      ]         model.set_generation_params(duration=chunk)
  116 [code      ]         cont = model.generate_continuation(
  117 [code      ]             prev[None],
  118 [code      ]             prompt=[prompt],
  119 [code      ]             prompt_sample_rate=model.sample_rate,
  120 [code      ]             progress=True,
  121 [code      ]         )
  122 [code      ]         all_wavs.append(cont[0].cpu())
  123 [blank     ] 
  124 [code      ]     full = torch.cat(all_wavs, dim=-1)
  125 [code      ]     out_path = os.path.join(OUTPUT_DIR, out_name.replace(".wav", ""))
  126 [code      ]     audio_write(
  127 [code      ]         out_path, full, model.sample_rate, strategy="loudness", loudness_compressor=True
  128 [code      ]     )
  129 [return    ]     return out_path + ".wav"
  130 [blank     ] 
  131 [blank     ] 
  132 [def       ] def generate_from_samples(
  133 [code      ]     sample_paths: list, style_vector: dict, duration_sec: int = 90
  134 [code      ] ) -> str:
  135 [code      ]     prompt = build_prompt(
  136 [code      ]         style_vector, samples_desc=f"{len(sample_paths)} user samples"
  137 [code      ]     )
  138 [code      ]     ref = sample_paths[0] if sample_paths else None
  139 [return    ]     return generate_beat(
  140 [code      ]         prompt,
  141 [code      ]         duration_sec=duration_sec,
  142 [code      ]         melody_ref=ref,
  143 [code      ]         out_name="beat_from_samples.wav",
  144 [code      ]     )
  145 [blank     ] 
  146 [blank     ] 
  147 [branch    ] if __name__ == "__main__":
  148 [code      ]     demo_style = {
  149 [code      ]         "target_bpm": 129,
  150 [code      ]         "target_mode": "minor",
  151 [code      ]         "vibe_tags": ["phonk/drift", "bass-heavy", "dark", "aggressive"],
  152 [code      ]     }
  153 [code      ]     print(build_prompt(demo_style, user_extra="summer, cars, istanbul"))
```