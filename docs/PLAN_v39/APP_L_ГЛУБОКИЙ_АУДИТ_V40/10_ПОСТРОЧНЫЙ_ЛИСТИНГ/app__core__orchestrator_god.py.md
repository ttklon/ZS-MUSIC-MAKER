# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/core/orchestrator_god.py`

**Всего строк:** 232

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 100 | 43.1 |
| blank | 30 | 12.9 |
| comment | 28 | 12.1 |
| docstring | 22 | 9.5 |
| return | 14 | 6.0 |
| branch | 12 | 5.2 |
| import | 10 | 4.3 |
| def | 8 | 3.4 |
| try_block | 6 | 2.6 |
| stmt | 1 | 0.4 |
| loop | 1 | 0.4 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """
    3 [docstring ] ZS Music Maker — orchestrator_god.py (GOD MODE)
    4 [docstring ] ========================================================================
    5 [docstring ] Самый продвинутый пайплайн в истории проекта.
    6 [docstring ] Реализован на базе PipelineCore для максимальной надежности.
    7 [docstring ] """
    8 [blank     ] 
    9 [import    ] import os
   10 [import    ] import json
   11 [import    ] from pathlib import Path
   12 [import    ] from typing import Any, Optional
   13 [blank     ] 
   14 [import    ] from app.core.pipeline_core import ZSPipeline, PipelineContext
   15 [import    ] from modules import (
   16 [code      ]     mastering_pro,
   17 [code      ]     voice_cleaner,
   18 [code      ]     beat_constructor,
   19 [code      ]     genre_engine,
   20 [code      ]     ai_arranger,
   21 [code      ]     midi_generator,
   22 [code      ] )
   23 [blank     ] 
   24 [def       ] def _json_safe(obj: Any) -> Any:
   25 [docstring ]     """v34 FIX (P2.29): честная JSON-сериализация вместо default=str.
   26 [blank     ] 
   27 [docstring ]     default=str молча превращал numpy-скаляры и прочие не-JSON объекты в
   28 [docstring ]     строки вида 'np.float32(0.95)' — метрики в project_meta.json переставали
   29 [docstring ]     быть числами и ломали downstream-анализ. Теперь рекурсивно приводим:
   30 [docstring ]     numpy-скаляры → python float/int, Path → str, set/tuple → list,
   31 [docstring ]     остальное неизвестное → str (как и раньше, но только как последний шанс).
   32 [docstring ]     """
   33 [try_block ]     try:
   34 [import    ]         import numpy as _np
   35 [branch    ]         if isinstance(obj, _np.generic):
   36 [return    ]             return obj.item()
   37 [try_block ]     except ImportError:
   38 [code      ]         pass
   39 [branch    ]     if isinstance(obj, dict):
   40 [return    ]         return {str(k): _json_safe(v) for k, v in obj.items()}
   41 [branch    ]     if isinstance(obj, (list, tuple, set)):
   42 [return    ]         return [_json_safe(v) for v in obj]
   43 [branch    ]     if isinstance(obj, Path):
   44 [return    ]         return str(obj)
   45 [return    ]     return obj
   46 [blank     ] 
   47 [blank     ] 
   48 [def       ] def _save_project_meta(project_id: str, data: dict, out_root: Path):
   49 [code      ]     meta_path = out_root / "project_meta.json"
   50 [stmt      ]     with open(meta_path, "w", encoding="utf-8") as f:
   51 [code      ]         json.dump(_json_safe(data), f, ensure_ascii=False, indent=2, default=str)
   52 [blank     ] 
   53 [def       ] def run_god_pipeline(
   54 [code      ]     project_id: str,
   55 [code      ]     wizard_state: Optional[dict] = None,
   56 [code      ]     dry_run: bool = False,
   57 [code      ]     out_root: Optional[Path] = None,
   58 [code      ] ) -> dict:
   59 [docstring ]     """
   60 [docstring ]     Запускает God Mode пайплайн через новое ядро.
   61 [blank     ] 
   62 [docstring ]     v28 (P1): wizard_state теперь Optional — раньше вызов
   63 [docstring ]     run_god_pipeline(pid, None) (например, из GUI без wizard или из
   64 [docstring ]     smoke-теста) мгновенно падал на стадии ai_arrangement с
   65 [docstring ]     "'NoneType' object has no attribute 'get'". Теперь None/пустой
   66 [docstring ]     dict заменяется на безопасный дефолт {genre: drift_phonk} —
   67 [docstring ]     пайплайн доезжает до мастеринга вместо краха на первой стадии.
   68 [docstring ]     """
   69 [branch    ]     if not isinstance(wizard_state, dict):
   70 [code      ]         wizard_state = {}
   71 [code      ]     wizard_state.setdefault("genre", "drift_phonk")
   72 [code      ]     isolated_output = out_root is not None
   73 [branch    ]     if out_root is None:
   74 [code      ]         out_root = Path(__file__).resolve().parents[2] / "output" / project_id
   75 [code      ]     out_root.mkdir(parents=True, exist_ok=True)
   76 [blank     ]     
   77 [comment   ]     # Checkpoints принадлежат текущему out_root. Это предотвращает загрузку
   78 [comment   ]     # старых результатов из output/<project_id>, когда smoke предварительно
   79 [comment   ]     # удалил свой каталог артефактов и запускается повторно.
   80 [code      ]     checkpoint_dir = out_root / "checkpoints"
   81 [code      ]     pipe = ZSPipeline(project_id, wizard_state, checkpoint_dir=checkpoint_dir)
   82 [blank     ]     
   83 [comment   ]     # 1. AI Arrangement
   84 [def       ]     def stage_arr(ctx: PipelineContext):
   85 [code      ]         reg = genre_engine.StyleRegistry()
   86 [code      ]         factory = genre_engine.GenreFactory(reg)
   87 [code      ]         genre_name = ctx.config.get("genre", "drift_phonk")
   88 [code      ]         state = factory.create_wizard_state(genre_name, override=ctx.config)
   89 [code      ]         ctx.shared_data["state"] = state
   90 [code      ]         arranger = ai_arranger.AIArranger()
   91 [return    ]         return arranger.get_structure(state["tags"])
   92 [blank     ]     
   93 [code      ]     pipe.add_stage("ai_arrangement", stage_arr)
   94 [blank     ] 
   95 [comment   ]     # 2. MIDI Generation
   96 [def       ]     def stage_midi(ctx: PipelineContext):
   97 [code      ]         midi_gen = midi_generator.MIDIGenerator()
   98 [code      ]         state = ctx.shared_data["state"]
   99 [return    ]         return {
  100 [code      ]             "ok": True,
  101 [code      ]             "drums": midi_gen.generate_drum_pattern(state["genre"], state["bpm_override"]),
  102 [code      ]             "melody": midi_gen.generate_melody_pattern(state["genre"], "A", "minor", state["bpm_override"])
  103 [code      ]         }
  104 [blank     ]     
  105 [code      ]     pipe.add_stage("midi_generation", stage_midi)
  106 [blank     ] 
  107 [comment   ]     # 3. Pro Audio Generation using CyberSynth Engine for Cyberpunk & Modern Genres
  108 [def       ]     def stage_audio(ctx: PipelineContext):
  109 [code      ]         state = ctx.shared_data["state"]
  110 [code      ]         genre_name = state["genre"]
  111 [code      ]         bpm = state["bpm_override"]
  112 [blank     ]         
  113 [code      ]         out_name = str(out_root / "multi_beat.wav")
  114 [try_block ]         try:
  115 [branch    ]             if "chanson" in genre_name.lower() or "шансон" in genre_name.lower():
  116 [import    ]                 from modules.chanson_engine import ChansonEngine
  117 [code      ]                 engine = ChansonEngine(sample_rate=44100)
  118 [code      ]                 res = engine.synthesize_chanson_track(bpm=max(80, min(bpm, 110)), duration_sec=120, out_path=out_name)
  119 [branch    ]             else:
  120 [import    ]                 from modules.cyber_synth import CyberSynth
  121 [code      ]                 synth = CyberSynth(sample_rate=44100)
  122 [code      ]                 res = synth.synthesize_track(bpm=bpm, duration_sec=120, out_path=out_name)
  123 [blank     ]             
  124 [branch    ]             if res.get("ok"):
  125 [code      ]                 ctx.shared_data["beat_wav"] = out_name
  126 [return    ]                 return out_name
  127 [try_block ]         except Exception as e:
  128 [code      ]             print(f"[orchestrator_god] Engine fallback due to: {e}")
  129 [blank     ] 
  130 [comment   ]         # Fallback to beat_constructor if needed
  131 [code      ]         res = beat_constructor.construct_beat(
  132 [code      ]             groove={}, samples=[], 
  133 [code      ]             style_vector={"target_bpm": bpm, "target_mode": "minor"},
  134 [code      ]             out_name=out_name
  135 [code      ]         )
  136 [code      ]         ctx.shared_data["beat_wav"] = res.get("beat_path")
  137 [return    ]         return res
  138 [blank     ]             
  139 [code      ]     pipe.add_stage("audio_generation", stage_audio)
  140 [blank     ] 
  141 [comment   ]     # 4. Vocal Synthesis & Cleaning (Generates speech/singing if no input vocal)
  142 [def       ]     def stage_vocal(ctx: PipelineContext):
  143 [code      ]         state = ctx.shared_data["state"]
  144 [code      ]         vocal_wav = ctx.config.get("vocal_input_path")
  145 [blank     ]         
  146 [branch    ]         if vocal_wav and os.path.exists(vocal_wav):
  147 [code      ]             clean_vocal_wav = str(out_root / "vocal_cleaned.wav")
  148 [code      ]             voice_cleaner.clean_vocal(vocal_wav, clean_vocal_wav)
  149 [code      ]             ctx.shared_data["vocal_wav"] = clean_vocal_wav
  150 [return    ]             return clean_vocal_wav
  151 [branch    ]         else:
  152 [comment   ]             # v26: Автоматически генерируем текст и озвучиваем его через gTTS для настоящего вокала в миксе!
  153 [try_block ]             try:
  154 [import    ]                 from modules import lyrics_gen, voice_synth
  155 [code      ]                 lyric_res = lyrics_gen.generate_lyrics(theme=state.get("theme", "Владимирский централ"), style_vector={"target_bpm": state.get("bpm_override", 96)})
  156 [code      ]                 text_content = lyric_res.get("lyrics", "Владимирский централ, ветер северный")
  157 [blank     ]                 
  158 [code      ]                 vocal_draft = str(out_root / "vocal_draft.wav")
  159 [code      ]                 os.makedirs(os.path.dirname(vocal_draft), exist_ok=True)
  160 [blank     ]                 
  161 [comment   ]                 # Используем voice_synth.synth для генерации аудио с русского текста
  162 [comment   ]                 # v30 FIX: после фикса честности voice_synth.synth возвращает
  163 [comment   ]                 # "" когда ни один TTS-движок недоступен — обрабатываем это
  164 [comment   ]                 # явно и кладём honest reason в отчёт (раньше стадия молча
  165 [comment   ]                 # возвращала None без объяснения).
  166 [comment   ]                 # v33 FIX (P0, SESSION_LOG v32.3): раньше текст насильно
  167 [comment   ]                 # обрезался до 200 символов (text_content[:200]) — на
  168 [comment   ]                 # 120-секундный трек синтезировалась одна фраза ≈2-3 строки.
  169 [comment   ]                 # Теперь передаём полный текст лирики. Если движок слабый
  170 [comment   ]                 # (pyttsx3/gtts) — он сам прочитает длинный текст; ограничение
  171 [comment   ]                 # оставляем только как мягкий safety-cap на случай мусора.
  172 [code      ]                 vocal_text = text_content if len(text_content) <= 4000 else text_content[:4000]
  173 [code      ]                 synth_path = voice_synth.synth(vocal_text, out_name=str(vocal_draft))
  174 [branch    ]                 if synth_path and os.path.exists(synth_path):
  175 [code      ]                     vocal_draft = synth_path
  176 [code      ]                     ctx.shared_data["vocal_wav"] = vocal_draft
  177 [return    ]                     return vocal_draft
  178 [code      ]                 ctx.shared_data["vocal_status"] = "BLOCKED"
  179 [code      ]                 ctx.shared_data["vocal_reason"] = "no_vocal_engine (silero/xtts/bark/pyttsx3/gtts недоступны)"
  180 [code      ]                 print("[orchestrator_god] vocal synth BLOCKED: no TTS engine available — pipeline продолжает без вокала")
  181 [try_block ]             except Exception as e:
  182 [code      ]                 print(f"[orchestrator_god] Auto-vocal synthesis error: {e}")
  183 [code      ]                 ctx.shared_data["vocal_status"] = "FAILED"
  184 [code      ]                 ctx.shared_data["vocal_reason"] = str(e)
  185 [blank     ] 
  186 [return    ]         return None
  187 [blank     ] 
  188 [code      ]     pipe.add_stage("vocal_cleaning", stage_vocal)
  189 [blank     ] 
  190 [comment   ]     # 5. Professional Mastering
  191 [def       ]     def stage_master(ctx: PipelineContext):
  192 [code      ]         beat_wav = ctx.shared_data.get("beat_wav")
  193 [code      ]         vocal_wav = ctx.shared_data.get("vocal_wav")
  194 [code      ]         master_wav = str(out_root / "masters" / "master_god.wav")
  195 [code      ]         os.makedirs(os.path.dirname(master_wav), exist_ok=True)
  196 [comment   ]         # Вызываем профессиональный мастеринг
  197 [return    ]         return mastering_pro.process_mastering(beat_wav, master_wav, vocal_path=vocal_wav, target_lufs=-12.0)
  198 [blank     ] 
  199 [code      ]     pipe.add_stage("god_mastering_pro", stage_master)
  200 [blank     ] 
  201 [comment   ]     # Интерактивные проекты могут переиспользовать checkpoints. Для явного
  202 [comment   ]     # out_root (smoke/изолированный запуск) этапы всегда пересчитываются: их
  203 [comment   ]     # аудиоартефакты являются частью этого же временного каталога.
  204 [code      ]     final_out = pipe.run(use_checkpoints=not isolated_output)
  205 [blank     ]     
  206 [comment   ]     # Формируем итоговый отчет для совместимости
  207 [code      ]     stages_list = []
  208 [code      ]     total_elapsed = 0.0
  209 [loop      ]     for name, sres in final_out["results"].items():
  210 [code      ]         stages_list.append({
  211 [code      ]             "name": name,
  212 [code      ]             "ok": sres.ok,
  213 [code      ]             "duration_sec": sres.duration_sec,
  214 [code      ]             "output": sres.output,
  215 [code      ]             "reason": sres.error
  216 [code      ]         })
  217 [code      ]         total_elapsed += sres.duration_sec
  218 [blank     ]         
  219 [code      ]     res = {
  220 [code      ]         "project_id": project_id,
  221 [code      ]         "status": final_out["status"],
  222 [code      ]         "god_mode": True,
  223 [code      ]         "elapsed_sec": round(total_elapsed, 2),
  224 [code      ]         "stages": stages_list,
  225 [comment   ]         # v30: честный статус вокала в отчёте (раньше информация терялась)
  226 [code      ]         "vocal_status": pipe.context.shared_data.get("vocal_status", "OK" if pipe.context.shared_data.get("vocal_wav") else "SKIPPED"),
  227 [code      ]         "vocal_reason": pipe.context.shared_data.get("vocal_reason"),
  228 [code      ]         "master_path": str(out_root / "masters" / "master_god.wav") if final_out["status"] == "completed" else None
  229 [code      ]     }
  230 [blank     ]     
  231 [code      ]     _save_project_meta(project_id, res, out_root)
  232 [return    ]     return res
```