# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/artist_dossier/manager.py`

**Всего строк:** 398

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 207 | 52.0 |
| return | 40 | 10.1 |
| branch | 40 | 10.1 |
| blank | 37 | 9.3 |
| def | 24 | 6.0 |
| import | 15 | 3.8 |
| try_block | 12 | 3.0 |
| loop | 7 | 1.8 |
| docstring | 5 | 1.3 |
| raise | 3 | 0.8 |
| class | 3 | 0.8 |
| decorator | 2 | 0.5 |
| stmt | 2 | 0.5 |
| comment | 1 | 0.3 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """ZS Music Maker - modules/artist_dossier/manager.py (v38)
    3 [docstring ] Последовательный AI-пайплайн на трек: demucs -> whisper -> librosa -> CLAP -> LLM."""
    4 [import    ] from __future__ import annotations
    5 [import    ] import json, re, time, hashlib, shutil
    6 [import    ] from dataclasses import dataclass, field, asdict
    7 [import    ] from pathlib import Path
    8 [import    ] from typing import Any, Dict, List, Optional
    9 [import    ] from app.ai.registry import registry
   10 [import    ] from app.ai.sequential_runner import SequentialAIRunner, AIStage
   11 [import    ] from app.ai import prompts as P
   12 [import    ] from app.ai import llm_service as LLM
   13 [import    ] from app.ai.quality import (
   14 [code      ]     validate_analysis_json,
   15 [code      ]     validate_asr_transcript,
   16 [code      ]     validate_stem_artifact,
   17 [code      ] )
   18 [blank     ] 
   19 [code      ] ROOT = Path(__file__).resolve().parents[2]
   20 [code      ] DOSSIER_ROOT = ROOT / "data" / "artist_dossier"
   21 [code      ] DOSSIER_ROOT.mkdir(parents=True, exist_ok=True)
   22 [blank     ] 
   23 [blank     ] 
   24 [def       ] def _slug(name: str) -> str:
   25 [code      ]     s = re.sub(r"[^A-Za-z0-9а-яА-ЯёЁ_-]+", "_", (name or "unknown").strip()).strip("_")
   26 [return    ]     return s.lower() or "unknown"
   27 [blank     ] 
   28 [blank     ] 
   29 [def       ] def _track_id(title: str, url: str = "") -> str:
   30 [code      ]     base = (title or "") + "|" + (url or "")
   31 [return    ]     return _slug(title)[:32] + "_" + hashlib.md5(base.encode("utf-8")).hexdigest()[:8]
   32 [blank     ] 
   33 [blank     ] 
   34 [def       ] def resolve_vocal_source_index(model: Any) -> int:
   35 [docstring ]     """Вернуть индекс stem ``vocals`` из порядка источников фактической Demucs-модели."""
   36 [code      ]     sources = tuple(getattr(model, "sources", ()) or ())
   37 [branch    ]     if "vocals" not in sources:
   38 [raise     ]         raise ValueError("Demucs model does not expose a 'vocals' source")
   39 [return    ]     return sources.index("vocals")
   40 [blank     ] 
   41 [blank     ] 
   42 [def       ] def rank_clap_tags(candidates: list[str], logits: Any, limit: int = 6) -> list[str]:
   43 [docstring ]     """Отсортировать CLAP logits и вернуть уникальные top-N labels из переданного словаря."""
   44 [import    ]     import numpy as np
   45 [blank     ] 
   46 [code      ]     scores = np.asarray(logits).reshape(-1)
   47 [branch    ]     if len(scores) != len(candidates):
   48 [raise     ]         raise ValueError("CLAP scores do not match the candidate vocabulary")
   49 [return    ]     return [candidates[index] for index in np.argsort(-scores)[:max(1, limit)]]
   50 [blank     ] 
   51 [blank     ] 
   52 [def       ] def transcribe_reference_audio(model: Any, audio_path: str, output_path: str) -> dict:
   53 [docstring ]     """Распознать reference-аудио совместимым faster-whisper handle и сохранить transcript."""
   54 [try_block ]     try:
   55 [code      ]         segments, info = model.transcribe(audio_path, language="ru", beam_size=5)
   56 [code      ]         text = "\n".join(
   57 [code      ]             str(getattr(segment, "text", "")).strip() for segment in segments
   58 [code      ]         ).strip()
   59 [code      ]         quality = validate_asr_transcript(text)
   60 [branch    ]         if not quality["ok"]:
   61 [return    ]             return {
   62 [code      ]                 "ok": False,
   63 [code      ]                 "reason": quality["reason"],
   64 [code      ]                 "quality": quality,
   65 [code      ]                 "fallback": "reference audio retained; transcript is not used",
   66 [code      ]             }
   67 [code      ]         target = Path(output_path)
   68 [code      ]         target.parent.mkdir(parents=True, exist_ok=True)
   69 [code      ]         target.write_text(text, encoding="utf-8")
   70 [return    ]         return {
   71 [code      ]             "ok": True,
   72 [code      ]             "lyrics": text,
   73 [code      ]             "language": str(getattr(info, "language", "")),
   74 [code      ]             "source": "faster_whisper",
   75 [code      ]             "transcript_path": str(target),
   76 [code      ]             "quality": quality,
   77 [code      ]             "reason": None,
   78 [code      ]         }
   79 [try_block ]     except Exception as exc:
   80 [return    ]         return {"ok": False, "reason": f"ASR transcription failed: {exc}"}
   81 [blank     ] 
   82 [blank     ] 
   83 [decorator ] @dataclass
   84 [class     ] class TrackEntry:
   85 [code      ]     track_id: str
   86 [code      ]     title: str
   87 [code      ]     artist: str
   88 [code      ]     audio_path: Optional[str] = None
   89 [code      ]     external_url: Optional[str] = None
   90 [code      ]     lyrics: Optional[str] = None
   91 [code      ]     features: Dict[str, Any] = field(default_factory=dict)
   92 [code      ]     dossier: Dict[str, Any] = field(default_factory=dict)
   93 [code      ]     status: str = "pending"
   94 [code      ]     added_at: float = 0.0
   95 [blank     ] 
   96 [blank     ] 
   97 [decorator ] @dataclass
   98 [class     ] class ArtistEntry:
   99 [code      ]     artist: str
  100 [code      ]     slug: str
  101 [code      ]     tracks: List[str] = field(default_factory=list)
  102 [code      ]     dossier: Dict[str, Any] = field(default_factory=dict)
  103 [code      ]     added_at: float = 0.0
  104 [code      ]     updated_at: float = 0.0
  105 [blank     ] 
  106 [blank     ] 
  107 [class     ] class DossierManager:
  108 [def       ]     def __init__(self, root: Optional[Path] = None):
  109 [code      ]         self.root = Path(root) if root else DOSSIER_ROOT
  110 [code      ]         self.root.mkdir(parents=True, exist_ok=True)
  111 [blank     ] 
  112 [def       ]     def add_artist(self, artist: str,
  113 [code      ]                    tracks: Optional[List[Dict[str, Any]]] = None) -> ArtistEntry:
  114 [code      ]         slug = _slug(artist)
  115 [code      ]         adir = self.root / slug
  116 [loop      ]         for sub in ("tracks", "audio", "vocals", "lyrics"):
  117 [code      ]             (adir / sub).mkdir(parents=True, exist_ok=True)
  118 [code      ]         entry = self._load_artist(slug) or ArtistEntry(
  119 [code      ]             artist=artist, slug=slug, added_at=time.time(), updated_at=time.time())
  120 [code      ]         self._save_artist(entry)  # скелет, чтобы add_track увидел артиста
  121 [loop      ]         for t in tracks or []:
  122 [code      ]             self.add_track(artist, t.get("title", "untitled"),
  123 [code      ]                            audio_path=t.get("audio_path"),
  124 [code      ]                            external_url=t.get("external_url"),
  125 [code      ]                            lyrics=t.get("lyrics"))
  126 [code      ]         entry = self._load_artist(slug) or entry
  127 [code      ]         entry.updated_at = time.time()
  128 [code      ]         self._save_artist(entry)
  129 [return    ]         return entry
  130 [blank     ] 
  131 [def       ]     def add_track(self, artist: str, title: str,
  132 [code      ]                   audio_path: Optional[str] = None,
  133 [code      ]                   external_url: Optional[str] = None,
  134 [code      ]                   lyrics: Optional[str] = None) -> TrackEntry:
  135 [code      ]         slug = _slug(artist)
  136 [code      ]         tid = _track_id(title, external_url or "")
  137 [code      ]         entry = TrackEntry(track_id=tid, title=title, artist=artist,
  138 [code      ]                            audio_path=audio_path, external_url=external_url,
  139 [code      ]                            lyrics=lyrics, added_at=time.time())
  140 [branch    ]         if audio_path and Path(audio_path).exists():
  141 [code      ]             dst = self.root / slug / "audio" / f"{tid}{Path(audio_path).suffix.lower()}"
  142 [try_block ]             try:
  143 [code      ]                 shutil.copy2(audio_path, dst)
  144 [code      ]                 entry.audio_path = str(dst)
  145 [try_block ]             except Exception:
  146 [code      ]                 pass
  147 [branch    ]         if lyrics:
  148 [code      ]             (self.root / slug / "lyrics" / f"{tid}.txt").write_text(lyrics, encoding="utf-8")
  149 [code      ]         self._save_track(slug, entry)
  150 [code      ]         a = self._load_artist(slug) or ArtistEntry(
  151 [code      ]             artist=artist, slug=slug, added_at=time.time(), updated_at=time.time())
  152 [branch    ]         if tid not in a.tracks:
  153 [code      ]             a.tracks.append(tid)
  154 [code      ]         a.updated_at = time.time()
  155 [code      ]         self._save_artist(a)
  156 [return    ]         return entry
  157 [blank     ] 
  158 [def       ]     def build_full_dossier(self, artist: str, refresh: bool = False,
  159 [code      ]                            progress_cb=None) -> Dict[str, Any]:
  160 [code      ]         slug = _slug(artist)
  161 [code      ]         a = self._load_artist(slug)
  162 [branch    ]         if not a:
  163 [raise     ]             raise ValueError(f"Artist {artist} not registered")
  164 [loop      ]         for tid in a.tracks:
  165 [code      ]             tr = self._load_track(slug, tid)
  166 [branch    ]             if not tr:
  167 [code      ]                 continue
  168 [branch    ]             if not refresh and tr.status == "analyzed":
  169 [branch    ]                 if progress_cb:
  170 [code      ]                     progress_cb(tid, "cached")
  171 [code      ]                 continue
  172 [try_block ]             try:
  173 [code      ]                 self._analyze_single_track(slug, tr, progress_cb=progress_cb)
  174 [try_block ]             except Exception as e:
  175 [code      ]                 tr.status = "failed"
  176 [code      ]                 tr.dossier = {"error": str(e)}
  177 [code      ]                 self._save_track(slug, tr)
  178 [code      ]         a.dossier = self._aggregate_artist_dossier(slug, a)
  179 [code      ]         a.updated_at = time.time()
  180 [code      ]         self._save_artist(a)
  181 [return    ]         return a.dossier
  182 [blank     ] 
  183 [def       ]     def _analyze_single_track(self, slug: str, tr: TrackEntry, progress_cb=None) -> None:
  184 [branch    ]         if progress_cb:
  185 [code      ]             progress_cb(tr.track_id, "start")
  186 [code      ]         runner = SequentialAIRunner()
  187 [blank     ] 
  188 [def       ]         def _demucs_stage(model, ctx):
  189 [branch    ]             if model is None:
  190 [return    ]                 return {"skipped": "stem_splitter unavailable"}
  191 [branch    ]             if not tr.audio_path or not Path(tr.audio_path).exists():
  192 [return    ]                 return {"skipped": "no audio"}
  193 [try_block ]             try:
  194 [import    ]                 import torchaudio, soundfile as sf
  195 [import    ]                 from demucs.apply import apply_model
  196 [code      ]                 wav, sr = torchaudio.load(tr.audio_path)
  197 [branch    ]                 if wav.dim() == 1:
  198 [code      ]                     wav = wav.unsqueeze(0)
  199 [branch    ]                 if wav.shape[0] == 1:
  200 [code      ]                     wav = wav.repeat(2, 1)
  201 [code      ]                 wav = wav.unsqueeze(0)
  202 [code      ]                 dev = str(next(model.parameters()).device)
  203 [branch    ]                 if dev.startswith("cuda"):
  204 [code      ]                     wav = wav.cuda()
  205 [code      ]                 vocal_index = resolve_vocal_source_index(model)
  206 [code      ]                 sources = apply_model(model, wav, device=dev, split=True, overlap=0.25)
  207 [code      ]                 vocals = sources[0, vocal_index].cpu().numpy().T
  208 [code      ]                 out = self.root / slug / "vocals" / f"{tr.track_id}_vocals.wav"
  209 [code      ]                 out.parent.mkdir(parents=True, exist_ok=True)
  210 [code      ]                 sf.write(str(out), vocals, int(sr))
  211 [code      ]                 quality = validate_stem_artifact(tr.audio_path, out)
  212 [return    ]                 return {
  213 [code      ]                     "ok": bool(quality["ok"]),
  214 [code      ]                     "vocals_path": str(out),
  215 [code      ]                     "source_index": vocal_index,
  216 [code      ]                     "quality": quality,
  217 [code      ]                     "reason": quality["reason"],
  218 [code      ]                 }
  219 [try_block ]             except Exception as e:
  220 [return    ]                 return {"ok": False, "error": str(e)}
  221 [code      ]         runner.add(AIStage("demucs", "stem_splitter", _demucs_stage, optional=True))
  222 [blank     ] 
  223 [def       ]         def _asr_stage(model, ctx):
  224 [branch    ]             if tr.lyrics:
  225 [return    ]                 return {"lyrics": tr.lyrics, "source": "user"}
  226 [branch    ]             if model is None:
  227 [return    ]                 return {"skipped": "asr unavailable"}
  228 [code      ]             vocals = (ctx.get("sink", {}).get("demucs") or {}).get("vocals_path")
  229 [code      ]             src = vocals or tr.audio_path
  230 [branch    ]             if not src or not Path(src).exists():
  231 [return    ]                 return {"skipped": "no audio for ASR"}
  232 [return    ]             return transcribe_reference_audio(
  233 [code      ]                 model,
  234 [code      ]                 str(src),
  235 [code      ]                 str(self.root / slug / "lyrics" / f"{tr.track_id}.txt"),
  236 [code      ]             )
  237 [code      ]         runner.add(AIStage("asr", "asr", _asr_stage, optional=True))
  238 [blank     ] 
  239 [def       ]         def _features_stage(_, ctx):
  240 [code      ]             feats: Dict[str, Any] = {}
  241 [branch    ]             if tr.audio_path and Path(tr.audio_path).exists():
  242 [try_block ]                 try:
  243 [import    ]                     import librosa, numpy as np
  244 [code      ]                     y, sr = librosa.load(tr.audio_path, sr=22050, mono=True, duration=180)
  245 [code      ]                     tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
  246 [code      ]                     feats["bpm"] = float(tempo)
  247 [code      ]                     chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)
  248 [code      ]                     keys = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
  249 [code      ]                     feats["key"] = keys[int(np.argmax(chroma))]
  250 [code      ]                     feats["duration_sec"] = float(len(y) / sr)
  251 [code      ]                     feats["loudness_rms"] = float(np.sqrt(np.mean(y ** 2)) + 1e-9)
  252 [try_block ]                 except Exception as e:
  253 [code      ]                     feats["error"] = str(e)
  254 [return    ]             return feats
  255 [code      ]         runner.add(AIStage("features", None, _features_stage))
  256 [blank     ] 
  257 [def       ]         def _tag_stage(bundle, ctx):
  258 [branch    ]             if bundle is None:
  259 [return    ]                 return {"skipped": "audio_tagger unavailable"}
  260 [branch    ]             if not tr.audio_path or not Path(tr.audio_path).exists():
  261 [return    ]                 return {"skipped": "no audio"}
  262 [try_block ]             try:
  263 [code      ]                 model, proc = bundle
  264 [import    ]                 import torch, librosa, numpy as np
  265 [code      ]                 y, sr = librosa.load(tr.audio_path, sr=48000, mono=True, duration=30)
  266 [code      ]                 cand = ["phonk", "trap", "drill", "hip-hop", "pop", "rock", "shanson",
  267 [code      ]                         "aggressive", "melancholic", "dark", "party", "romantic",
  268 [code      ]                         "808 bass", "acoustic guitar", "piano", "female vocal",
  269 [code      ]                         "male vocal", "rap", "singing"]
  270 [code      ]                 inputs = proc(text=cand, audios=y, sampling_rate=48000,
  271 [return    ]                               return_tensors="pt", padding=True)
  272 [branch    ]                 if any(p.is_cuda for p in model.parameters()):
  273 [code      ]                     inputs = {k: (v.cuda() if hasattr(v, "cuda") else v)
  274 [loop      ]                               for k, v in inputs.items()}
  275 [stmt      ]                 with torch.no_grad():
  276 [code      ]                     logits = model(**inputs).logits_per_audio[0].cpu().numpy()
  277 [return    ]                 return {"ok": True, "tags": rank_clap_tags(cand, logits), "source": "clap"}
  278 [try_block ]             except Exception as e:
  279 [return    ]                 return {"ok": False, "error": str(e)}
  280 [code      ]         runner.add(AIStage("tags", "audio_tagger", _tag_stage, optional=True))
  281 [blank     ] 
  282 [def       ]         def _llm_stage(handle, ctx):
  283 [code      ]             lyrics = (tr.lyrics or (ctx.get("sink", {}).get("asr") or {}).get("lyrics") or "")
  284 [branch    ]             if not lyrics.strip():
  285 [return    ]                 return {"skipped": "no lyrics"}
  286 [code      ]             feats = (ctx.get("sink", {}).get("features") or {}).copy()
  287 [code      ]             feats["tags"] = (ctx.get("sink", {}).get("tags") or {}).get("tags", [])
  288 [code      ]             js = LLM.complete_json(handle, P.SYSTEM_TRACK_ANALYSIS,
  289 [code      ]                                    P.build_track_dossier_prompt(tr.title, lyrics, feats),
  290 [code      ]                                    max_tokens=3000, temperature=0.35)
  291 [code      ]             quality = validate_analysis_json(js, track_level=True)
  292 [branch    ]             if not quality["ok"]:
  293 [return    ]                 return {"error": quality["reason"], "quality": quality}
  294 [code      ]             js["quality"] = quality
  295 [return    ]             return js
  296 [code      ]         runner.add(AIStage("llm_breakdown", "analysis_llm", _llm_stage, optional=True))
  297 [blank     ] 
  298 [code      ]         report = runner.run({"track_id": tr.track_id, "artist": tr.artist})
  299 [code      ]         sink = runner.sink()
  300 [code      ]         tr.features.update(sink.get("features") or {})
  301 [branch    ]         if (sink.get("tags") or {}).get("tags"):
  302 [code      ]             tr.features["tags"] = sink["tags"]["tags"]
  303 [branch    ]         if (sink.get("asr") or {}).get("lyrics") and not tr.lyrics:
  304 [code      ]             tr.lyrics = sink["asr"]["lyrics"]
  305 [code      ]         br = sink.get("llm_breakdown")
  306 [branch    ]         if isinstance(br, dict) and "error" not in br and "skipped" not in br:
  307 [code      ]             tr.dossier = br
  308 [code      ]             tr.status = "analyzed"
  309 [branch    ]         else:
  310 [code      ]             tr.status = "partial"
  311 [code      ]             tr.dossier = {"partial": True, "report": report.to_dict()}
  312 [code      ]         self._save_track(slug, tr)
  313 [branch    ]         if progress_cb:
  314 [code      ]             progress_cb(tr.track_id, "done")
  315 [blank     ] 
  316 [def       ]     def _aggregate_artist_dossier(self, slug: str, a: ArtistEntry) -> Dict[str, Any]:
  317 [code      ]         chunks = []
  318 [loop      ]         for tid in a.tracks:
  319 [code      ]             tr = self._load_track(slug, tid)
  320 [branch    ]             if tr and tr.lyrics and tr.lyrics.strip():
  321 [code      ]                 chunks.append(f"=== {tr.title} ===\n{tr.lyrics}\n")
  322 [branch    ]         if not chunks:
  323 [return    ]             return {"note": "no lyrics collected - cannot build dossier"}
  324 [code      ]         blob = "\n".join(chunks)
  325 [branch    ]         if not registry.is_available("analysis_llm"):
  326 [return    ]             return {"note": "analysis_llm unavailable - dossier deferred",
  327 [code      ]                     "tracks_count": len(a.tracks), "lyrics_bytes": len(blob)}
  328 [stmt      ]         with registry.use("analysis_llm") as m:
  329 [code      ]             js = LLM.complete_json(m.handle, P.SYSTEM_ANALYSIS,
  330 [code      ]                                    P.build_dossier_prompt(a.artist, blob),
  331 [code      ]                                    max_tokens=2500, temperature=0.4)
  332 [code      ]         quality = validate_analysis_json(js)
  333 [branch    ]         if not quality["ok"]:
  334 [return    ]             return {
  335 [code      ]                 "note": "analysis_llm output rejected: " + str(quality["reason"]),
  336 [code      ]                 "tracks_count": len(a.tracks),
  337 [code      ]                 "quality": quality,
  338 [code      ]             }
  339 [code      ]         js["quality"] = quality
  340 [code      ]         js["tracks_count"] = len(a.tracks)
  341 [code      ]         js["updated_at"] = time.time()
  342 [return    ]         return js
  343 [blank     ] 
  344 [def       ]     def get_artist_dossier(self, artist: str) -> Optional[Dict[str, Any]]:
  345 [code      ]         a = self._load_artist(_slug(artist))
  346 [return    ]         return a.dossier if a else None
  347 [blank     ] 
  348 [def       ]     def get_track_dossier(self, artist: str, track_id: str) -> Optional[Dict[str, Any]]:
  349 [code      ]         tr = self._load_track(_slug(artist), track_id)
  350 [return    ]         return tr.dossier if tr else None
  351 [blank     ] 
  352 [def       ]     def list_artists(self) -> List[Dict[str, Any]]:
  353 [code      ]         out = []
  354 [loop      ]         for adir in sorted(self.root.iterdir()):
  355 [branch    ]             if not adir.is_dir():
  356 [code      ]                 continue
  357 [code      ]             a = self._load_artist(adir.name)
  358 [branch    ]             if a:
  359 [code      ]                 out.append({"artist": a.artist, "slug": a.slug, "tracks": len(a.tracks),
  360 [code      ]                             "has_dossier": bool(a.dossier), "updated_at": a.updated_at})
  361 [return    ]         return out
  362 [blank     ] 
  363 [def       ]     def list_tracks(self, artist: str) -> List[Dict[str, Any]]:
  364 [code      ]         slug = _slug(artist)
  365 [code      ]         a = self._load_artist(slug)
  366 [branch    ]         if not a:
  367 [return    ]             return []
  368 [code      ]         out = []
  369 [loop      ]         for tid in a.tracks:
  370 [code      ]             tr = self._load_track(slug, tid)
  371 [branch    ]             if tr:
  372 [code      ]                 out.append({"track_id": tr.track_id, "title": tr.title,
  373 [code      ]                             "status": tr.status, "has_lyrics": bool(tr.lyrics),
  374 [code      ]                             "has_audio": bool(tr.audio_path and Path(tr.audio_path).exists()),
  375 [code      ]                             "features": {k: tr.features.get(k) for k in ("bpm", "key", "tags")}})
  376 [return    ]         return out
  377 [blank     ] 
  378 [def       ]     def _save_artist(self, a: ArtistEntry) -> None:
  379 [code      ]         p = self.root / a.slug / "artist.json"
  380 [code      ]         p.parent.mkdir(parents=True, exist_ok=True)
  381 [code      ]         p.write_text(json.dumps(asdict(a), ensure_ascii=False, indent=2), encoding="utf-8")
  382 [blank     ] 
  383 [def       ]     def _load_artist(self, slug: str) -> Optional[ArtistEntry]:
  384 [code      ]         p = self.root / slug / "artist.json"
  385 [branch    ]         if not p.exists():
  386 [return    ]             return None
  387 [return    ]         return ArtistEntry(**json.loads(p.read_text(encoding="utf-8")))
  388 [blank     ] 
  389 [def       ]     def _save_track(self, slug: str, tr: TrackEntry) -> None:
  390 [code      ]         p = self.root / slug / "tracks" / f"{tr.track_id}.json"
  391 [code      ]         p.parent.mkdir(parents=True, exist_ok=True)
  392 [code      ]         p.write_text(json.dumps(asdict(tr), ensure_ascii=False, indent=2), encoding="utf-8")
  393 [blank     ] 
  394 [def       ]     def _load_track(self, slug: str, tid: str) -> Optional[TrackEntry]:
  395 [code      ]         p = self.root / slug / "tracks" / f"{tid}.json"
  396 [branch    ]         if not p.exists():
  397 [return    ]             return None
  398 [return    ]         return TrackEntry(**json.loads(p.read_text(encoding="utf-8")))
```