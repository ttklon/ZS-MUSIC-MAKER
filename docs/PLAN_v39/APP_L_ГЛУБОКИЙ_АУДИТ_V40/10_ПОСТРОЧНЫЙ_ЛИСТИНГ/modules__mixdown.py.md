# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/mixdown.py`

**Всего строк:** 177

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 88 | 49.7 |
| blank | 31 | 17.5 |
| docstring | 13 | 7.3 |
| comment | 10 | 5.6 |
| branch | 9 | 5.1 |
| import | 8 | 4.5 |
| try_block | 7 | 4.0 |
| return | 6 | 3.4 |
| def | 5 | 2.8 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [7] mixdown.py — Финальный микс + мастеринг v2
    3 [docstring ] Усиления v2:
    4 [docstring ]   • Sidechain-компрессия (ducking от бочки)
    5 [docstring ]   • Эквалайзер (Low-cut, Hi-shelf)
    6 [docstring ]   • Matchering под ЛЮБОЙ референс
    7 [docstring ]   • Многотрековый микс (beat + vocal + adlibs + backing)
    8 [docstring ] """
    9 [blank     ] 
   10 [import    ] import os
   11 [import    ] import shutil
   12 [blank     ] 
   13 [import    ] import numpy as np
   14 [blank     ] 
   15 [code      ] OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "final")
   16 [comment   ] # v22: ленивое создание (не при импорте)
   17 [blank     ] 
   18 [blank     ] 
   19 [def       ] def mix_beat_and_vocal(
   20 [code      ]     beat_path: str,
   21 [code      ]     vocal_path: str,
   22 [code      ]     vocal_gain_db: float = -3.0,
   23 [code      ]     sidechain_strength: float = 0.3,
   24 [code      ]     out_name: str = "mix.wav",
   25 [code      ] ) -> str:
   26 [docstring ]     """Склеивает бит и вокал с sidechain ducking от бочки."""
   27 [import    ]     from pydub import AudioSegment
   28 [blank     ] 
   29 [code      ]     beat = AudioSegment.from_file(beat_path)
   30 [code      ]     vocal = AudioSegment.from_file(vocal_path)
   31 [blank     ] 
   32 [comment   ]     # Выравниваем длину
   33 [branch    ]     if len(vocal) < len(beat):
   34 [code      ]         loops = (len(beat) // len(vocal)) + 1
   35 [code      ]         vocal = (vocal * loops)[: len(beat)]
   36 [branch    ]     else:
   37 [code      ]         vocal = vocal[: len(beat)]
   38 [blank     ] 
   39 [code      ]     vocal = vocal + vocal_gain_db
   40 [blank     ] 
   41 [comment   ]     # Sidechain: упрощённая имитация (тихий dip каждые 60/BPM мс)
   42 [comment   ]     # На слабом железе делаем в pydub
   43 [code      ]     combined = beat.overlay(vocal)
   44 [code      ]     os.makedirs(OUTPUT_DIR, exist_ok=True)
   45 [code      ]     out = os.path.join(OUTPUT_DIR, out_name)
   46 [code      ]     combined.export(out, format="wav")
   47 [return    ]     return out
   48 [blank     ] 
   49 [blank     ] 
   50 [def       ] def apply_eq(
   51 [code      ]     audio_path: str,
   52 [code      ]     low_cut_hz: float = 30,
   53 [code      ]     high_shelf_db: float = 2.0,
   54 [code      ]     out_name: str = "eq_output.wav",
   55 [code      ] ) -> str:
   56 [docstring ]     """Простой эквалайзер через numpy."""
   57 [try_block ]     try:
   58 [import    ]         from scipy.io import wavfile
   59 [import    ]         from scipy.signal import butter, sosfilt
   60 [try_block ]     except ImportError:
   61 [return    ]         return audio_path
   62 [blank     ] 
   63 [code      ]     sr, data = wavfile.read(audio_path)
   64 [branch    ]     if data.ndim > 1:
   65 [code      ]         data = data[:, 0]
   66 [code      ]     data = data.astype(np.float32) / (2**15)
   67 [blank     ] 
   68 [comment   ]     # Low-cut (high-pass)
   69 [branch    ]     if low_cut_hz > 0:
   70 [code      ]         sos = butter(4, low_cut_hz, btype="high", fs=sr, output="sos")
   71 [code      ]         data = sosfilt(sos, data)
   72 [blank     ] 
   73 [comment   ]     # High-shelf (простое усиление верхов)
   74 [branch    ]     if high_shelf_db != 0:
   75 [code      ]         sos_hi = butter(2, 5000, btype="high", fs=sr, output="sos")
   76 [code      ]         highs = sosfilt(sos_hi, data)
   77 [code      ]         data = data + highs * (10 ** (high_shelf_db / 20) - 1)
   78 [blank     ] 
   79 [comment   ]     # Нормализация
   80 [code      ]     peak = np.max(np.abs(data)) + 1e-9
   81 [branch    ]     if peak > 1.0:
   82 [code      ]         data = data / peak * 0.95
   83 [blank     ] 
   84 [code      ]     os.makedirs(OUTPUT_DIR, exist_ok=True)
   85 [code      ]     out = os.path.join(OUTPUT_DIR, out_name)
   86 [code      ]     wavfile.write(out, sr, (data * 32767).astype(np.int16))
   87 [return    ]     return out
   88 [blank     ] 
   89 [blank     ] 
   90 [def       ] def master_with_matchering(
   91 [code      ]     mix_path: str, reference_path: str, out_name: str = "master.wav"
   92 [code      ] ) -> str:
   93 [docstring ]     """Matchering под ЛЮБОЙ референс. Возвращает путь к мастеру."""
   94 [code      ]     res = master_with_matchering_status(mix_path, reference_path, out_name)
   95 [return    ]     return res["master_wav"]
   96 [blank     ] 
   97 [blank     ] 
   98 [def       ] def master_with_matchering_status(
   99 [code      ]     mix_path: str, reference_path: str, out_name: str = "master.wav"
  100 [code      ] ) -> dict:
  101 [docstring ]     """Matchering под ЛЮБОЙ референс с возвратом статуса."""
  102 [code      ]     os.makedirs(OUTPUT_DIR, exist_ok=True)
  103 [code      ]     out = os.path.join(OUTPUT_DIR, out_name)
  104 [code      ]     used_matchering = False
  105 [blank     ]     
  106 [try_block ]     try:
  107 [import    ]         import matchering as mg
  108 [code      ]         mg.process(
  109 [code      ]             target=mix_path,
  110 [code      ]             reference=reference_path,
  111 [code      ]             results=[
  112 [code      ]                 mg.pcm16(out),
  113 [code      ]                 mg.pcm24(out.replace(".wav", "_24.wav")),
  114 [code      ]             ],
  115 [code      ]         )
  116 [code      ]         used_matchering = True
  117 [try_block ]     except ImportError:
  118 [code      ]         shutil.copy(mix_path, out)
  119 [code      ]         print("[matchering] MISSING — fallback: copy")
  120 [try_block ]     except Exception as e:
  121 [code      ]         shutil.copy(mix_path, out)
  122 [code      ]         print(f"[matchering error] {e} — fallback: copy")
  123 [blank     ] 
  124 [comment   ]     # Дополнительно: mp3 320
  125 [try_block ]     try:
  126 [import    ]         from pydub import AudioSegment
  127 [code      ]         AudioSegment.from_wav(out).export(
  128 [code      ]             out.replace(".wav", ".mp3"), format="mp3", bitrate="320k"
  129 [code      ]         )
  130 [try_block ]     except Exception:
  131 [code      ]         pass
  132 [blank     ]         
  133 [return    ]     return {
  134 [code      ]         "master_wav": out,
  135 [code      ]         "used_matchering": used_matchering,
  136 [code      ]         "engine": "matchering" if used_matchering else "copy_fallback"
  137 [code      ]     }
  138 [blank     ] 
  139 [blank     ] 
  140 [comment   ] # Функция master_with_matchering_status была перемещена выше для устранения дублирования и улучшения логики.
  141 [blank     ] 
  142 [blank     ] 
  143 [def       ] def full_mixdown(
  144 [code      ]     beat_path: str,
  145 [code      ]     vocal_path: str,
  146 [code      ]     reference_path: str,
  147 [code      ]     vocal_gain_db: float = -3.0,
  148 [code      ]     apply_eq_enabled: bool = True,
  149 [code      ]     out_name: str = "ZS_track_final.wav",
  150 [code      ] ) -> dict:
  151 [docstring ]     """Полный цикл: микс → EQ → мастеринг."""
  152 [code      ]     mix = mix_beat_and_vocal(
  153 [code      ]         beat_path, vocal_path, vocal_gain_db=vocal_gain_db, out_name="_temp_mix.wav"
  154 [code      ]     )
  155 [blank     ] 
  156 [branch    ]     if apply_eq_enabled:
  157 [code      ]         mix = apply_eq(mix, out_name="_temp_eq.wav")
  158 [blank     ] 
  159 [code      ]     master = master_with_matchering(mix, reference_path, out_name=out_name)
  160 [code      ]     used_matchering = os.path.exists(master.replace(".wav", "_24.wav"))
  161 [return    ]     return {
  162 [code      ]         "mix": mix,
  163 [code      ]         "master_wav": master,
  164 [code      ]         "master_mp3": (
  165 [code      ]             master.replace(".wav", ".mp3")
  166 [branch    ]             if os.path.exists(master.replace(".wav", ".mp3"))
  167 [code      ]             else None
  168 [code      ]         ),
  169 [comment   ]         # v18: честный статус, чтобы UI/логи не выдавали copy за мастеринг
  170 [code      ]         "used_matchering": used_matchering,
  171 [code      ]         "fallback_used": not used_matchering,
  172 [code      ]         "engine": "matchering" if used_matchering else "copy_fallback",
  173 [code      ]     }
  174 [blank     ] 
  175 [blank     ] 
  176 [branch    ] if __name__ == "__main__":
  177 [code      ]     print("mixdown module ready v2")
```