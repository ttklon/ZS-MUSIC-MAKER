# ПОСТРОЧНЫЙ ЛИСТИНГ: `ui/karaoke_recorder.py`

**Всего строк:** 154

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 55 | 35.7 |
| blank | 27 | 17.5 |
| docstring | 23 | 14.9 |
| import | 15 | 9.7 |
| try_block | 10 | 6.5 |
| return | 10 | 6.5 |
| branch | 6 | 3.9 |
| def | 5 | 3.2 |
| comment | 2 | 1.3 |
| loop | 1 | 0.6 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v7] karaoke_recorder v4 — караоке-запись с 8 стилями и прогрессом покрытия.
    3 [blank     ] 
    4 [docstring ] Возможности:
    5 [docstring ]   • Показ фразы с подсветкой слова (по времени)
    6 [docstring ]   • Проигрывание бита в наушниках при записи (Pro mode)
    7 [docstring ]   • Метроном по BPM
    8 [docstring ]   • Автосохранение в voice_vault/ с меткой стиля
    9 [docstring ]   • Прогресс: сколько записей по каждому стилю, покрытие фонем
   10 [docstring ] """
   11 [blank     ] 
   12 [import    ] from __future__ import annotations
   13 [blank     ] 
   14 [import    ] import json
   15 [import    ] import os
   16 [import    ] import time
   17 [import    ] from pathlib import Path
   18 [blank     ] 
   19 [code      ] ROOT = Path(__file__).resolve().parents[1]
   20 [code      ] VAULT = ROOT / "voice_vault"
   21 [code      ] VAULT.mkdir(parents=True, exist_ok=True)
   22 [blank     ] 
   23 [blank     ] 
   24 [def       ] def build_metronome(bpm: int, duration_sec: int = 8, sr: int = 44100) -> str:
   25 [docstring ]     """Генерирует WAV с метрономом на BPM."""
   26 [try_block ]     try:
   27 [import    ]         import numpy as np
   28 [import    ]         import soundfile as sf
   29 [blank     ] 
   30 [code      ]         n = int(sr * duration_sec)
   31 [code      ]         y = np.zeros(n, dtype="float32")
   32 [code      ]         beat_samples = int(sr * 60.0 / bpm)
   33 [code      ]         click_dur = int(0.02 * sr)
   34 [comment   ]         # клик — короткий треугольник
   35 [loop      ]         for i in range(0, n, beat_samples):
   36 [branch    ]             if i + click_dur >= n:
   37 [code      ]                 break
   38 [code      ]             t = np.linspace(0, 1, click_dur)
   39 [code      ]             click = np.sin(2 * np.pi * 1200 * t) * np.exp(-t * 30) * 0.5
   40 [code      ]             y[i : i + click_dur] += click.astype("float32")
   41 [code      ]         out = str(VAULT / f"_metronome_{bpm}.wav")
   42 [code      ]         sf.write(out, y, sr)
   43 [return    ]         return out
   44 [try_block ]     except Exception as e:
   45 [code      ]         print(f"[karaoke.metronome] {e}")
   46 [return    ]         return ""
   47 [blank     ] 
   48 [blank     ] 
   49 [def       ] def play_backing_track(track_path: str, in_headphones: bool = True) -> bool:
   50 [docstring ]     """
   51 [docstring ]     Стартует проигрывание бита в наушниках. На Windows — через winsound
   52 [docstring ]     (playAsync), на других системах — через subprocess.
   53 [docstring ]     """
   54 [branch    ]     if not track_path or not os.path.exists(track_path):
   55 [return    ]         return False
   56 [try_block ]     try:
   57 [import    ]         import platform
   58 [blank     ] 
   59 [branch    ]         if platform.system() == "Windows":
   60 [import    ]             import winsound
   61 [blank     ] 
   62 [code      ]             winsound.PlaySound(
   63 [code      ]                 track_path,
   64 [code      ]                 winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP,
   65 [code      ]             )
   66 [branch    ]         else:
   67 [import    ]             import subprocess
   68 [blank     ] 
   69 [code      ]             subprocess.Popen(["aplay", track_path], stderr=subprocess.DEVNULL)
   70 [return    ]         return True
   71 [try_block ]     except Exception as e:
   72 [code      ]         print(f"[karaoke.play_backing_track] {e}")
   73 [return    ]         return False
   74 [blank     ] 
   75 [blank     ] 
   76 [def       ] def record_with_backing(
   77 [code      ]     backing_path: str,
   78 [code      ]     duration_sec: int = 30,
   79 [code      ]     style: str = "conversational",
   80 [code      ]     text: str = "",
   81 [code      ]     sr: int = 44100,
   82 [code      ] ) -> dict:
   83 [docstring ]     """
   84 [docstring ]     Записывает голос с параллельным проигрыванием бита.
   85 [docstring ]     Автоматически кладёт в voice_vault/ с меткой стиля.
   86 [docstring ]     """
   87 [try_block ]     try:
   88 [import    ]         import numpy as np
   89 [import    ]         import sounddevice as sd
   90 [import    ]         import soundfile as sf
   91 [try_block ]     except ImportError:
   92 [return    ]         return {"error": "sounddevice не установлен"}
   93 [blank     ] 
   94 [branch    ]     if backing_path and os.path.exists(backing_path):
   95 [code      ]         play_backing_track(backing_path, in_headphones=True)
   96 [blank     ] 
   97 [code      ]     print(f"[karaoke] Запись {duration_sec} сек в стиле '{style}' — ПОЕХАЛИ!")
   98 [code      ]     audio = sd.rec(int(duration_sec * sr), samplerate=sr, channels=1, dtype="float32")
   99 [code      ]     sd.wait()
  100 [blank     ] 
  101 [code      ]     ts = int(time.time())
  102 [code      ]     out = VAULT / f"rec_{ts}_{style}.wav"
  103 [code      ]     sf.write(str(out), audio.squeeze(), sr)
  104 [blank     ] 
  105 [comment   ]     # Регистрируем в vault_index через voice_convert
  106 [try_block ]     try:
  107 [import    ]         from modules.voice_convert import add_recording
  108 [blank     ] 
  109 [code      ]         add_recording(
  110 [code      ]             str(out),
  111 [code      ]             {
  112 [code      ]                 "style": style,
  113 [code      ]                 "text": text,
  114 [code      ]                 "duration_sec": duration_sec,
  115 [code      ]                 "timestamp": ts,
  116 [code      ]             },
  117 [code      ]         )
  118 [try_block ]     except Exception:
  119 [code      ]         pass
  120 [blank     ] 
  121 [return    ]     return {"ok": True, "path": str(out), "style": style, "duration_sec": duration_sec}
  122 [blank     ] 
  123 [blank     ] 
  124 [def       ] def karaoke_ui(
  125 [code      ]     phrase: str,
  126 [code      ]     bpm: int = 120,
  127 [code      ]     style: str = "conversational",
  128 [code      ]     beat_path: str | None = None,
  129 [code      ] ) -> dict:
  130 [docstring ]     """
  131 [docstring ]     Заглушка для интеграции с v5 Gradio.
  132 [docstring ]     В v7 Wizard использует прямо record_with_backing().
  133 [docstring ]     """
  134 [return    ]     return {
  135 [code      ]         "phrase": phrase,
  136 [code      ]         "bpm": bpm,
  137 [code      ]         "style": style,
  138 [code      ]         "hint": "Слушай бит в наушниках, читай фразу, жми запись.",
  139 [code      ]     }
  140 [blank     ] 
  141 [blank     ] 
  142 [def       ] def get_progress() -> dict:
  143 [docstring ]     """Прогресс по всем 8 стилям — для дашборда."""
  144 [try_block ]     try:
  145 [import    ]         from modules.voice_convert import vault_summary
  146 [blank     ] 
  147 [return    ]         return vault_summary()
  148 [try_block ]     except Exception as e:
  149 [return    ]         return {"error": str(e)}
  150 [blank     ] 
  151 [blank     ] 
  152 [branch    ] if __name__ == "__main__":
  153 [code      ]     print(json.dumps(get_progress(), ensure_ascii=False, indent=2))
  154 [code      ]     print("Метроном для BPM=140:", build_metronome(140, duration_sec=4))
```