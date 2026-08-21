# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/voice_convert.py`

**Всего строк:** 204

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 92 | 45.1 |
| blank | 37 | 18.1 |
| docstring | 27 | 13.2 |
| return | 14 | 6.9 |
| def | 12 | 5.9 |
| import | 7 | 3.4 |
| comment | 6 | 2.9 |
| try_block | 4 | 2.0 |
| branch | 3 | 1.5 |
| loop | 2 | 1.0 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v7] voice_convert.py — тонкая обёртка над rvc_manager.
    3 [blank     ] 
    4 [docstring ] Изменения относительно v6:
    5 [docstring ]   • RVC теперь ОСНОВНОЙ путь (см. 20.1 ТЗ).
    6 [docstring ]   • Offline pitch-shift оставлен только как аварийный fallback с WARNING.
    7 [docstring ]   • Тренировку и инференс полностью делегируем rvc_manager.
    8 [docstring ]   • Voice Vault (записи по 8 стилям + phoneme coverage) сохранён.
    9 [docstring ] """
   10 [blank     ] 
   11 [import    ] import json
   12 [import    ] import shutil
   13 [import    ] from pathlib import Path
   14 [blank     ] 
   15 [code      ] ROOT = Path(__file__).resolve().parents[1]
   16 [code      ] VAULT_DIR = ROOT / "voice_vault"
   17 [code      ] MODELS_DIR = ROOT / "models" / "rvc"
   18 [code      ] OUTPUT_DIR = ROOT / "output" / "voice_final"
   19 [blank     ] 
   20 [blank     ] 
   21 [def       ] def _ensure_dirs():
   22 [docstring ]     """v23 FIX: каталоги создаются лениво (не при импорте модуля).
   23 [docstring ]     Раньше import voice_convert создавал voice_vault/, models/rvc/ и
   24 [docstring ]     output/voice_final/ как побочный эффект — это нарушало политику v22
   25 [docstring ]     «no import side effects» и засоряло диск при простом импорте."""
   26 [loop      ]     for d in (VAULT_DIR, MODELS_DIR, OUTPUT_DIR):
   27 [code      ]         d.mkdir(parents=True, exist_ok=True)
   28 [blank     ] 
   29 [blank     ] 
   30 [code      ] VOICE_INDEX = VAULT_DIR / "vault_index.json"
   31 [blank     ] 
   32 [comment   ] # 33 русских фонем-эквивалента для покрытия
   33 [code      ] PHONEMES = list("аоуыэеёиюя") + list("бвгджзйклмнпрстфхцчшщъь")
   34 [blank     ] 
   35 [comment   ] # 8 стилей записи (из ТЗ 3.8)
   36 [code      ] STYLES = [
   37 [code      ]     "slow_clear",
   38 [code      ]     "fast_clear",
   39 [code      ]     "conversational",
   40 [code      ]     "aggressive",
   41 [code      ]     "whisper",
   42 [code      ]     "raspy",
   43 [code      ]     "singing",
   44 [code      ]     "semi_recitative",
   45 [code      ] ]
   46 [blank     ] 
   47 [blank     ] 
   48 [comment   ] # ---------- Voice Vault ----------
   49 [def       ] def _load_index() -> list:
   50 [branch    ]     if VOICE_INDEX.exists():
   51 [try_block ]         try:
   52 [return    ]             return json.load(open(VOICE_INDEX, "r", encoding="utf-8"))
   53 [try_block ]         except Exception:
   54 [return    ]             return []
   55 [return    ]     return []
   56 [blank     ] 
   57 [blank     ] 
   58 [def       ] def _save_index(idx: list):
   59 [code      ]     _ensure_dirs()
   60 [code      ]     json.dump(
   61 [code      ]         idx, open(VOICE_INDEX, "w", encoding="utf-8"), ensure_ascii=False, indent=2
   62 [code      ]     )
   63 [blank     ] 
   64 [blank     ] 
   65 [def       ] def add_recording(wav_path: str, meta: dict) -> dict:
   66 [docstring ]     """Добавить запись в Voice Vault."""
   67 [code      ]     _ensure_dirs()
   68 [code      ]     idx = _load_index()
   69 [code      ]     style = meta.get("style", "unk")
   70 [code      ]     fname = f"rec_{len(idx):04d}_{style}.wav"
   71 [code      ]     dst = VAULT_DIR / fname
   72 [try_block ]     try:
   73 [code      ]         shutil.copy(wav_path, dst)
   74 [try_block ]     except Exception as e:
   75 [return    ]         return {"error": f"copy failed: {e}"}
   76 [code      ]     entry = {
   77 [code      ]         "file": fname,
   78 [code      ]         "path": str(dst),
   79 [code      ]         "style": style,
   80 [code      ]         "text": meta.get("text", ""),
   81 [code      ]         "duration_sec": float(meta.get("duration_sec", 0)),
   82 [code      ]         "quality_score": meta.get("quality_score"),
   83 [code      ]         "timestamp": meta.get("timestamp"),
   84 [code      ]     }
   85 [code      ]     idx.append(entry)
   86 [code      ]     _save_index(idx)
   87 [return    ]     return entry
   88 [blank     ] 
   89 [blank     ] 
   90 [def       ] def vault_summary() -> dict:
   91 [docstring ]     """Сводка по vault: сколько минут, покрытие фонем, рекомендации."""
   92 [code      ]     idx = _load_index()
   93 [code      ]     by_style = {}
   94 [code      ]     total_sec = 0
   95 [loop      ]     for e in idx:
   96 [code      ]         by_style[e.get("style", "unknown")] = (
   97 [code      ]             by_style.get(e.get("style", "unknown"), 0) + 1
   98 [code      ]         )
   99 [code      ]         total_sec += float(e.get("duration_sec", 0))
  100 [code      ]     text = " ".join(e.get("text", "") for e in idx).lower()
  101 [code      ]     covered = [p for p in PHONEMES if p in text]
  102 [code      ]     missing = [p for p in PHONEMES if p not in text]
  103 [return    ]     return {
  104 [code      ]         "recordings": len(idx),
  105 [code      ]         "total_minutes": round(total_sec / 60, 2),
  106 [code      ]         "by_style": by_style,
  107 [code      ]         "ready_for_training": total_sec >= 300,  # 5 минут — минимум
  108 [code      ]         "recommended_for_full": total_sec >= 600,  # 10 минут — идеал
  109 [code      ]         "phoneme_coverage_pct": round(len(covered) / len(PHONEMES) * 100, 1),
  110 [code      ]         "missing_phonemes": missing,
  111 [code      ]         "recommended_next_styles": [s for s in STYLES if by_style.get(s, 0) < 3],
  112 [code      ]     }
  113 [blank     ] 
  114 [blank     ] 
  115 [def       ] def rate_recording(index: int, quality_score: int) -> dict:
  116 [code      ]     idx = _load_index()
  117 [branch    ]     if index < 0 or index >= len(idx):
  118 [return    ]         return {"error": "индекс вне диапазона"}
  119 [code      ]     idx[index]["quality_score"] = quality_score
  120 [code      ]     _save_index(idx)
  121 [return    ]     return {"ok": True, "entry": idx[index]}
  122 [blank     ] 
  123 [blank     ] 
  124 [comment   ] # ---------- Training (делегируем rvc_manager) ----------
  125 [def       ] def train_rvc_model(
  126 [code      ]     voice_name: str = "my_voice", epochs: int = 100, night_mode: bool = False
  127 [code      ] ) -> dict:
  128 [docstring ]     """Обучение RVC-модели. В v7 — через rvc_manager (фоново, с прогрессом)."""
  129 [import    ]     from modules import rvc_manager
  130 [blank     ] 
  131 [code      ]     trainer = rvc_manager.RVCTrainer()
  132 [code      ]     job = trainer.train(voice_name=voice_name, epochs=epochs, night_mode=night_mode)
  133 [comment   ]     # ждать НЕ надо в UI — прогресс отдаётся через колбэки
  134 [return    ]     return {
  135 [code      ]         "ok": True,
  136 [code      ]         "job_started": True,
  137 [code      ]         "voice_name": voice_name,
  138 [code      ]         "backend": trainer.backend.kind,
  139 [code      ]         "fork": trainer.backend.fork,
  140 [code      ]         "epochs": job.epochs,
  141 [code      ]         "device": job.device,
  142 [code      ]         "note": "Обучение идёт в фоне. Смотри voice_convert.get_training_status()",
  143 [code      ]     }
  144 [blank     ] 
  145 [blank     ] 
  146 [def       ] def incremental_finetune(voice_name: str = "my_voice", added_epochs: int = 20) -> dict:
  147 [docstring ]     """Инкрементальное дообучение по новым записям."""
  148 [return    ]     return train_rvc_model(voice_name, epochs=added_epochs, night_mode=False)
  149 [blank     ] 
  150 [blank     ] 
  151 [def       ] def get_training_status(voice_name: str = "my_voice") -> dict:
  152 [docstring ]     """Прогресс текущего обучения (для UI)."""
  153 [import    ]     from modules import rvc_manager
  154 [blank     ] 
  155 [return    ]     return rvc_manager.get_state(voice_name)
  156 [blank     ] 
  157 [blank     ] 
  158 [comment   ] # ---------- Conversion ----------
  159 [def       ] def convert(
  160 [code      ]     input_wav: str,
  161 [code      ]     voice_name: str = "my_voice",
  162 [code      ]     pitch_shift: int = 0,
  163 [code      ]     out_name: str = "converted.wav",
  164 [code      ] ) -> str:
  165 [docstring ]     """RVC-инференс. Основной путь v7."""
  166 [import    ]     from modules import rvc_manager
  167 [blank     ] 
  168 [return    ]     return rvc_manager.infer(
  169 [code      ]         input_wav, voice_name=voice_name, pitch_shift=pitch_shift, out_name=out_name
  170 [code      ]     )
  171 [blank     ] 
  172 [blank     ] 
  173 [def       ] def polish_vocal(
  174 [code      ]     user_vocal_path: str,
  175 [code      ]     voice_name: str = "my_voice",
  176 [code      ]     out_name: str = "polished_vocal.wav",
  177 [code      ] ) -> str:
  178 [docstring ]     """
  179 [docstring ]     ProVoice Mode: пользователь сам записал вокал под бит.
  180 [docstring ]     RVC полирует — стабилизирует тембр, добавляет ровности, но сохраняет
  181 [docstring ]     живое дыхание и микро-фальшь пользователя.
  182 [docstring ]     """
  183 [return    ]     return convert(
  184 [code      ]         user_vocal_path, voice_name=voice_name, pitch_shift=0, out_name=out_name
  185 [code      ]     )
  186 [blank     ] 
  187 [blank     ] 
  188 [def       ] def polish_vocal_offline(
  189 [code      ]     user_vocal_path: str, out_name: str = "polished_offline.wav", n_steps: int = 0
  190 [code      ] ) -> str:
  191 [docstring ]     """
  192 [docstring ]     ⚠ ПОСЛЕДНЯЯ ЛИНИЯ ОБОРОНЫ. Используется ТОЛЬКО когда RVC полностью
  193 [docstring ]     недоступен. НЕ является основным путём в v7.
  194 [docstring ]     """
  195 [import    ]     from modules import rvc_manager
  196 [blank     ] 
  197 [code      ]     _ensure_dirs()
  198 [return    ]     return rvc_manager._fallback_pitch(
  199 [code      ]         user_vocal_path, str(OUTPUT_DIR / out_name), n_steps
  200 [code      ]     )
  201 [blank     ] 
  202 [blank     ] 
  203 [branch    ] if __name__ == "__main__":
  204 [code      ]     print(json.dumps(vault_summary(), indent=2, ensure_ascii=False))
```