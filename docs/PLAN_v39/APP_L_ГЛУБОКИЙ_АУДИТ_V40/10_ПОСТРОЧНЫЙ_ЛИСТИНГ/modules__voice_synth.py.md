# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/voice_synth.py`

**Всего строк:** 195

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 63 | 32.3 |
| blank | 32 | 16.4 |
| docstring | 22 | 11.3 |
| return | 18 | 9.2 |
| comment | 16 | 8.2 |
| try_block | 14 | 7.2 |
| branch | 11 | 5.6 |
| import | 10 | 5.1 |
| def | 7 | 3.6 |
| loop | 2 | 1.0 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v7] voice_synth.py — синтез "рыбы" вокала (draft).
    3 [blank     ] 
    4 [docstring ] Движки в порядке приоритета:
    5 [docstring ]   1. silero  — русский v3.1, ~50MB, самый лёгкий, быстрый, локальный
    6 [docstring ]   2. xtts    — Coqui XTTS-v2, многоязычный, качественнее
    7 [docstring ]   3. bark    — bark-full от Suno, самый выразительный, но медленный
    8 [docstring ]   4. pyttsx3 — системный TTS Windows (гарантированный fallback)
    9 [blank     ] 
   10 [docstring ] Все движки graceful: если один не установлен — идём к следующему.
   11 [docstring ] """
   12 [blank     ] 
   13 [import    ] import os
   14 [import    ] from pathlib import Path
   15 [blank     ] 
   16 [code      ] ROOT = Path(__file__).resolve().parents[1]
   17 [code      ] OUT_DIR = ROOT / "output" / "voice_draft"
   18 [comment   ] # v22: ленивое создание (не при импорте)
   19 [blank     ] 
   20 [blank     ] 
   21 [def       ] def _synth_silero(text: str, out_path: str, speaker: str = "aidar") -> bool:
   22 [docstring ]     """Silero v3.1 RU — быстро и локально."""
   23 [try_block ]     try:
   24 [import    ]         import torch
   25 [blank     ] 
   26 [comment   ]         # Silero через torch.hub (первый раз скачивает ~50 MB)
   27 [code      ]         model, _ = torch.hub.load(
   28 [code      ]             repo_or_dir="snakers4/silero-models",
   29 [code      ]             model="silero_tts",
   30 [code      ]             language="ru",
   31 [code      ]             speaker="v3_1_ru",
   32 [code      ]             trust_repo=True,
   33 [code      ]         )
   34 [code      ]         audio = model.apply_tts(text=text, speaker=speaker, sample_rate=48000)
   35 [import    ]         import torchaudio
   36 [blank     ] 
   37 [code      ]         torchaudio.save(out_path, audio.unsqueeze(0), 48000)
   38 [return    ]         return True
   39 [try_block ]     except Exception as e:
   40 [code      ]         print(f"[voice_synth.silero] {e}")
   41 [return    ]         return False
   42 [blank     ] 
   43 [blank     ] 
   44 [def       ] def _synth_xtts(
   45 [code      ]     text: str, out_path: str, language: str = "ru", speaker_wav: str | None = None
   46 [code      ] ) -> bool:
   47 [docstring ]     """Coqui XTTS-v2 — многоязычный, поддерживает клонирование по 6+ сек аудио."""
   48 [try_block ]     try:
   49 [import    ]         from TTS.api import TTS
   50 [blank     ] 
   51 [code      ]         model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
   52 [code      ]         tts = TTS(model_name=model_name)
   53 [code      ]         kwargs = dict(text=text, file_path=out_path, language=language)
   54 [branch    ]         if speaker_wav and os.path.exists(speaker_wav):
   55 [code      ]             kwargs["speaker_wav"] = speaker_wav
   56 [code      ]         tts.tts_to_file(**kwargs)
   57 [return    ]         return True
   58 [try_block ]     except Exception as e:
   59 [code      ]         print(f"[voice_synth.xtts] {e}")
   60 [return    ]         return False
   61 [blank     ] 
   62 [blank     ] 
   63 [def       ] def _synth_bark(
   64 [code      ]     text: str, out_path: str, voice_preset: str = "v2/ru_speaker_0"
   65 [code      ] ) -> bool:
   66 [docstring ]     """Bark-full от Suno — выразительный, но медленный (только под 12GB VRAM)."""
   67 [try_block ]     try:
   68 [import    ]         import soundfile as sf
   69 [import    ]         from bark import SAMPLE_RATE, generate_audio
   70 [blank     ] 
   71 [code      ]         audio = generate_audio(text, history_prompt=voice_preset)
   72 [code      ]         sf.write(out_path, audio, SAMPLE_RATE)
   73 [return    ]         return True
   74 [try_block ]     except Exception as e:
   75 [code      ]         print(f"[voice_synth.bark] {e}")
   76 [return    ]         return False
   77 [blank     ] 
   78 [blank     ] 
   79 [def       ] def _synth_pyttsx3(text: str, out_path: str) -> bool:
   80 [docstring ]     """Гарантированный fallback — системный TTS Windows."""
   81 [try_block ]     try:
   82 [import    ]         import pyttsx3
   83 [blank     ] 
   84 [code      ]         engine = pyttsx3.init()
   85 [code      ]         engine.save_to_file(text, out_path)
   86 [code      ]         engine.runAndWait()
   87 [branch    ]         if os.path.exists(out_path) and os.path.getsize(out_path) > 100:
   88 [return    ]             return True
   89 [try_block ]     except Exception as e:
   90 [code      ]         print(f"[voice_synth.pyttsx3] {e}")
   91 [return    ]     return False
   92 [blank     ] 
   93 [blank     ] 
   94 [def       ] def _synth_gtts(text: str, out_path: str) -> bool:
   95 [docstring ]     """Fallback для Linux через Google TTS (требует интернет)."""
   96 [try_block ]     try:
   97 [import    ]         from gtts import gTTS
   98 [blank     ] 
   99 [code      ]         tts = gTTS(text=text, lang="ru")
  100 [code      ]         tts.save(out_path)
  101 [return    ]         return os.path.exists(out_path) and os.path.getsize(out_path) > 100
  102 [try_block ]     except Exception as e:
  103 [code      ]         print(f"[voice_synth.gtts] {e}")
  104 [return    ]         return False
  105 [blank     ] 
  106 [blank     ] 
  107 [def       ] def synth(
  108 [code      ]     text: str,
  109 [code      ]     engine: str = "silero",
  110 [code      ]     out_name: str | None = None,
  111 [code      ]     speaker_wav: str | None = None,
  112 [code      ]     gender: str = "male",
  113 [code      ] ) -> str:
  114 [docstring ]     """
  115 [docstring ]     Синтезируем draft-вокал. Возвращаем путь к WAV.
  116 [docstring ]     engine: silero | xtts | bark | pyttsx3 | auto
  117 [docstring ]     speaker_wav — путь к записи пользователя для XTTS-клонирования (опционально).
  118 [docstring ]     gender: male | female — v34 FIX (P3.21): выбор голоса для Silero
  119 [docstring ]       (male=aidar, female=kseniya). Раньше был жёстко зашит aidar,
  120 [docstring ]       женский вокал получить было невозможно.
  121 [docstring ]     """
  122 [comment   ]     # v34: gender → silero speaker (остальные движки игнорируют gender —
  123 [comment   ]     # xtts клонирует speaker_wav, bark/pyttsx3 имеют свои голоса)
  124 [code      ]     silero_speaker = "kseniya" if str(gender).lower() in ("female", "f", "ж", "жен") else "aidar"
  125 [branch    ]     if not text or not text.strip():
  126 [return    ]         return ""
  127 [comment   ]     # v22: ленивое создание каталога — только при реальном вызове
  128 [try_block ]     try:
  129 [code      ]         OUT_DIR.mkdir(parents=True, exist_ok=True)
  130 [try_block ]     except Exception:
  131 [code      ]         pass
  132 [comment   ]     # v33 FIX (P0, SESSION_LOG v32.4): дефолтное имя draft.wav молча
  133 [comment   ]     # перезаписывалось при каждом вызове — параллельные/повторные синтезы
  134 [comment   ]     # затирали друг друга. Теперь дефолт уникализируется timestamp'ом.
  135 [branch    ]     if not out_name:
  136 [import    ]         import time as _t
  137 [code      ]         out_name = f"draft_{int(_t.time() * 1000)}.wav"
  138 [code      ]     out_path = str(OUT_DIR / out_name)
  139 [blank     ] 
  140 [code      ]     engines = {
  141 [code      ]         "silero": lambda: _synth_silero(text, out_path, speaker=silero_speaker),
  142 [code      ]         "xtts": lambda: _synth_xtts(text, out_path, speaker_wav=speaker_wav),
  143 [code      ]         "bark": lambda: _synth_bark(text, out_path),
  144 [code      ]         "bark_full": lambda: _synth_bark(text, out_path),
  145 [code      ]         "pyttsx3": lambda: _synth_pyttsx3(text, out_path),
  146 [code      ]         "gtts": lambda: _synth_gtts(text, out_path),
  147 [code      ]     }
  148 [blank     ] 
  149 [comment   ]     # v30 FIX (P0-честность): раньше synth() ВСЕГДА возвращал out_path,
  150 [comment   ]     # даже если НИ ОДИН движок не отработал и файл не создан. Оркестраторы
  151 [comment   ]     # проверяли os.path.exists() и молча теряли вокал, а вызывающий код,
  152 [comment   ]     # доверяющий возвращаемому пути, получал несуществующий файл.
  153 [comment   ]     # Теперь: возвращаем путь ТОЛЬКО если файл реально записан (>100 байт),
  154 [comment   ]     # иначе честный "" — вызывающий код обязан обработать пустой результат.
  155 [blank     ] 
  156 [def       ]     def _produced() -> bool:
  157 [try_block ]         try:
  158 [return    ]             return os.path.exists(out_path) and os.path.getsize(out_path) > 100
  159 [try_block ]         except Exception:
  160 [return    ]             return False
  161 [blank     ] 
  162 [branch    ]     if engine == "auto":
  163 [comment   ]         # Пробуем от быстрого к качественному
  164 [loop      ]         for e in ("silero", "xtts", "bark", "pyttsx3", "gtts"):
  165 [branch    ]             if engines[e]() and _produced():
  166 [return    ]                 return out_path
  167 [code      ]         print("[voice_synth] ALL engines failed/unavailable — honest empty return")
  168 [return    ]         return ""
  169 [blank     ] 
  170 [code      ]     fn = engines.get(engine)
  171 [branch    ]     if not fn:
  172 [code      ]         print(f"[voice_synth] unknown engine={engine}, fallback silero")
  173 [code      ]         fn = engines["silero"]
  174 [blank     ] 
  175 [code      ]     ok = fn()
  176 [branch    ]     if ok and _produced():
  177 [return    ]         return out_path
  178 [blank     ] 
  179 [comment   ]     # цепочка fallback
  180 [loop      ]     for backup in ("silero", "pyttsx3", "gtts"):
  181 [branch    ]         if backup != engine:
  182 [branch    ]             if engines[backup]() and _produced():
  183 [return    ]                 return out_path
  184 [blank     ] 
  185 [code      ]     print("[voice_synth] no engine produced a file — honest empty return")
  186 [return    ]     return ""
  187 [blank     ] 
  188 [blank     ] 
  189 [branch    ] if __name__ == "__main__":
  190 [code      ]     r = synth(
  191 [code      ]         "Привет, это ZS Music Maker v7. Первый тест синтеза.",
  192 [code      ]         engine="pyttsx3",
  193 [code      ]         out_name="test_v7.wav",
  194 [code      ]     )
  195 [code      ]     print(f"WAV: {r}, exists: {os.path.exists(r)}")
```