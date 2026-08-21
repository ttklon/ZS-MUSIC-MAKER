# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/core/orchestrator_ai.py`

**Всего строк:** 470

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 267 | 56.8 |
| branch | 51 | 10.9 |
| return | 50 | 10.6 |
| blank | 27 | 5.7 |
| try_block | 24 | 5.1 |
| import | 23 | 4.9 |
| def | 18 | 3.8 |
| docstring | 6 | 1.3 |
| loop | 2 | 0.4 |
| comment | 1 | 0.2 |
| stmt | 1 | 0.2 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """ZS Music Maker - app/core/orchestrator_ai.py (v38 GOD MODE 4.0 AI)"""
    3 [import    ] from __future__ import annotations
    4 [import    ] import json, math, shutil
    5 [import    ] from pathlib import Path
    6 [import    ] from app.core.logger import app_logger
    7 [import    ] from app.ai.sequential_runner import SequentialAIRunner, AIStage
    8 [import    ] from app.ai import prompts as P
    9 [import    ] from app.ai import llm_service as LLM
   10 [import    ] from app.ai.quality import (
   11 [code      ]     validate_audio_artifact,
   12 [code      ]     validate_lyrics,
   13 [code      ]     validate_metadata_json,
   14 [code      ]     validate_rvc_artifact,
   15 [code      ]     validate_stereo_texture,
   16 [code      ]     validate_vocal_artifact,
   17 [code      ] )
   18 [import    ] from modules.artist_dossier import DossierManager
   19 [blank     ] 
   20 [blank     ] 
   21 [def       ] def _slug(name: str) -> str:
   22 [import    ]     import re
   23 [code      ]     s = re.sub(r"[^A-Za-z0-9а-яА-ЯёЁ_-]+", "_", (name or "").strip()).strip("_")
   24 [return    ]     return s.lower() or "unknown"
   25 [blank     ] 
   26 [blank     ] 
   27 [def       ] def render_stereo_texture(handle, prompt: str, duration_sec: int, out_path: str) -> dict:
   28 [docstring ]     """Рендерить отдельную стерео-текстуру через совместимый MusicGen handle."""
   29 [try_block ]     try:
   30 [import    ]         import soundfile as sf
   31 [blank     ] 
   32 [code      ]         handle.set_generation_params(
   33 [code      ]             duration=duration_sec, top_k=250, temperature=1.0, cfg_coef=3.0
   34 [code      ]         )
   35 [code      ]         generated = handle.generate([prompt], progress=False)[0].detach().cpu().numpy()
   36 [branch    ]         if generated.ndim == 1:
   37 [code      ]             generated = generated[:, None]
   38 [branch    ]         elif generated.ndim == 2:
   39 [code      ]             generated = generated.T
   40 [branch    ]         else:
   41 [return    ]             return {"ok": False, "reason": "unexpected MusicGen stereo tensor shape"}
   42 [branch    ]         if generated.shape[1] == 1:
   43 [code      ]             generated = generated.repeat(2, axis=1)
   44 [code      ]         sf.write(out_path, generated.astype("float32"), int(getattr(handle, "sample_rate", 32000)),
   45 [code      ]                  subtype="PCM_16")
   46 [return    ]         return {"ok": True, "texture_path": out_path}
   47 [try_block ]     except Exception as exc:
   48 [return    ]         return {"ok": False, "reason": f"music_stereo generation failed: {exc}"}
   49 [blank     ] 
   50 [blank     ] 
   51 [def       ] def render_xtts_vocal(handle, text: str, out_path: str, speaker_wav: str | None = None) -> dict:
   52 [docstring ]     """Синтезировать вокал через совместимый XTTS handle и подтвердить файл-результат."""
   53 [try_block ]     try:
   54 [code      ]         kwargs = {"text": text, "file_path": out_path, "language": "ru"}
   55 [branch    ]         if speaker_wav and Path(speaker_wav).exists():
   56 [code      ]             kwargs["speaker_wav"] = speaker_wav
   57 [code      ]         handle.tts_to_file(**kwargs)
   58 [code      ]         target = Path(out_path)
   59 [branch    ]         if not target.exists() or target.stat().st_size <= 100:
   60 [return    ]             return {"ok": False, "reason": "XTTS did not produce an audio file"}
   61 [code      ]         quality = validate_vocal_artifact(target, text)
   62 [return    ]         return {
   63 [code      ]             "ok": bool(quality["ok"]),
   64 [code      ]             "vocal_path": str(target),
   65 [code      ]             "engine": "xtts_v2",
   66 [code      ]             "quality": quality,
   67 [code      ]             "reason": quality["reason"],
   68 [code      ]         }
   69 [try_block ]     except Exception as exc:
   70 [return    ]         return {"ok": False, "reason": f"XTTS synthesis failed: {exc}"}
   71 [blank     ] 
   72 [blank     ] 
   73 [def       ] def render_voice_synth_fallback(text: str, out_path: str, synth_fn=None) -> dict:
   74 [docstring ]     """Запустить существующую честную TTS-цепочку и привести результат к vocal-артефакту проекта."""
   75 [try_block ]     try:
   76 [branch    ]         if synth_fn is None:
   77 [import    ]             from modules.voice_synth import synth as synth_fn
   78 [code      ]         source_path = synth_fn(text, engine="auto", out_name=Path(out_path).name)
   79 [code      ]         source = Path(source_path) if source_path else None
   80 [branch    ]         if source is None or not source.exists():
   81 [return    ]             return {"ok": False, "reason": "no fallback TTS engine produced audio"}
   82 [code      ]         target = Path(out_path)
   83 [code      ]         target.parent.mkdir(parents=True, exist_ok=True)
   84 [branch    ]         if source.resolve() != target.resolve():
   85 [code      ]             shutil.copy2(source, target)
   86 [code      ]         quality = validate_vocal_artifact(target, text)
   87 [return    ]         return {
   88 [code      ]             "ok": bool(quality["ok"]),
   89 [code      ]             "vocal_path": str(target),
   90 [code      ]             "engine": "voice_synth_fallback",
   91 [code      ]             "quality": quality,
   92 [code      ]             "reason": quality["reason"],
   93 [code      ]         }
   94 [try_block ]     except Exception as exc:
   95 [return    ]         return {"ok": False, "reason": f"fallback TTS failed: {exc}"}
   96 [blank     ] 
   97 [blank     ] 
   98 [def       ] def render_rvc_vocal(handle, input_wav: str, out_path: str, voice_name: str, pitch_shift: int = 0) -> dict:
   99 [docstring ]     """Выполнить RVC через публичный ``rvc_manager.infer`` и сохранить проектный артефакт."""
  100 [try_block ]     try:
  101 [code      ]         safe_voice_name = Path(voice_name).name
  102 [branch    ]         if not safe_voice_name:
  103 [return    ]             return {"ok": False, "reason": "RVC voice name is missing"}
  104 [code      ]         produced = handle.infer(
  105 [code      ]             input_wav=input_wav,
  106 [code      ]             voice_name=safe_voice_name,
  107 [code      ]             pitch_shift=int(pitch_shift),
  108 [code      ]             out_name=Path(out_path).name,
  109 [code      ]         )
  110 [code      ]         source = Path(produced) if produced else None
  111 [branch    ]         if source is None or not source.exists() or source.stat().st_size <= 100:
  112 [return    ]             return {"ok": False, "reason": "RVC did not produce an audio file"}
  113 [code      ]         target = Path(out_path)
  114 [code      ]         target.parent.mkdir(parents=True, exist_ok=True)
  115 [branch    ]         if source.resolve() != target.resolve():
  116 [code      ]             shutil.copy2(source, target)
  117 [code      ]         quality = validate_rvc_artifact(input_wav, target)
  118 [return    ]         return {
  119 [code      ]             "ok": bool(quality["ok"]),
  120 [code      ]             "vocal_path": str(target),
  121 [code      ]             "engine": "rvc",
  122 [code      ]             "voice_name": safe_voice_name,
  123 [code      ]             "pitch_shift": int(pitch_shift),
  124 [code      ]             "quality": quality,
  125 [code      ]             "reason": quality["reason"],
  126 [code      ]         }
  127 [try_block ]     except Exception as exc:
  128 [return    ]         return {"ok": False, "reason": f"RVC inference failed: {exc}"}
  129 [blank     ] 
  130 [blank     ] 
  131 [def       ] def run_ai_pipeline(project_id, wizard_state=None, out_root=None, dry_run=False):
  132 [code      ]     ws = dict(wizard_state or {})
  133 [try_block ]     try:
  134 [import    ]         from config.settings import get_settings
  135 [code      ]         cfg = get_settings()
  136 [code      ]         app_logger.info(f"[orchestrator_ai] config_path={cfg.config_path} vram_gb={cfg.vram_gb}")
  137 [try_block ]     except Exception:  # noqa: BLE001
  138 [code      ]         cfg = None
  139 [code      ]     ws.setdefault("genre", "drift_phonk")
  140 [code      ]     ws.setdefault("theme", "движ, ночь, город")
  141 [code      ]     ws.setdefault("bpm", 140)
  142 [code      ]     ws.setdefault("key", "A minor")
  143 [code      ]     ws.setdefault("mood", "dark, hypnotic, energetic")
  144 [code      ]     ws.setdefault("n_verses", 2)
  145 [code      ]     ws.setdefault("bilingual", True)
  146 [code      ]     ws.setdefault("duration_sec", 120)
  147 [branch    ]     if not out_root:
  148 [code      ]         out_root = Path(__file__).resolve().parents[2] / "output" / project_id
  149 [code      ]     out_root = Path(out_root)
  150 [code      ]     out_root.mkdir(parents=True, exist_ok=True)
  151 [code      ]     (out_root / "masters").mkdir(exist_ok=True)
  152 [code      ]     artist_slug = _slug(ws["artist_slug"]) if ws.get("artist_slug") else None
  153 [code      ]     ref_track_id = ws.get("track_id")
  154 [blank     ] 
  155 [def       ]     def stage_hw(_, ctx):
  156 [try_block ]         try:
  157 [import    ]             from app.core.hw_autodetect import get_hardware_profile
  158 [return    ]             return get_hardware_profile()
  159 [try_block ]         except Exception as e:
  160 [return    ]             return {"error": str(e)}
  161 [blank     ] 
  162 [def       ]     def stage_dossier_load(_, ctx):
  163 [branch    ]         if not artist_slug:
  164 [return    ]             return {"skipped": "no artist_slug"}
  165 [code      ]         mgr = DossierManager()
  166 [return    ]         return {"artist_dossier": mgr.get_artist_dossier(artist_slug),
  167 [code      ]                 "track_dossier": mgr.get_track_dossier(artist_slug, ref_track_id) if ref_track_id else None}
  168 [blank     ] 
  169 [def       ]     def stage_lyrics(handle, ctx):
  170 [branch    ]         if dry_run:
  171 [return    ]             return {"ok": True, "lyrics": "[dry-run]", "source": "dry"}
  172 [code      ]         art = (ctx["sink"].get("dossier_load") or {}).get("artist_dossier")
  173 [code      ]         trk = (ctx["sink"].get("dossier_load") or {}).get("track_dossier")
  174 [code      ]         text, source = "", "lyrics_llm"
  175 [branch    ]         if handle is not None:
  176 [code      ]             prompt = P.build_lyrics_prompt(theme=ws["theme"], genre=ws["genre"], bpm=ws["bpm"],
  177 [code      ]                 n_verses=ws["n_verses"], bilingual=ws["bilingual"],
  178 [code      ]                 user_lines=ws.get("user_lyrics_lines"),
  179 [code      ]                 artist_dossier=art, track_reference=trk)
  180 [code      ]             text = LLM.complete(handle, P.SYSTEM_LYRICS, prompt, max_tokens=1400,
  181 [code      ]                                 temperature=0.9, repeat_penalty=1.15)
  182 [blank     ] 
  183 [code      ]         quality = validate_lyrics(text)
  184 [branch    ]         if not quality["ok"]:
  185 [try_block ]             try:
  186 [import    ]                 from modules import lyrics_gen
  187 [code      ]                 r = lyrics_gen.generate_lyrics(theme=ws["theme"],
  188 [code      ]                     style_vector={"target_bpm": ws["bpm"]}, n_verses=ws["n_verses"],
  189 [code      ]                     user_lyrics_lines=ws.get("user_lyrics_lines") or [],
  190 [code      ]                     bilingual=ws["bilingual"])
  191 [code      ]                 text = r.get("lyrics", "")
  192 [code      ]                 source = "punch_lib_fallback"
  193 [code      ]                 quality = validate_lyrics(text)
  194 [try_block ]             except Exception as _lg_e:  # noqa: BLE001
  195 [code      ]                 app_logger.error(
  196 [code      ]                     f"[orchestrator_ai] stage=lyrics event=fallback_failed "
  197 [code      ]                     f"reason={type(_lg_e).__name__}: {_lg_e}")
  198 [code      ]         (out_root / "lyrics.txt").write_text(text or "", encoding="utf-8")
  199 [return    ]         return {"ok": bool(quality["ok"]), "lyrics": text, "source": source,
  200 [code      ]                 "path": str(out_root / "lyrics.txt"), "quality": quality,
  201 [code      ]                 "reason": quality["reason"]}
  202 [blank     ] 
  203 [def       ]     def stage_metadata(handle, ctx):
  204 [code      ]         lyrics = (ctx["sink"].get("lyrics") or {}).get("lyrics") or ""
  205 [code      ]         fallback = {
  206 [code      ]             "title": ws.get("theme", "Untitled").strip()[:120] or "Untitled",
  207 [code      ]             "spotify_desc": f"{ws['genre']} трек: {ws['theme']}.",
  208 [code      ]             "youtube_desc": f"{ws['theme']} — {ws['genre']} / {ws['mood']}.",
  209 [code      ]             "tags_tiktok": [ws["genre"], "newmusic", "independent"],
  210 [code      ]             "tags_instagram": [ws["genre"], "music", "release"],
  211 [code      ]         }
  212 [code      ]         source = "metadata_fallback"
  213 [branch    ]         if dry_run:
  214 [code      ]             js, source = fallback, "dry"
  215 [branch    ]         elif handle is not None:
  216 [code      ]             js = LLM.complete_json(handle, P.SYSTEM_METADATA,
  217 [code      ]                 P.build_metadata_prompt(ws["theme"], ws["genre"], lyrics),
  218 [code      ]                 max_tokens=1200, temperature=0.6) or {}
  219 [code      ]             source = "metadata_llm"
  220 [branch    ]         else:
  221 [code      ]             js = fallback
  222 [code      ]         quality = validate_metadata_json(js)
  223 [branch    ]         if not quality["ok"]:
  224 [code      ]             js, source = fallback, "metadata_fallback"
  225 [code      ]             quality = validate_metadata_json(js)
  226 [code      ]         js = dict(js)
  227 [code      ]         js.update({"ok": bool(quality["ok"]), "source": source, "quality": quality,
  228 [code      ]                    "reason": quality["reason"]})
  229 [code      ]         (out_root / "metadata.json").write_text(
  230 [code      ]             json.dumps(js, ensure_ascii=False, indent=2), encoding="utf-8")
  231 [return    ]         return js
  232 [blank     ] 
  233 [def       ]     def stage_music(handle, ctx):
  234 [branch    ]         if dry_run:
  235 [return    ]             return {"ok": True, "beat_path": "[dry]"}
  236 [branch    ]         if handle is None:
  237 [try_block ]             try:
  238 [import    ]                 from modules.cyber_synth import CyberSynth
  239 [code      ]                 out_p = str(out_root / "beat.wav")
  240 [code      ]                 res = CyberSynth().synthesize_track(bpm=ws["bpm"],
  241 [code      ]                     duration_sec=ws["duration_sec"], out_path=out_p)
  242 [code      ]                 res = dict(res) if isinstance(res, dict) else {}
  243 [code      ]                 quality = validate_audio_artifact(
  244 [code      ]                     out_p, min_duration_sec=max(1.0, min(5.0, ws["duration_sec"] * 0.5))
  245 [code      ]                 )
  246 [code      ]                 res.update({"engine": "cyber_synth_fallback", "beat_path": out_p,
  247 [code      ]                             "quality": quality, "reason": quality["reason"],
  248 [code      ]                             "ok": bool(res.get("ok", True)) and bool(quality["ok"])})
  249 [return    ]                 return res
  250 [try_block ]             except Exception as e:
  251 [return    ]                 return {"ok": False, "reason": f"no music engine: {e}"}
  252 [code      ]         art = (ctx["sink"].get("dossier_load") or {}).get("artist_dossier")
  253 [code      ]         trk = (ctx["sink"].get("dossier_load") or {}).get("track_dossier")
  254 [code      ]         instruments = trk.get("reusable_elements", [])[:5] if isinstance(trk, dict) else []
  255 [code      ]         ref_feats = {"instruments": instruments,
  256 [code      ]                      "atmosphere": (art or {}).get("flow", "")} if art else None
  257 [code      ]         prompt = P.build_music_prompt(ws["genre"], ws["bpm"], ws["key"], ws["mood"],
  258 [code      ]             reference_artist=ws.get("reference_artist") or ws.get("artist_slug"),
  259 [code      ]             reference_track_features=ref_feats)
  260 [import    ]         import numpy as np, soundfile as sf, torch
  261 [code      ]         out_path = str(out_root / "beat.wav")
  262 [code      ]         model = handle
  263 [try_block ]         try:
  264 [code      ]             model.set_generation_params(duration=20, top_k=250, temperature=1.0, cfg_coef=3.0)
  265 [try_block ]         except Exception:
  266 [code      ]             pass
  267 [code      ]         n_chunks = max(1, math.ceil(ws["duration_sec"] / 20))
  268 [code      ]         sr = getattr(model, "sample_rate", 32000)
  269 [code      ]         chunks = [model.generate([prompt], progress=False)[0].cpu().numpy()]
  270 [loop      ]         for i in range(1, n_chunks):
  271 [try_block ]             try:
  272 [code      ]                 prev_t = torch.from_numpy(chunks[-1]).unsqueeze(0)
  273 [branch    ]                 if any(p.is_cuda for p in model.lm.parameters()):
  274 [code      ]                     prev_t = prev_t.cuda()
  275 [code      ]                 cont = model.generate_continuation(prev_t, sr, [prompt], progress=False)[0]
  276 [code      ]                 chunks.append(cont.cpu().numpy())
  277 [try_block ]             except Exception:
  278 [code      ]                 chunks.append(model.generate([prompt], progress=False)[0].cpu().numpy())
  279 [code      ]         full = np.concatenate(chunks, axis=-1)
  280 [code      ]         total = int(ws["duration_sec"] * sr)
  281 [branch    ]         if full.shape[-1] > total:
  282 [code      ]             full = full[..., :total]
  283 [branch    ]         if full.ndim == 1:
  284 [code      ]             full = np.stack([full, full], axis=-1)
  285 [branch    ]         else:
  286 [code      ]             full = full.T
  287 [branch    ]             if full.shape[1] == 1:
  288 [code      ]                 full = np.concatenate([full, full], axis=1)
  289 [code      ]         peak = float(np.max(np.abs(full)) + 1e-9)
  290 [branch    ]         if peak > 0.99:
  291 [code      ]             full = full * (0.98 / peak)
  292 [code      ]         sf.write(out_path, full.astype("float32"), int(sr), subtype="PCM_16")
  293 [code      ]         quality = validate_audio_artifact(
  294 [code      ]             out_path, min_duration_sec=max(1.0, min(5.0, ws["duration_sec"] * 0.5))
  295 [code      ]         )
  296 [return    ]         return {"ok": bool(quality["ok"]), "beat_path": out_path, "engine": "musicgen-large",
  297 [code      ]                 "sample_rate": int(sr), "prompt": prompt, "chunks": n_chunks,
  298 [code      ]                 "quality": quality, "reason": quality["reason"]}
  299 [blank     ] 
  300 [def       ]     def stage_music_stereo(handle, ctx):
  301 [docstring ]         """Создать отдельную стерео-текстуру; основной beat не меняется на этой стадии."""
  302 [branch    ]         if dry_run:
  303 [return    ]             return {"skipped": "dry-run"}
  304 [branch    ]         if handle is None:
  305 [return    ]             return {
  306 [code      ]                 "skipped": "music_stereo unavailable",
  307 [code      ]                 "reason": "audiocraft model is not installed or not loadable",
  308 [code      ]                 "fallback": "base beat is preserved without a synthetic texture",
  309 [code      ]             }
  310 [code      ]         prompt = P.build_music_prompt(ws["genre"], ws["bpm"], ws["key"], ws["mood"])
  311 [code      ]         prompt += ", wide stereo atmosphere, transition texture, no lead vocal"
  312 [code      ]         duration = max(2, min(int(ws.get("texture_duration_sec", 8)), 20))
  313 [code      ]         out_path = str(out_root / "texture_stereo.wav")
  314 [code      ]         result = render_stereo_texture(handle, prompt, duration, out_path)
  315 [branch    ]         if result.get("ok"):
  316 [code      ]             quality = validate_stereo_texture(out_path, min_duration_sec=max(1.0, duration * 0.5))
  317 [code      ]             result["ok"] = bool(quality["ok"])
  318 [code      ]             result["quality"] = quality
  319 [code      ]             result["reason"] = quality["reason"]
  320 [code      ]         result.update({
  321 [code      ]             "engine": "musicgen-stereo-medium",
  322 [code      ]             "prompt": prompt,
  323 [code      ]             "duration_sec": duration,
  324 [code      ]         })
  325 [return    ]         return result
  326 [blank     ] 
  327 [def       ]     def stage_vocal(handle, ctx):
  328 [branch    ]         if dry_run:
  329 [return    ]             return {"skipped": "dry-run"}
  330 [code      ]         lyrics = (ctx["sink"].get("lyrics") or {}).get("lyrics") or ""
  331 [branch    ]         if not lyrics.strip():
  332 [return    ]             return {"skipped": "no lyrics"}
  333 [import    ]         import re
  334 [code      ]         clean = re.sub(r"^\[.*?\]\s*$", "", lyrics, flags=re.MULTILINE).strip()
  335 [code      ]         clean = re.sub(r"\n{3,}", "\n\n", clean)[:3500]
  336 [code      ]         out_path = str(out_root / "vocal_xtts.wav")
  337 [branch    ]         if handle is not None:
  338 [code      ]             primary = render_xtts_vocal(handle, clean, out_path, speaker_wav=ws.get("speaker_wav"))
  339 [branch    ]             if primary.get("ok"):
  340 [return    ]                 return primary
  341 [branch    ]         else:
  342 [code      ]             primary = {"ok": False, "reason": "XTTS model unavailable"}
  343 [code      ]         fallback = render_voice_synth_fallback(clean, out_path)
  344 [code      ]         fallback["xtts_attempt"] = primary.get("reason")
  345 [return    ]         return fallback
  346 [blank     ] 
  347 [def       ]     def stage_rvc(handle, ctx):
  348 [branch    ]         if dry_run:
  349 [return    ]             return {"skipped": "dry-run"}
  350 [branch    ]         if handle is None:
  351 [return    ]             return {"skipped": "RVC unavailable", "reason": "no installed RVC model/runtime"}
  352 [code      ]         vocal = (ctx["sink"].get("vocal_synth") or {}).get("vocal_path")
  353 [branch    ]         if not vocal or not Path(vocal).exists():
  354 [return    ]             return {"skipped": "no vocal"}
  355 [code      ]         voice_name = ws.get("rvc_voice_name") or Path(str(ws.get("rvc_model") or "")).stem
  356 [branch    ]         if not voice_name:
  357 [return    ]             return {"skipped": "no rvc_voice_name"}
  358 [code      ]         out_path = str(out_root / "vocal_rvc.wav")
  359 [return    ]         return render_rvc_vocal(
  360 [code      ]             handle,
  361 [code      ]             vocal,
  362 [code      ]             out_path,
  363 [code      ]             voice_name=voice_name,
  364 [code      ]             pitch_shift=int(ws.get("rvc_pitch_shift", 0)),
  365 [code      ]         )
  366 [blank     ] 
  367 [def       ]     def stage_mix(_, ctx):
  368 [code      ]         beat = (ctx["sink"].get("music") or {}).get("beat_path")
  369 [code      ]         vocal = ((ctx["sink"].get("rvc") or {}).get("vocal_path")
  370 [code      ]                  or (ctx["sink"].get("vocal_synth") or {}).get("vocal_path"))
  371 [code      ]         mix_path = str(out_root / "mix.wav")
  372 [branch    ]         if not beat or not Path(beat).exists():
  373 [return    ]             return {"skipped": "no beat"}
  374 [try_block ]         try:
  375 [import    ]             import numpy as np, soundfile as sf
  376 [code      ]             b, sr_b = sf.read(beat)
  377 [branch    ]             if b.ndim == 1:
  378 [code      ]                 b = np.stack([b, b], axis=-1)
  379 [branch    ]             if not vocal or not Path(vocal).exists():
  380 [code      ]                 sf.write(mix_path, b, sr_b)
  381 [return    ]                 return {"ok": True, "mix_path": mix_path, "vocal": False}
  382 [code      ]             v, sr_v = sf.read(vocal)
  383 [branch    ]             if sr_v != sr_b:
  384 [import    ]                 import librosa
  385 [code      ]                 v = librosa.resample(v.T if v.ndim > 1 else v, orig_sr=sr_v, target_sr=sr_b)
  386 [code      ]                 v = v.T if v.ndim > 1 else v
  387 [branch    ]             if v.ndim == 1:
  388 [code      ]                 v = np.stack([v, v], axis=-1)
  389 [code      ]             n = min(len(b), len(v))
  390 [code      ]             mix = b[:n] * 0.9 + v[:n] * 0.75
  391 [code      ]             peak = float(np.max(np.abs(mix)) + 1e-9)
  392 [branch    ]             if peak > 0.99:
  393 [code      ]                 mix = mix * (0.98 / peak)
  394 [code      ]             sf.write(mix_path, mix, sr_b)
  395 [return    ]             return {"ok": True, "mix_path": mix_path, "vocal": True}
  396 [try_block ]         except Exception as e:
  397 [return    ]             return {"ok": False, "reason": str(e)}
  398 [blank     ] 
  399 [def       ]     def stage_master(_, ctx):
  400 [code      ]         mix = (ctx["sink"].get("mix") or {}).get("mix_path")
  401 [branch    ]         if not mix:
  402 [return    ]             return {"skipped": "no mix"}
  403 [code      ]         out_master = str(out_root / "masters" / "master_ai.wav")
  404 [import    ]         from modules.mastering_ai import master_ai
  405 [return    ]         return master_ai(mix, out_master, reference_wav=ws.get("reference_master_wav"),
  406 [code      ]                          target_lufs=-9.0)
  407 [blank     ] 
  408 [def       ]     def stage_cover(_, ctx):
  409 [code      ]         meta = ctx["sink"].get("metadata") or {}
  410 [code      ]         title = meta.get("title") or ws.get("theme", "Untitled")
  411 [code      ]         artist = ws.get("artist_display") or ws.get("artist_slug") or "ZS"
  412 [import    ]         from modules.cover_art_ai import render_cover_ai
  413 [return    ]         return render_cover_ai(title=title, artist=artist, genre=ws["genre"],
  414 [code      ]                                mood=ws["mood"], out_path=str(out_root / "cover.png"))
  415 [blank     ] 
  416 [def       ]     def stage_tag(bundle, ctx):
  417 [branch    ]         if bundle is None:
  418 [return    ]             return {"skipped": "no clap"}
  419 [code      ]         master = ((ctx["sink"].get("master") or {}).get("path")
  420 [code      ]                   or str(out_root / "masters" / "master_ai.wav"))
  421 [branch    ]         if not Path(master).exists():
  422 [return    ]             return {"skipped": "no master"}
  423 [try_block ]         try:
  424 [import    ]             import torch, librosa, numpy as np
  425 [code      ]             model, proc = bundle
  426 [code      ]             y, sr = librosa.load(master, sr=48000, mono=True, duration=30)
  427 [code      ]             cand = ["phonk", "trap", "drill", "pop", "rock", "shanson",
  428 [code      ]                     "aggressive", "melancholic", "party", "romantic"]
  429 [code      ]             inputs = proc(text=cand, audios=y, sampling_rate=48000,
  430 [return    ]                           return_tensors="pt", padding=True)
  431 [branch    ]             if any(p.is_cuda for p in model.parameters()):
  432 [code      ]                 inputs = {k: (v.cuda() if hasattr(v, "cuda") else v)
  433 [loop      ]                           for k, v in inputs.items()}
  434 [stmt      ]             with torch.no_grad():
  435 [code      ]                 logits = model(**inputs).logits_per_audio[0].cpu().numpy()
  436 [code      ]             tags = [cand[i] for i in np.argsort(-logits)[:5]]
  437 [return    ]             return {"ok": True, "tags": tags, "goal": ws["genre"],
  438 [code      ]                     "match_genre": ws["genre"] in tags}
  439 [try_block ]         except Exception as e:
  440 [return    ]             return {"ok": False, "reason": str(e)}
  441 [blank     ] 
  442 [code      ]     runner = SequentialAIRunner()
  443 [code      ]     runner.add(AIStage("hw_check",     None,               stage_hw))
  444 [code      ]     runner.add(AIStage("dossier_load", None,               stage_dossier_load))
  445 [code      ]     runner.add(AIStage("lyrics",       "lyrics_llm",       stage_lyrics,   optional=True))
  446 [code      ]     runner.add(AIStage("metadata",     "metadata_llm",     stage_metadata, optional=True))
  447 [code      ]     runner.add(AIStage("music",        "music_generation", stage_music,    optional=True))
  448 [code      ]     runner.add(AIStage("music_stereo", "music_stereo",     stage_music_stereo, optional=True))
  449 [code      ]     runner.add(AIStage("vocal_synth",  "tts_vocal",        stage_vocal,    optional=True))
  450 [code      ]     runner.add(AIStage("rvc",          "vocal_rvc",        stage_rvc,      optional=True))
  451 [code      ]     runner.add(AIStage("mix",          None,               stage_mix))
  452 [code      ]     runner.add(AIStage("master",       None,               stage_master))
  453 [code      ]     runner.add(AIStage("cover",        "cover_art",        stage_cover,    optional=True))
  454 [code      ]     runner.add(AIStage("tag",          "audio_tagger",     stage_tag,      optional=True))
  455 [code      ]     report = runner.run({"project_id": project_id, "wizard_state": ws})
  456 [code      ]     result = {"project_id": project_id, "god_mode": "4.0-AI", "wizard_state": ws,
  457 [code      ]               "report": report.to_dict(),
  458 [code      ]               "config": cfg.dump() if cfg is not None else None,
  459 [code      ]               "artefacts": {"lyrics": str(out_root / "lyrics.txt"),
  460 [code      ]                             "metadata": str(out_root / "metadata.json"),
  461 [code      ]                             "beat": str(out_root / "beat.wav"),
  462 [code      ]                             "texture_stereo": str(out_root / "texture_stereo.wav"),
  463 [code      ]                             "vocal": str(out_root / "vocal_xtts.wav"),
  464 [code      ]                             "mix": str(out_root / "mix.wav"),
  465 [code      ]                             "master": str(out_root / "masters" / "master_ai.wav"),
  466 [code      ]                             "cover": str(out_root / "cover.png")}}
  467 [code      ]     (out_root / "project_meta.json").write_text(
  468 [code      ]         json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
  469 [code      ]     app_logger.info(f"[orchestrator_ai] finished project={project_id}")
  470 [return    ]     return result
```