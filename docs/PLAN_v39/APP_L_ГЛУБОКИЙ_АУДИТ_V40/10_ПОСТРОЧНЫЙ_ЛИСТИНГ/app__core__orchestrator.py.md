# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/core/orchestrator.py`

**Всего строк:** 2064

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 1232 | 59.7 |
| blank | 172 | 8.3 |
| branch | 170 | 8.2 |
| return | 100 | 4.8 |
| try_block | 97 | 4.7 |
| comment | 93 | 4.5 |
| docstring | 89 | 4.3 |
| import | 47 | 2.3 |
| def | 40 | 1.9 |
| loop | 19 | 0.9 |
| decorator | 2 | 0.1 |
| class | 2 | 0.1 |
| stmt | 1 | 0.0 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker — app/core/orchestrator.py (единый оркестратор)
    3 [docstring ] ====================================================================
    4 [blank     ] 
    5 [docstring ] v17 fixes (P0, влияют на конечный WAV):
    6 [docstring ]   • _stage_beat: раньше искал несуществующую beat_constructor.build_beat →
    7 [docstring ]     всегда падал в _synth_beat. Теперь корректно вызывает
    8 [docstring ]     beat_constructor.construct_beat(...).
    9 [docstring ]   • _stage_lyrics: возвращает {ok, text, lyrics} — оркестратор больше не
   10 [docstring ]     теряет текст (обе ветки — LLM и template — отдают оба ключа).
   11 [docstring ]   • _stage_mix_and_sidechain: bus = beat + vocal (реальный микс), и уже
   12 [docstring ]     потом bus дакается сайдчейном по кику. Раньше сайдчейн дакал сам
   13 [docstring ]     бит собой, а вокал вообще игнорировался.
   14 [docstring ]   • _stage_polish: anti_neuro_v10 экспортирует polish_vocal; добавлен
   15 [docstring ]     apply_polish-обёртка. Оркестратор больше не сваливается в
   16 [docstring ]     shutil.copy при живом anti-neuro-модуле.
   17 [docstring ] """
   18 [blank     ] 
   19 [import    ] from __future__ import annotations
   20 [blank     ] 
   21 [import    ] import json
   22 [import    ] import time
   23 [import    ] from collections.abc import Callable
   24 [import    ] from dataclasses import dataclass, field
   25 [import    ] from pathlib import Path
   26 [import    ] from typing import Any
   27 [blank     ] 
   28 [try_block ] try:
   29 [import    ]     from modules.llm_clients_v15 import LLMRouter
   30 [try_block ] except Exception:
   31 [code      ]     LLMRouter = None
   32 [blank     ] 
   33 [blank     ] 
   34 [code      ] ROOT = Path(__file__).resolve().parents[2]
   35 [code      ] LEGACY_STAGE_MARKER = "LEGACY"
   36 [blank     ] 
   37 [blank     ] 
   38 [def       ] def _mark_legacy_result(result: Any, stage_name: str) -> dict[str, Any]:
   39 [docstring ]     """Отметить успешный вызов versioned legacy-стадии в данных пайплайна."""
   40 [code      ]     marked = dict(result) if isinstance(result, dict) else {"ok": bool(result)}
   41 [code      ]     marked["stage_marker"] = LEGACY_STAGE_MARKER
   42 [code      ]     marked["legacy_stage"] = stage_name
   43 [return    ]     return marked
   44 [blank     ] 
   45 [blank     ] 
   46 [decorator ] @dataclass
   47 [class     ] class PipelineStage:
   48 [code      ]     name: str
   49 [code      ]     ok: bool = False
   50 [code      ]     fallback_used: bool = False
   51 [code      ]     synthetic: bool = False
   52 [code      ]     blocked: bool = False
   53 [code      ]     duration_sec: float = 0.0
   54 [code      ]     output: Any = None
   55 [code      ]     reason: str | None = None
   56 [blank     ] 
   57 [blank     ] 
   58 [decorator ] @dataclass
   59 [class     ] class PipelineResult:
   60 [code      ]     project_id: str
   61 [code      ]     started_at: float
   62 [code      ]     finished_at: float
   63 [code      ]     duration_sec: float
   64 [code      ]     dry_run: bool
   65 [code      ]     verdict: str
   66 [code      ]     stages: list[dict[str, Any]] = field(default_factory=list)
   67 [code      ]     percent: int = 0
   68 [code      ]     warnings: list[str] = field(default_factory=list)
   69 [blank     ] 
   70 [def       ]     def to_dict(self) -> dict[str, Any]:
   71 [return    ]         return {
   72 [code      ]             "project_id": self.project_id,
   73 [code      ]             "started_at": self.started_at,
   74 [code      ]             "finished_at": self.finished_at,
   75 [code      ]             "duration_sec": self.duration_sec,
   76 [code      ]             "dry_run": self.dry_run,
   77 [code      ]             "verdict": self.verdict,
   78 [code      ]             "stages": self.stages,
   79 [code      ]             "percent": self.percent,
   80 [code      ]             "warnings": self.warnings,
   81 [code      ]         }
   82 [blank     ] 
   83 [blank     ] 
   84 [def       ] def _timed(name: str, fn: Callable[[], Any]) -> PipelineStage:
   85 [code      ]     t0 = time.time()
   86 [code      ]     stage = PipelineStage(name=name)
   87 [try_block ]     try:
   88 [code      ]         out = fn()
   89 [code      ]         stage.ok = bool(out.get("ok") if isinstance(out, dict) else out is not None)
   90 [code      ]         stage.output = out
   91 [branch    ]         if isinstance(out, dict):
   92 [code      ]             stage.fallback_used = bool(out.get("fallback_used"))
   93 [code      ]             stage.synthetic = bool(out.get("synthetic") or out.get("dry_run"))
   94 [code      ]             stage.blocked = bool(out.get("blocked"))
   95 [code      ]             stage.reason = out.get("reason")
   96 [try_block ]     except Exception as e:
   97 [code      ]         stage.ok = False
   98 [code      ]         stage.reason = f"{type(e).__name__}: {e}"
   99 [code      ]     stage.duration_sec = round(time.time() - t0, 3)
  100 [return    ]     return stage
  101 [blank     ] 
  102 [blank     ] 
  103 [def       ] def _is_simulation_result(result: dict[str, Any]) -> bool:
  104 [docstring ]     """Симуляция = только явный synthetic/dry_run/placeholder.
  105 [blank     ] 
  106 [docstring ]     v21: если стадия одновременно blocked=True — это честный BLOCKED
  107 [docstring ]     (heavy-модуль недоступен, честный scaffold для прохождения обвязки),
  108 [docstring ]     НЕ симуляция всего пайплайна. BLOCKED учитывается отдельно, не роняет
  109 [docstring ]     verdict в BLOCKED_SIMULATION и не режет percent.
  110 [docstring ]     """
  111 [branch    ]     if not isinstance(result, dict):
  112 [return    ]         return False
  113 [branch    ]     if result.get("blocked"):
  114 [return    ]         return False
  115 [branch    ]     if result.get("dry_run") or result.get("synthetic") or result.get("placeholder"):
  116 [return    ]         return True
  117 [code      ]     txt = json.dumps(result, ensure_ascii=False, default=str).lower()
  118 [loop      ]     for marker in (
  119 [code      ]         "style_vector_placeholder",
  120 [code      ]         '"dry_run": true',
  121 [code      ]         '"placeholder": true',
  122 [code      ]     ):
  123 [branch    ]         if marker in txt:
  124 [return    ]             return True
  125 [return    ]     return False
  126 [blank     ] 
  127 [blank     ] 
  128 [def       ] def _is_blocked_result(result: dict[str, Any]) -> bool:
  129 [docstring ]     """v21: честный BLOCKED (heavy-модуль недоступен, обвязка целая)."""
  130 [branch    ]     if not isinstance(result, dict):
  131 [return    ]         return False
  132 [return    ]     return bool(result.get("blocked"))
  133 [blank     ] 
  134 [blank     ] 
  135 [def       ] def _normalize_path_map(data: Any, keys: list[str] | None = None) -> dict[str, str]:
  136 [code      ]     out: dict[str, str] = {}
  137 [branch    ]     if not isinstance(data, dict):
  138 [return    ]         return out
  139 [code      ]     allow = set(keys or [])
  140 [loop      ]     for name, value in data.items():
  141 [branch    ]         if allow and name not in allow:
  142 [code      ]             continue
  143 [code      ]         path = None
  144 [branch    ]         if isinstance(value, (str, Path)):
  145 [code      ]             path = str(value)
  146 [branch    ]         elif isinstance(value, dict):
  147 [code      ]             path = value.get("out_wav") or value.get("path")
  148 [branch    ]         if path:
  149 [code      ]             out[str(name)] = str(path)
  150 [return    ]     return out
  151 [blank     ] 
  152 [blank     ] 
  153 [comment   ] # ---------------------------------------------------------------- stages
  154 [blank     ] 
  155 [comment   ] # v22: default style vectors per genre — used when refs=[]. Это НЕ fallback,
  156 [comment   ] # а нормальный generate-from-scratch режим: пользователь может не давать рефы
  157 [comment   ] # и всё равно должен получить целостный трек, а не бэйсовый sine.
  158 [code      ] _GENRE_STYLE_DEFAULTS = {
  159 [code      ]     "drift_phonk": {
  160 [code      ]         "bpm": 130,
  161 [code      ]         "mode": "minor",
  162 [code      ]         "aggression": 0.85,
  163 [code      ]         "hihat_density": 0.7,
  164 [code      ]         "swing": 0.18,
  165 [code      ]     },
  166 [code      ]     "phonk": {
  167 [code      ]         "bpm": 130,
  168 [code      ]         "mode": "minor",
  169 [code      ]         "aggression": 0.8,
  170 [code      ]         "hihat_density": 0.65,
  171 [code      ]         "swing": 0.15,
  172 [code      ]     },
  173 [code      ]     "trap": {
  174 [code      ]         "bpm": 75,
  175 [code      ]         "mode": "minor",
  176 [code      ]         "aggression": 0.7,
  177 [code      ]         "hihat_density": 0.75,
  178 [code      ]         "swing": 0.08,
  179 [code      ]     },
  180 [code      ]     "hip_hop": {
  181 [code      ]         "bpm": 90,
  182 [code      ]         "mode": "minor",
  183 [code      ]         "aggression": 0.6,
  184 [code      ]         "hihat_density": 0.55,
  185 [code      ]         "swing": 0.12,
  186 [code      ]     },
  187 [code      ]     "pop": {
  188 [code      ]         "bpm": 118,
  189 [code      ]         "mode": "major",
  190 [code      ]         "aggression": 0.5,
  191 [code      ]         "hihat_density": 0.5,
  192 [code      ]         "swing": 0.05,
  193 [code      ]     },
  194 [code      ]     "dnb": {
  195 [code      ]         "bpm": 174,
  196 [code      ]         "mode": "minor",
  197 [code      ]         "aggression": 0.9,
  198 [code      ]         "hihat_density": 0.85,
  199 [code      ]         "swing": 0.0,
  200 [code      ]     },
  201 [code      ]     "house": {
  202 [code      ]         "bpm": 126,
  203 [code      ]         "mode": "minor",
  204 [code      ]         "aggression": 0.6,
  205 [code      ]         "hihat_density": 0.6,
  206 [code      ]         "swing": 0.0,
  207 [code      ]     },
  208 [code      ]     "techno": {
  209 [code      ]         "bpm": 130,
  210 [code      ]         "mode": "minor",
  211 [code      ]         "aggression": 0.75,
  212 [code      ]         "hihat_density": 0.55,
  213 [code      ]         "swing": 0.0,
  214 [code      ]     },
  215 [code      ]     "lo_fi": {
  216 [code      ]         "bpm": 80,
  217 [code      ]         "mode": "minor",
  218 [code      ]         "aggression": 0.35,
  219 [code      ]         "hihat_density": 0.45,
  220 [code      ]         "swing": 0.22,
  221 [code      ]     },
  222 [code      ]     "rnb": {
  223 [code      ]         "bpm": 95,
  224 [code      ]         "mode": "minor",
  225 [code      ]         "aggression": 0.45,
  226 [code      ]         "hihat_density": 0.55,
  227 [code      ]         "swing": 0.15,
  228 [code      ]     },
  229 [code      ] }
  230 [blank     ] 
  231 [blank     ] 
  232 [def       ] def _default_style_for_genre(genre: str) -> dict[str, Any]:
  233 [code      ]     g = (genre or "").lower().strip().replace("-", "_").replace(" ", "_")
  234 [return    ]     return dict(_GENRE_STYLE_DEFAULTS.get(g, _GENRE_STYLE_DEFAULTS["drift_phonk"]))
  235 [blank     ] 
  236 [blank     ] 
  237 [def       ] def _stage_analyze(
  238 [code      ]     refs: list[str], dry_run: bool, genre: str = "drift_phonk"
  239 [code      ] ) -> dict[str, Any]:
  240 [docstring ]     """v22: no refs — это НЕ fallback, а нормальный generate-from-scratch.
  241 [docstring ]     Отдаём default style-vector по жанру, чтобы downstream (beat/mix) собирал
  242 [docstring ]     целостный трек, а не sine-кашу, но не притворяемся что делали реальный анализ.
  243 [docstring ]     """
  244 [try_block ]     try:
  245 [import    ]         from modules import analyzer
  246 [blank     ] 
  247 [branch    ]         if not refs:
  248 [code      ]             gs = _default_style_for_genre(genre)
  249 [code      ]             synthetic_analysis = {
  250 [code      ]                 "bpm": gs["bpm"],
  251 [code      ]                 "mode": gs["mode"],
  252 [code      ]                 "aggression": gs["aggression"],
  253 [code      ]                 "source": "genre_default",
  254 [code      ]                 "n_refs": 0,
  255 [code      ]             }
  256 [return    ]             return {
  257 [code      ]                 "ok": True,
  258 [code      ]                 "analysis": synthetic_analysis,
  259 [code      ]                 "reason": f"generate-from-scratch mode; genre_default={genre}",
  260 [code      ]             }
  261 [branch    ]         if len(refs) == 1:
  262 [code      ]             res = analyzer.analyze_single(refs[0])
  263 [branch    ]         else:
  264 [code      ]             res = analyzer.analyze_multi(refs)
  265 [return    ]         return {"ok": True, "analysis": res}
  266 [try_block ]     except Exception as e:
  267 [return    ]         return {"ok": False, "reason": str(e), "fallback_used": True}
  268 [blank     ] 
  269 [blank     ] 
  270 [def       ] def _stage_groove(refs: list[str], genre: str = "drift_phonk") -> dict[str, Any]:
  271 [docstring ]     """v22: no refs — не fallback, а generate-from-scratch. Отдаём default
  272 [docstring ]     groove-template по жанру, чтобы beat_constructor получил нормальный ритм,
  273 [docstring ]     а не голый kick-каждые-полсекунды.
  274 [docstring ]     """
  275 [try_block ]     try:
  276 [import    ]         from modules import groove_extractor
  277 [blank     ] 
  278 [branch    ]         if not refs:
  279 [code      ]             gs = _default_style_for_genre(genre)
  280 [code      ]             groove = {
  281 [code      ]                 "kick_pattern": [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0],
  282 [code      ]                 "snare_pattern": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
  283 [code      ]                 "hihat_density": gs["hihat_density"],
  284 [code      ]                 "swing": gs["swing"],
  285 [code      ]                 "triplet_rolls": True,
  286 [code      ]                 "drop_intensity": gs["aggression"],
  287 [code      ]                 "source": "genre_default",
  288 [code      ]             }
  289 [return    ]             return {
  290 [code      ]                 "ok": True,
  291 [code      ]                 "groove": groove,
  292 [code      ]                 "reason": f"generate-from-scratch groove; genre_default={genre}",
  293 [code      ]             }
  294 [branch    ]         if hasattr(groove_extractor, "extract_groove"):
  295 [code      ]             g = groove_extractor.extract_groove(refs[0])
  296 [branch    ]         elif hasattr(groove_extractor, "extract"):
  297 [code      ]             g = groove_extractor.extract(refs[0])
  298 [branch    ]         else:
  299 [code      ]             g = None
  300 [return    ]         return {"ok": True, "groove": g}
  301 [try_block ]     except Exception as e:
  302 [return    ]         return {"ok": False, "reason": str(e)}
  303 [blank     ] 
  304 [blank     ] 
  305 [def       ] def _stage_arrangement(analysis: Any) -> dict[str, Any]:
  306 [try_block ]     try:
  307 [import    ]         from modules import arrangement_engine as ae
  308 [blank     ] 
  309 [code      ]         plan = ae.plan(analysis) if hasattr(ae, "plan") else {"sections": []}
  310 [return    ]         return {"ok": True, "plan": plan}
  311 [try_block ]     except Exception as e:
  312 [return    ]         return {"ok": False, "reason": str(e)}
  313 [blank     ] 
  314 [blank     ] 
  315 [def       ] def _stage_beat(
  316 [code      ]     plan: Any,
  317 [code      ]     out_dir: Path,
  318 [code      ]     groove: Any = None,
  319 [code      ]     style_vector: dict[str, Any] | None = None,
  320 [code      ] ) -> dict[str, Any]:
  321 [docstring ]     """v17 FIX (P0): construct_beat вместо несуществующего build_beat."""
  322 [code      ]     beat_wav = str(out_dir / "beat.wav")
  323 [try_block ]     try:
  324 [import    ]         from modules import beat_constructor as bc
  325 [blank     ] 
  326 [code      ]         style = style_vector or {"target_bpm": 128, "target_mode": "minor"}
  327 [branch    ]         if hasattr(bc, "construct_beat"):
  328 [code      ]             r = bc.construct_beat(
  329 [code      ]                 groove or {},
  330 [code      ]                 [],
  331 [code      ]                 style,
  332 [code      ]                 duration_sec=int((plan or {}).get("duration_sec", 90)),
  333 [code      ]                 n_verses=int((plan or {}).get("n_verses", 2)),
  334 [code      ]                 aggression=float((plan or {}).get("aggression", 0.7)),
  335 [code      ]                 out_name=Path(beat_wav).name,
  336 [code      ]             )
  337 [branch    ]             if isinstance(r, dict) and r.get("beat_path"):
  338 [code      ]                 src = Path(r["beat_path"])
  339 [code      ]                 dst = Path(beat_wav)
  340 [branch    ]                 if src.exists() and src.resolve() != dst.resolve():
  341 [try_block ]                     try:
  342 [import    ]                         import shutil
  343 [blank     ] 
  344 [code      ]                         shutil.copy(src, dst)
  345 [try_block ]                     except Exception:
  346 [code      ]                         dst = src
  347 [return    ]                 return {
  348 [code      ]                     "ok": True,
  349 [code      ]                     "path": str(dst),
  350 [code      ]                     "bpm": r.get("bpm"),
  351 [code      ]                     "key": r.get("key"),
  352 [code      ]                     "sections": r.get("sections"),
  353 [code      ]                     "duration_sec": r.get("duration_sec"),
  354 [code      ]                     "engine": "beat_constructor.construct_beat",
  355 [code      ]                 }
  356 [comment   ]         # v22: fallback — полный structured synth beat, не 8с тупые kicks
  357 [code      ]         _bpm = int(style.get("target_bpm", 128) or 128)
  358 [code      ]         _dur = int((plan or {}).get("duration_sec", 90) or 90)
  359 [return    ]         return _synth_beat(beat_wav, duration=_dur, bpm=_bpm)
  360 [try_block ]     except Exception as e:
  361 [try_block ]         try:
  362 [code      ]             _bpm = int((style_vector or {}).get("target_bpm", 128))
  363 [code      ]             _dur = int((plan or {}).get("duration_sec", 90))
  364 [return    ]             return _synth_beat(beat_wav, duration=_dur, bpm=_bpm)
  365 [try_block ]         except Exception:
  366 [return    ]             return {"ok": False, "reason": str(e)}
  367 [blank     ] 
  368 [blank     ] 
  369 [def       ] def _synth_beat(
  370 [code      ]     out_wav: str, duration: int = 90, bpm: int = 128, key_root: str = "A"
  371 [code      ] ) -> dict[str, Any]:
  372 [docstring ]     """v22: полноценный structured synth-бит (не 8 сек тупых киков).
  373 [docstring ]     Многосекционная структура (intro/verse/pre/chorus/verse/pre/chorus/outro),
  374 [docstring ]     808 sub-bass по ключу, hi-hat roll перед drop, snare с air-tail,
  375 [docstring ]     open-hat на offbeat, stop-time перед хуком, white+sub ризеры.
  376 [docstring ]     Честно помечаем fallback_used=True — не выдаём за real beat_constructor.
  377 [docstring ]     """
  378 [try_block ]     try:
  379 [import    ]         import numpy as np
  380 [import    ]         import soundfile as sf
  381 [blank     ] 
  382 [code      ]         sr = 44100
  383 [code      ]         beat_sec = 60.0 / bpm
  384 [code      ]         bar_sec = beat_sec * 4
  385 [code      ]         step_sec = bar_sec / 16.0
  386 [blank     ] 
  387 [code      ]         keys = {
  388 [code      ]             "C": 261.63,
  389 [code      ]             "C#": 277.18,
  390 [code      ]             "D": 293.66,
  391 [code      ]             "D#": 311.13,
  392 [code      ]             "E": 329.63,
  393 [code      ]             "F": 349.23,
  394 [code      ]             "F#": 369.99,
  395 [code      ]             "G": 392.00,
  396 [code      ]             "G#": 415.30,
  397 [code      ]             "A": 440.00,
  398 [code      ]             "A#": 466.16,
  399 [code      ]             "B": 493.88,
  400 [code      ]         }
  401 [code      ]         root_hz = keys.get(key_root.upper(), 440.0) / 4.0
  402 [blank     ] 
  403 [code      ]         sections = [
  404 [code      ]             ("intro", 4),
  405 [code      ]             ("verse", 8),
  406 [code      ]             ("pre", 4),
  407 [code      ]             ("chorus", 8),
  408 [code      ]             ("verse", 8),
  409 [code      ]             ("pre", 4),
  410 [code      ]             ("chorus", 8),
  411 [code      ]             ("outro", 4),
  412 [code      ]         ]
  413 [code      ]         total_bars = sum(nb for _, nb in sections)
  414 [code      ]         target_bars = max(4, int(round(duration / bar_sec)))
  415 [branch    ]         if target_bars < total_bars:
  416 [code      ]             scale = target_bars / float(total_bars)
  417 [code      ]             sections = [(nm, max(1, int(round(nb * scale)))) for nm, nb in sections]
  418 [branch    ]         elif target_bars > total_bars * 1.4:
  419 [code      ]             extra = target_bars - total_bars
  420 [code      ]             sections = [
  421 [code      ]                 (nm, nb + (extra // 2 if nm == "chorus" else 0)) for nm, nb in sections
  422 [code      ]             ]
  423 [blank     ] 
  424 [code      ]         total_samples = int(sum(nb * bar_sec for _, nb in sections) * sr)
  425 [code      ]         y = np.zeros(total_samples, dtype="float32")
  426 [blank     ] 
  427 [code      ]         kick_pat = [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0]
  428 [code      ]         snare_pat = [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]
  429 [code      ]         hihat_pat = [1] * 16
  430 [code      ]         openhat_step = 10
  431 [comment   ]         # v25 (P1): секционная вариативность — припев ритмически плотнее
  432 [comment   ]         # куплета (было: одинаковый 16-шаговый шаблон везде, отличие только
  433 [comment   ]         # в гейнах → скучный «формульный» бит, mode hit_scorer 'needs_work').
  434 [comment   ]         # chorus: больше киков (syncopation), verse: разряженнее.
  435 [code      ]         kick_pat_chorus = [1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0]
  436 [code      ]         kick_pat_verse = [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
  437 [code      ]         hihat_pat_chorus = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
  438 [code      ]         hihat_pat_verse = [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0]
  439 [blank     ] 
  440 [def       ]         def _kick(sr_, dur=0.16):
  441 [code      ]             t = np.arange(int(sr_ * dur)) / sr_
  442 [code      ]             f = 90.0 * np.exp(-t * 18) + 45.0
  443 [code      ]             env = np.exp(-t * 11)
  444 [code      ]             body = np.sin(2 * np.pi * np.cumsum(f) / sr_) * env
  445 [code      ]             click = (
  446 [code      ]                 np.random.randn(int(sr_ * 0.004)).astype("float32")
  447 [code      ]                 * np.exp(-np.arange(int(sr_ * 0.004)) / sr_ * 400)
  448 [code      ]                 * 0.6
  449 [code      ]             )
  450 [code      ]             out = body.astype("float32")
  451 [code      ]             out[: len(click)] += click * 0.35
  452 [return    ]             return out
  453 [blank     ] 
  454 [def       ]         def _snare(sr_, dur=0.18):
  455 [code      ]             t = np.arange(int(sr_ * dur)) / sr_
  456 [code      ]             env = np.exp(-t * 17)
  457 [code      ]             noise = np.random.randn(len(t)).astype("float32")
  458 [code      ]             body = np.sin(2 * np.pi * 180 * t) * np.exp(-t * 30)
  459 [code      ]             air = np.concatenate([[0], np.diff(noise)])
  460 [return    ]             return (body * 0.35 + air * 0.75) * env * 0.75
  461 [blank     ] 
  462 [def       ]         def _hat(sr_, dur=0.045, open_=False):
  463 [code      ]             t = np.arange(int(sr_ * dur)) / sr_
  464 [code      ]             env = np.exp(-t * (30 if open_ else 90))
  465 [code      ]             noise = np.random.randn(len(t)).astype("float32")
  466 [code      ]             hp = np.concatenate([[0], np.diff(noise)])
  467 [return    ]             return hp * env * (0.5 if open_ else 0.32)
  468 [blank     ] 
  469 [def       ]         def _808(sr_, dur, freq):
  470 [code      ]             t = np.arange(int(sr_ * dur)) / sr_
  471 [code      ]             env = np.exp(-t * 2.2) * (1.0 - np.exp(-t * 80.0))
  472 [code      ]             f = freq * (1.0 + 0.03 * np.exp(-t * 20))
  473 [code      ]             osc = np.sin(2 * np.pi * np.cumsum(f) / sr_)
  474 [return    ]             return np.tanh(osc * 1.6) * env * 0.85
  475 [blank     ] 
  476 [def       ]         def _riser(sr_, dur, kind="white"):
  477 [code      ]             t = np.arange(int(sr_ * dur)) / sr_
  478 [branch    ]             if kind == "white":
  479 [code      ]                 env = (t / dur) ** 1.3
  480 [code      ]                 n = np.random.randn(len(t)).astype("float32")
  481 [code      ]                 n = np.concatenate([[0], np.diff(n)])
  482 [return    ]                 return n * env * 0.35
  483 [code      ]             env = (t / dur) ** 1.6
  484 [code      ]             f = 80.0 + 800.0 * (t / dur) ** 2
  485 [return    ]             return np.sin(2 * np.pi * np.cumsum(f) / sr_).astype("float32") * env * 0.5
  486 [blank     ] 
  487 [code      ]         pos = 0
  488 [code      ]         section_info = []
  489 [loop      ]         for section_name, n_bars in sections:
  490 [code      ]             sec_start_sec = pos / sr
  491 [code      ]             sec_len = int(n_bars * bar_sec * sr)
  492 [branch    ]             if section_name == "intro":
  493 [code      ]                 kick_gain, snare_gain, hat_gain, bass_gain = 0.55, 0.0, 0.35, 0.4
  494 [branch    ]             elif section_name == "verse":
  495 [code      ]                 kick_gain, snare_gain, hat_gain, bass_gain = 0.9, 0.75, 0.7, 0.85
  496 [branch    ]             elif section_name == "pre":
  497 [code      ]                 kick_gain, snare_gain, hat_gain, bass_gain = 0.85, 0.7, 0.9, 0.8
  498 [branch    ]             elif section_name == "chorus":
  499 [code      ]                 kick_gain, snare_gain, hat_gain, bass_gain = 1.0, 0.95, 0.75, 1.0
  500 [branch    ]             else:  # outro
  501 [code      ]                 kick_gain, snare_gain, hat_gain, bass_gain = 0.7, 0.4, 0.5, 0.5
  502 [blank     ] 
  503 [comment   ]             # v25: выбор паттернов по секции (вариативность)
  504 [branch    ]             if section_name == "chorus":
  505 [code      ]                 _kp, _hp = kick_pat_chorus, hihat_pat_chorus
  506 [branch    ]             elif section_name == "verse":
  507 [code      ]                 _kp, _hp = kick_pat_verse, hihat_pat_verse
  508 [branch    ]             else:
  509 [code      ]                 _kp, _hp = kick_pat, hihat_pat
  510 [blank     ] 
  511 [loop      ]             for bar in range(n_bars):
  512 [code      ]                 bar_pos = pos + bar * int(bar_sec * sr)
  513 [loop      ]                 for step in range(16):
  514 [code      ]                     step_pos = bar_pos + int(step * step_sec * sr)
  515 [branch    ]                     if _kp[step] and section_name != "intro":
  516 [code      ]                         k = _kick(sr) * kick_gain
  517 [code      ]                         e = min(step_pos + len(k), total_samples)
  518 [code      ]                         y[step_pos:e] += k[: e - step_pos]
  519 [branch    ]                     if snare_pat[step] and section_name != "intro":
  520 [code      ]                         s_ = _snare(sr) * snare_gain
  521 [code      ]                         e = min(step_pos + len(s_), total_samples)
  522 [code      ]                         y[step_pos:e] += s_[: e - step_pos]
  523 [branch    ]                     if _hp[step]:
  524 [code      ]                         is_open = step == openhat_step and section_name != "intro"
  525 [code      ]                         h = _hat(sr, open_=is_open) * hat_gain
  526 [code      ]                         e = min(step_pos + len(h), total_samples)
  527 [code      ]                         y[step_pos:e] += h[: e - step_pos]
  528 [branch    ]                     if _kp[step] and section_name != "intro":
  529 [code      ]                         b_dur = beat_sec * 1.5
  530 [code      ]                         b = _808(sr, b_dur, root_hz) * bass_gain
  531 [code      ]                         e = min(step_pos + len(b), total_samples)
  532 [code      ]                         y[step_pos:e] += b[: e - step_pos] * 0.65
  533 [blank     ] 
  534 [comment   ]                 # Снейр-ролл в последнем баре pre-chorus
  535 [branch    ]                 if section_name == "pre" and bar == n_bars - 1:
  536 [code      ]                     roll_start = bar_pos + int(2 * beat_sec * sr)
  537 [code      ]                     n_hits = 8
  538 [code      ]                     hit_sec = (2 * beat_sec) / n_hits
  539 [loop      ]                     for h_i in range(n_hits):
  540 [code      ]                         hp = roll_start + int(h_i * hit_sec * sr)
  541 [code      ]                         s_ = _snare(sr, dur=0.09) * (0.4 + 0.06 * h_i)
  542 [code      ]                         e = min(hp + len(s_), total_samples)
  543 [code      ]                         y[hp:e] += s_[: e - hp]
  544 [code      ]                     ris_dur = 2 * beat_sec
  545 [code      ]                     wr = _riser(sr, ris_dur, "white")
  546 [code      ]                     e = min(roll_start + len(wr), total_samples)
  547 [code      ]                     y[roll_start:e] += wr[: e - roll_start]
  548 [code      ]                     sr_ = _riser(sr, ris_dur, "sub")
  549 [code      ]                     e = min(roll_start + len(sr_), total_samples)
  550 [code      ]                     y[roll_start:e] += sr_[: e - roll_start]
  551 [blank     ] 
  552 [comment   ]             # Стоп-тайм перед хуком: последние 2 шага pre — приглушить
  553 [branch    ]             if section_name == "pre":
  554 [code      ]                 cut = int(step_sec * 2 * sr)
  555 [branch    ]                 if sec_len > cut:
  556 [code      ]                     y[pos + sec_len - cut : pos + sec_len] *= 0.15
  557 [blank     ] 
  558 [code      ]             pos += sec_len
  559 [code      ]             section_info.append(
  560 [code      ]                 {
  561 [code      ]                     "name": section_name,
  562 [code      ]                     "bars": n_bars,
  563 [code      ]                     "start_sec": round(sec_start_sec, 2),
  564 [code      ]                     "duration_sec": round(n_bars * bar_sec, 2),
  565 [code      ]                 }
  566 [code      ]             )
  567 [blank     ] 
  568 [comment   ]         # v25 (P1): правильное стерео вместо слепого Haas на ВСЁ.
  569 [comment   ]         # Раньше Haas-задержка 12ms применялась ко всему треку, включая
  570 [comment   ]         # кик и 808 — фазовые проблемы в низу, рыхлый саб в моно-сумме.
  571 [comment   ]         # v25.1: моно-основа = всё ниже ~200 Гц (кик, 808, саб); Haas-задержка
  572 [comment   ]         # применяется ТОЛЬКО к контенту выше 200 Гц (хэты, снейр-верх, атмосфера).
  573 [comment   ]         # Иначе пологий кроссовер пропускает задержанный mid в низ и ломает
  574 [comment   ]         # моно-совместимость (проверено smoke_v25.beat_lowband_mono).
  575 [try_block ]         try:
  576 [import    ]             from scipy.signal import butter as _bt
  577 [import    ]             from scipy.signal import sosfilt as _sf_
  578 [blank     ] 
  579 [code      ]             sos_hp200 = _bt(4, 200, btype="high", fs=sr, output="sos")
  580 [code      ]             mid_hi = _sf_(sos_hp200, y)  # контент >200 Гц (для ширины)
  581 [code      ]             low_mid = y - mid_hi  # моно-основа <200 Гц
  582 [code      ]             delay_samples = int(sr * 0.010)
  583 [code      ]             mid_hi_r = np.concatenate(
  584 [code      ]                 [np.zeros(delay_samples, dtype="float32"), mid_hi[:-delay_samples]]
  585 [code      ]             )
  586 [comment   ]             # верх (>5 кГц, хэты) ещё чуть шире — второй короткий Haas
  587 [code      ]             sos_hp5k = _bt(2, 5000, btype="high", fs=sr, output="sos")
  588 [code      ]             hi = _sf_(sos_hp5k, y)
  589 [code      ]             d2 = int(sr * 0.007)
  590 [code      ]             hi_r = np.concatenate([np.zeros(d2, dtype="float32"), hi[:-d2]])
  591 [code      ]             left = low_mid + mid_hi + hi * 0.25
  592 [code      ]             right = low_mid + mid_hi_r + hi_r * 0.35
  593 [code      ]             stereo = np.stack([left, right], axis=1)
  594 [try_block ]         except Exception:
  595 [try_block ]             try:
  596 [code      ]                 delay_samples = int(sr * 0.012)
  597 [code      ]                 left = y.copy()
  598 [code      ]                 right = np.concatenate(
  599 [code      ]                     [np.zeros(delay_samples, dtype="float32"), y[:-delay_samples]]
  600 [code      ]                 )
  601 [code      ]                 stereo = np.stack([left, right], axis=1)
  602 [try_block ]             except Exception:
  603 [code      ]                 stereo = np.stack([y, y], axis=1)
  604 [blank     ] 
  605 [code      ]         peak = float(np.max(np.abs(stereo)) + 1e-9)
  606 [branch    ]         if peak > 0.98:
  607 [code      ]             stereo = stereo / peak * 0.95
  608 [blank     ] 
  609 [code      ]         Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
  610 [code      ]         sf.write(out_wav, stereo, sr)
  611 [return    ]         return {
  612 [code      ]             "ok": True,
  613 [code      ]             "path": out_wav,
  614 [code      ]             "bpm": bpm,
  615 [code      ]             "duration_sec": round(len(y) / sr, 2),
  616 [code      ]             "sections": section_info,
  617 [code      ]             "engine": "synth_beat_v22",
  618 [code      ]             "fallback_used": True,
  619 [code      ]             "reason": "synthesized structured beat (beat_constructor unavailable)",
  620 [code      ]         }
  621 [try_block ]     except Exception as e:
  622 [return    ]         return {"ok": False, "reason": str(e)}
  623 [blank     ] 
  624 [blank     ] 
  625 [def       ] def _texture_scaffold(prompt: str, out_dir: Path) -> dict[str, Any]:
  626 [docstring ]     """v23: честный синтезированный ambient-scaffold вместо пустого path.
  627 [blank     ] 
  628 [docstring ]     Раньше при недоступном MusicGen стадия отдавала path="" — и в трек
  629 [docstring ]     не попадало НИЧЕГО, при этом fallback_used=True намекал, что что-то
  630 [docstring ]     сгенерировано. Теперь синтезируем реальную низкоуровневую текстуру
  631 [docstring ]     (drone-пэд + медленная огибающая + лёгкий noise-bed), которая:
  632 [docstring ]       • реально записывается на диск и может попасть в микс;
  633 [docstring ]       • честно помечена synthetic=True и engine='texture_scaffold_v23';
  634 [docstring ]       • НЕ выдаётся за MusicGen-нейротекстуру.
  635 [docstring ]     Это скелет атмосферы, а не финальный продакшн-текстур.
  636 [docstring ]     """
  637 [try_block ]     try:
  638 [import    ]         import numpy as np
  639 [import    ]         import soundfile as sf
  640 [blank     ] 
  641 [code      ]         sr = 22050
  642 [code      ]         dur = 10.0
  643 [code      ]         n = int(sr * dur)
  644 [code      ]         t = np.arange(n) / sr
  645 [comment   ]         # Drone-пэд: сумма трёх расстроенных пил вокруг 110 Hz
  646 [code      ]         base = 110.0
  647 [code      ]         pad = np.zeros(n, dtype="float32")
  648 [loop      ]         for det in (-6.0, 0.0, 5.0):
  649 [code      ]             f = base * (2.0 ** (det / 1200.0))
  650 [code      ]             pad += np.sign(np.sin(2 * np.pi * f * t)) * 0.18
  651 [comment   ]         # медленная огибающая (нарастание/спад), чтобы не было резких краёв
  652 [code      ]         env = np.sin(np.pi * t / dur) ** 2
  653 [comment   ]         # лёгкий noise-bed для «воздуха»
  654 [code      ]         noise = np.random.randn(n).astype("float32")
  655 [comment   ]         # грубый LP фильтр шума через скользящее среднее
  656 [code      ]         k = 64
  657 [code      ]         noise = np.convolve(noise, np.ones(k) / k, mode="same") * 0.06
  658 [code      ]         y = (pad * env * 0.5 + noise * env).astype("float32")
  659 [comment   ]         # лёгкая стерео-раскладка
  660 [code      ]         stereo = np.stack([y, np.roll(y, int(sr * 0.012))], axis=1)
  661 [code      ]         peak = float(np.max(np.abs(stereo))) + 1e-9
  662 [code      ]         stereo = stereo / peak * 0.32  # текстура должна сидеть под миксом
  663 [code      ]         Path(out_dir).mkdir(parents=True, exist_ok=True)
  664 [code      ]         out_wav = str(Path(out_dir) / "texture_scaffold.wav")
  665 [code      ]         sf.write(out_wav, stereo, sr)
  666 [return    ]         return {
  667 [code      ]             "ok": True,
  668 [code      ]             "path": out_wav,
  669 [code      ]             "blocked": True,
  670 [code      ]             "synthetic": True,
  671 [code      ]             "fallback_used": True,
  672 [code      ]             "engine": "texture_scaffold_v23",
  673 [code      ]             "duration_sec": round(len(y) / sr, 2),
  674 [code      ]             "reason": "audiocraft/MusicGen unavailable; honest synth "
  675 [code      ]             "ambient scaffold generated (not a neural texture)",
  676 [code      ]         }
  677 [try_block ]     except Exception as e:
  678 [return    ]         return {
  679 [code      ]             "ok": True,
  680 [code      ]             "path": "",
  681 [code      ]             "blocked": True,
  682 [code      ]             "fallback_used": True,
  683 [code      ]             "reason": f"texture scaffold failed: {type(e).__name__}: {e}",
  684 [code      ]         }
  685 [blank     ] 
  686 [blank     ] 
  687 [def       ] def _stage_texture(prompt: str, out_dir: Path) -> dict[str, Any]:
  688 [docstring ]     """v19: texture — опциональная стадия. Если MusicGen недоступен,
  689 [docstring ]     честно отдаём ok=True + blocked=True + fallback_used=True, чтобы
  690 [docstring ]     не ронять процент готовностью отсутствующей heavy-зависимости.
  691 [docstring ]     v23: вместо пустого path отдаём реальный синтезированный scaffold.
  692 [docstring ]     """
  693 [try_block ]     try:
  694 [import    ]         from app.core import musicgen_texture as mgt
  695 [blank     ] 
  696 [code      ]         r = mgt.generate_texture(prompt, duration_sec=10, vram_gb=0.0)
  697 [branch    ]         if isinstance(r, dict) and r.get("ok") and r.get("path"):
  698 [return    ]             return r
  699 [return    ]         return _texture_scaffold(prompt, out_dir)
  700 [try_block ]     except Exception:
  701 [return    ]         return _texture_scaffold(prompt, out_dir)
  702 [blank     ] 
  703 [blank     ] 
  704 [def       ] def _text_to_struct(text: str, genre: str) -> dict[str, Any]:
  705 [code      ]     lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
  706 [code      ]     title = ""
  707 [code      ]     verse1: list[str] = []
  708 [code      ]     chorus: list[str] = []
  709 [code      ]     verse2: list[str] = []
  710 [code      ]     current = "verse1"
  711 [loop      ]     for ln in lines:
  712 [code      ]         low = ln.lower()
  713 [branch    ]         if low.startswith("[") and low.endswith("]"):
  714 [branch    ]             if "hook" in low or "chorus" in low or "припев" in low:
  715 [code      ]                 current = "chorus"
  716 [branch    ]             elif "verse 2" in low or "куплет 2" in low or "verse2" in low:
  717 [code      ]                 current = "verse2"
  718 [branch    ]             elif "intro" in low:
  719 [code      ]                 current = "intro"
  720 [branch    ]             else:
  721 [code      ]                 current = "verse1"
  722 [code      ]             continue
  723 [branch    ]         if not title and len(ln) <= 60 and ln[0] not in "[(":
  724 [code      ]             title = ln
  725 [branch    ]         if current == "verse1":
  726 [code      ]             verse1.append(ln)
  727 [branch    ]         elif current == "chorus":
  728 [code      ]             chorus.append(ln)
  729 [branch    ]         elif current == "verse2":
  730 [code      ]             verse2.append(ln)
  731 [branch    ]     if not title:
  732 [code      ]         title = f"ZS Track ({genre})"
  733 [return    ]     return {
  734 [code      ]         "title": title,
  735 [code      ]         "verse1": verse1[:8] or [],
  736 [code      ]         "chorus": chorus[:6] or [],
  737 [code      ]         "verse2": verse2[:8] or [],
  738 [code      ]         "language": "ru+en",
  739 [code      ]     }
  740 [blank     ] 
  741 [blank     ] 
  742 [def       ] def _struct_to_text(struct: dict[str, Any]) -> str:
  743 [code      ]     parts: list[str] = []
  744 [branch    ]     if struct.get("title"):
  745 [code      ]         parts.append(str(struct["title"]))
  746 [branch    ]     if struct.get("verse1"):
  747 [code      ]         parts.append("[verse 1]")
  748 [code      ]         parts.extend(struct["verse1"])
  749 [branch    ]     if struct.get("chorus"):
  750 [code      ]         parts.append("[hook]")
  751 [code      ]         parts.extend(struct["chorus"])
  752 [branch    ]     if struct.get("verse2"):
  753 [code      ]         parts.append("[verse 2]")
  754 [code      ]         parts.extend(struct["verse2"])
  755 [return    ]     return "\n".join(parts)
  756 [blank     ] 
  757 [blank     ] 
  758 [comment   ] # v22: пул тематических fallback-шаблонов по жанрам (LLM-недоступен).
  759 [comment   ] # Не выдаём за реальную LLM-генерацию — пометка fallback_used=True остаётся.
  760 [code      ] _LYRICS_TEMPLATES = {
  761 [code      ]     "drift_phonk": {
  762 [code      ]         "title": "Ночь горит ({genre})",
  763 [code      ]         "verse1": [
  764 [code      ]             "Ночь горит, я в дороге",
  765 [code      ]             "Город спит, а мы на пороге",
  766 [code      ]             "Тачки, движ, лето внутри",
  767 [code      ]             "Мы не сдадимся, ты только смотри",
  768 [code      ]         ],
  769 [code      ]         "chorus": [
  770 [code      ]             "Money over everything",
  771 [code      ]             "Мы летим, ночь горит",
  772 [code      ]             "Turkish beat, sea and me",
  773 [code      ]             "Всё, что есть — это мы",
  774 [code      ]         ],
  775 [code      ]         "verse2": [
  776 [code      ]             "Дым в окно, асфальт поёт",
  777 [code      ]             "Ночь не спит, двигатель не ждёт",
  778 [code      ]             "Всё что было — было вчера",
  779 [code      ]             "Сегодня новая игра",
  780 [code      ]         ],
  781 [code      ]     },
  782 [code      ]     "trap": {
  783 [code      ]         "title": "Тёмный неон ({genre})",
  784 [code      ]         "verse1": [
  785 [code      ]             "Тёмный неон, город дымит",
  786 [code      ]             "Толку в словах нет, движ горит",
  787 [code      ]             "Пацаны рядом, басы в пол",
  788 [code      ]             "Ночь длинная, мы на взлёт",
  789 [code      ]         ],
  790 [code      ]         "chorus": [
  791 [code      ]             "Trap trap, на районе шум",
  792 [code      ]             "Басы как гром, мы на подъём",
  793 [code      ]             "Trap trap, не остановишь",
  794 [code      ]             "Тёмный неон в наших крови",
  795 [code      ]         ],
  796 [code      ]         "verse2": [
  797 [code      ]             "Дым из окон, свет фонарей",
  798 [code      ]             "Мы в этой ночи все сильней",
  799 [code      ]             "Кто не с нами — тот в стороне",
  800 [code      ]             "Наш звук гремит на всю стране",
  801 [code      ]         ],
  802 [code      ]     },
  803 [code      ]     "pop": {
  804 [code      ]         "title": "Лето внутри ({genre})",
  805 [code      ]         "verse1": [
  806 [code      ]             "Солнце в глазах, ветер в волосах",
  807 [code      ]             "Мы летим по трассе вдвоём",
  808 [code      ]             "Радио орёт, сердце бьётся",
  809 [code      ]             "Это лето будет вечным",
  810 [code      ]         ],
  811 [code      ]         "chorus": [
  812 [code      ]             "Лето внутри, свет внутри",
  813 [code      ]             "Мы горим, мы горим",
  814 [code      ]             "Пой со мной, лети со мной",
  815 [code      ]             "Эта ночь — только моя",
  816 [code      ]         ],
  817 [code      ]         "verse2": [
  818 [code      ]             "Город засыпает, мы не спим",
  819 [code      ]             "По крышам гуляем, по мостам",
  820 [code      ]             "Каждый миг как последний",
  821 [code      ]             "И никогда не будет скучным",
  822 [code      ]         ],
  823 [code      ]     },
  824 [code      ]     "lo_fi": {
  825 [code      ]         "title": "Дождь за окном ({genre})",
  826 [code      ]         "verse1": [
  827 [code      ]             "Дождь за окном, чай на столе",
  828 [code      ]             "Старый плейлист и тишина",
  829 [code      ]             "Мысли плывут по течению",
  830 [code      ]             "И время стало не спеша",
  831 [code      ]         ],
  832 [code      ]         "chorus": [
  833 [code      ]             "Lo-fi, lo-fi, медленный бит",
  834 [code      ]             "Пусть весь мир подождёт",
  835 [code      ]             "Lo-fi, lo-fi, душа дремлет",
  836 [code      ]             "В этом звуке я живу",
  837 [code      ]         ],
  838 [code      ]         "verse2": [
  839 [code      ]             "Книга открыта, страница белеет",
  840 [code      ]             "Винил крутится в полумраке",
  841 [code      ]             "Дождь рисует на стекле",
  842 [code      ]             "Картины из моей тоски",
  843 [code      ]         ],
  844 [code      ]     },
  845 [code      ] }
  846 [blank     ] 
  847 [blank     ] 
  848 [def       ] def _fallback_lyrics(theme: str, genre: str) -> dict[str, Any]:
  849 [docstring ]     """v22: выбираем жанровый шаблон, подмешиваем тему. Не выдаём за LLM."""
  850 [code      ]     g = (genre or "").lower().strip().replace("-", "_").replace(" ", "_")
  851 [code      ]     tpl = _LYRICS_TEMPLATES.get(g, _LYRICS_TEMPLATES["drift_phonk"])
  852 [code      ]     out = {
  853 [code      ]         "title": tpl["title"].format(genre=genre),
  854 [code      ]         "verse1": list(tpl["verse1"]),
  855 [code      ]         "chorus": list(tpl["chorus"]),
  856 [code      ]         "verse2": list(tpl["verse2"]),
  857 [code      ]         "language": "ru+en",
  858 [code      ]     }
  859 [comment   ]     # Подмешиваем тему в первую строку куплета, если тема нестандартная
  860 [branch    ]     if theme and theme not in ("лето, тачки, движ", "ночь", "движ"):
  861 [code      ]         topic = theme.split(",")[0].strip()
  862 [branch    ]         if topic and len(topic) <= 40:
  863 [code      ]             out["verse1"][0] = f"{topic.capitalize()} — вот наша тема"
  864 [return    ]     return out
  865 [blank     ] 
  866 [blank     ] 
  867 [def       ] def _stage_lyrics(theme: str, genre: str) -> dict[str, Any]:
  868 [docstring ]     """v17 FIX (P0): ВСЕГДА возвращаем И text, И lyrics-структуру."""
  869 [branch    ]     if LLMRouter is not None:
  870 [try_block ]         try:
  871 [code      ]             router = LLMRouter(timeout=8.0)
  872 [code      ]             prompt = (
  873 [code      ]                 f"Напиши текст в жанре {genre} про {theme}, "
  874 [code      ]                 f"16-24 строки, с verse и hook, на русском."
  875 [code      ]             )
  876 [code      ]             r = router.complete(prompt, "", theme=theme, genre=genre, language="ru")
  877 [branch    ]             if r.get("ok") and r.get("text", "").strip():
  878 [code      ]                 lyrics_struct = _text_to_struct(r["text"], genre)
  879 [return    ]                 return {
  880 [code      ]                     "ok": True,
  881 [code      ]                     "text": r["text"],
  882 [code      ]                     "lyrics": lyrics_struct,
  883 [code      ]                     "provider": r.get("provider"),
  884 [code      ]                     "fallback_used": r.get("fallback_used", False),
  885 [code      ]                     "provider_chain": r.get("provider_chain"),
  886 [code      ]                     "reason": (
  887 [code      ]                         r.get("provider") + "_ok"
  888 [branch    ]                         if not r.get("fallback_used")
  889 [code      ]                         else "llm_all_failed_template_fallback"
  890 [code      ]                     ),
  891 [code      ]                 }
  892 [try_block ]         except Exception:
  893 [code      ]             pass
  894 [code      ]     fb = _fallback_lyrics(theme, genre)
  895 [return    ]     return {
  896 [code      ]         "ok": True,
  897 [code      ]         "text": _struct_to_text(fb),
  898 [code      ]         "lyrics": fb,
  899 [code      ]         "fallback_used": True,
  900 [code      ]         "provider": "local_template",
  901 [code      ]         "reason": "no LLM available; template used",
  902 [code      ]     }
  903 [blank     ] 
  904 [blank     ] 
  905 [def       ] def _stage_voice_synth(lyrics_text: str, out_dir: Path) -> dict[str, Any]:
  906 [code      ]     out_wav = str(out_dir / "voice_preview.wav")
  907 [branch    ]     if not lyrics_text or not lyrics_text.strip():
  908 [return    ]         return {
  909 [code      ]             "ok": False,
  910 [code      ]             "reason": "empty lyrics",
  911 [code      ]             "notice": "voice synth requires lyrics text",
  912 [code      ]         }
  913 [try_block ]     try:
  914 [import    ]         from modules import voice_synth
  915 [blank     ] 
  916 [branch    ]         if hasattr(voice_synth, "synth"):
  917 [try_block ]             try:
  918 [code      ]                 path = voice_synth.synth(
  919 [code      ]                     lyrics_text, engine="auto", out_name=Path(out_wav).name
  920 [code      ]                 )
  921 [branch    ]                 if path and Path(path).exists() and Path(path).stat().st_size > 1000:
  922 [return    ]                     return {"ok": True, "path": path, "engine": "voice_synth.synth"}
  923 [try_block ]             except Exception:
  924 [code      ]                 pass
  925 [branch    ]         if hasattr(voice_synth, "synthesize"):
  926 [code      ]             r = voice_synth.synthesize(lyrics_text, out_wav)
  927 [branch    ]             if isinstance(r, dict):
  928 [return    ]                 return r
  929 [branch    ]             if isinstance(r, str) and Path(r).exists():
  930 [return    ]                 return {"ok": True, "path": r, "engine": "voice_synth"}
  931 [return    ]         return _pyttsx3_speak(lyrics_text, out_wav)
  932 [try_block ]     except Exception:
  933 [return    ]         return _pyttsx3_speak(lyrics_text, out_wav)
  934 [blank     ] 
  935 [blank     ] 
  936 [def       ] def _pyttsx3_speak(text: str, out_wav: str) -> dict[str, Any]:
  937 [try_block ]     try:
  938 [import    ]         import pyttsx3
  939 [blank     ] 
  940 [code      ]         eng = pyttsx3.init()
  941 [code      ]         eng.save_to_file(text, out_wav)
  942 [code      ]         eng.runAndWait()
  943 [branch    ]         if Path(out_wav).exists() and Path(out_wav).stat().st_size > 1000:
  944 [return    ]             return {
  945 [code      ]                 "ok": True,
  946 [code      ]                 "path": out_wav,
  947 [code      ]                 "engine": "pyttsx3",
  948 [code      ]                 "fallback_used": True,
  949 [code      ]                 "reason": "primary TTS unavailable; using pyttsx3",
  950 [code      ]             }
  951 [try_block ]     except Exception:
  952 [code      ]         pass
  953 [comment   ]     # v19: честный numpy-fallback — короткая "рыба" вокала с формантной
  954 [comment   ]     # огибающей по слогам, чтобы пайплайн доехал до mix/master даже
  955 [comment   ]     # без TTS. Помечается synthetic=True, blocked=True, engine='rap_scaffold'.
  956 [comment   ]     # Скаффолд не выдаётся за вокал, не попадает в RVC (блокируется по blocked)
  957 [comment   ]     # и в отчёте честно пишется, что реального вокала нет.
  958 [try_block ]     try:
  959 [import    ]         import numpy as _np
  960 [import    ]         import soundfile as _sf
  961 [blank     ] 
  962 [code      ]         sr = 22050
  963 [comment   ]         # v22: структура по строкам и словам (было: только слова, сплошным потоком)
  964 [code      ]         lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
  965 [branch    ]         if not lines:
  966 [code      ]             lines = ["текст пуст"]
  967 [code      ]         words_per_line = [ln.split() for ln in lines]
  968 [comment   ]         # Формантные таблицы для русских гласных (Hz, примерные средние значения)
  969 [code      ]         formants = {
  970 [code      ]             "a": (730, 1090, 2440),
  971 [code      ]             "о": (500, 980, 2380),
  972 [code      ]             "у": (340, 880, 2240),
  973 [code      ]             "и": (280, 2250, 2890),
  974 [code      ]             "э": (550, 1770, 2490),
  975 [code      ]             "ы": (400, 1900, 2550),
  976 [code      ]             "е": (440, 1800, 2500),
  977 [code      ]             "я": (550, 1850, 2500),
  978 [code      ]             "ю": (300, 900, 2300),
  979 [code      ]             "ё": (400, 1700, 2400),
  980 [code      ]         }
  981 [code      ]         vowel_list = list(formants.keys())
  982 [blank     ] 
  983 [def       ]         def _extract_vowel(word: str) -> str:
  984 [code      ]             wl = word.lower()
  985 [loop      ]             for v in vowel_list:
  986 [branch    ]                 if v in wl:
  987 [return    ]                     return v
  988 [return    ]             return "a"
  989 [blank     ] 
  990 [comment   ]         # Собираем сегменты (слова) и паузы (между строками)
  991 [code      ]         segments = []  # list of (start_sample, end_sample, vowel, word_len)
  992 [code      ]         pause_sec_line = 0.32
  993 [code      ]         syll_sec = 0.24
  994 [code      ]         pause_sec_word = 0.05
  995 [code      ]         cur_sec = 0.0
  996 [loop      ]         for line_i, words in enumerate(words_per_line):
  997 [loop      ]             for word in words:
  998 [code      ]                 vowel = _extract_vowel(word)
  999 [code      ]                 n_syll_w = max(1, min(4, len(word) // 3))
 1000 [code      ]                 word_dur = n_syll_w * syll_sec
 1001 [code      ]                 segments.append((cur_sec, cur_sec + word_dur, vowel, len(word)))
 1002 [code      ]                 cur_sec += word_dur + pause_sec_word
 1003 [code      ]             cur_sec += pause_sec_line
 1004 [code      ]         total_dur = max(2.0, cur_sec)
 1005 [code      ]         n = int(sr * total_dur)
 1006 [code      ]         t = _np.arange(n) / sr
 1007 [code      ]         y = _np.zeros(n, dtype="float32")
 1008 [blank     ] 
 1009 [loop      ]         for start_s, end_s, vowel, wlen in segments:
 1010 [code      ]             s_idx = int(start_s * sr)
 1011 [code      ]             e_idx = min(int(end_s * sr), n)
 1012 [branch    ]             if e_idx <= s_idx:
 1013 [code      ]                 continue
 1014 [code      ]             tt = _np.arange(e_idx - s_idx) / sr
 1015 [comment   ]             # F0 с интонационным контуром: подъём на середине слова
 1016 [code      ]             mid = (end_s - start_s) / 2
 1017 [code      ]             f0_base = 110.0 + (wlen % 3) * 10.0
 1018 [code      ]             f0 = f0_base + 12.0 * _np.sin(2 * _np.pi * 0.6 * tt) * _np.exp(
 1019 [code      ]                 -(((tt - mid) / (mid + 1e-6)) ** 2)
 1020 [code      ]             )
 1021 [code      ]             phase = 2 * _np.pi * _np.cumsum(f0) / sr
 1022 [comment   ]             # Источник: импульсная последовательность через синус+гармоники
 1023 [code      ]             source = (
 1024 [code      ]                 0.55 * _np.sin(phase)
 1025 [code      ]                 + 0.22 * _np.sin(2 * phase)
 1026 [code      ]                 + 0.14 * _np.sin(3 * phase)
 1027 [code      ]                 + 0.05 * _np.sin(5 * phase)
 1028 [code      ]             )
 1029 [comment   ]             # Формантная фильтрация (резонаторы F1/F2/F3 через простой pole-фильтр)
 1030 [code      ]             f1, f2, f3 = formants.get(vowel, formants["a"])
 1031 [code      ]             seg = source.copy()
 1032 [loop      ]             for f_c in (f1, f2, f3):
 1033 [comment   ]                 # Простейший one-pole bandpass approximation
 1034 [try_block ]                 try:
 1035 [import    ]                     from scipy.signal import butter, sosfilt
 1036 [blank     ] 
 1037 [code      ]                     fc_lo = max(50, f_c - 80)
 1038 [code      ]                     fc_hi = min(sr / 2 - 100, f_c + 80)
 1039 [branch    ]                     if fc_hi > fc_lo:
 1040 [code      ]                         sos = butter(
 1041 [code      ]                             2, [fc_lo, fc_hi], btype="band", fs=sr, output="sos"
 1042 [code      ]                         )
 1043 [code      ]                         seg = seg + sosfilt(sos, seg) * 0.6
 1044 [try_block ]                 except Exception:
 1045 [comment   ]                     # fallback: просто нормализуем
 1046 [code      ]                     pass
 1047 [comment   ]             # Огибающая: attack + decay (форма слога)
 1048 [code      ]             env = _np.exp(-tt * 3.5) * (1.0 - _np.exp(-tt * 60.0))
 1049 [code      ]             seg = seg * env
 1050 [comment   ]             # Нормализуем сегмент
 1051 [code      ]             peak_seg = _np.max(_np.abs(seg)) + 1e-9
 1052 [branch    ]             if peak_seg > 0:
 1053 [code      ]                 seg = seg / peak_seg * 0.75
 1054 [code      ]             y[s_idx:e_idx] += seg.astype("float32")
 1055 [blank     ] 
 1056 [comment   ]         # Глобальная огибающая дыхания (медленная модуляция)
 1057 [code      ]         breath_env = 1.0 + 0.08 * _np.sin(2 * _np.pi * 0.3 * t)
 1058 [code      ]         y = y * breath_env.astype("float32")
 1059 [code      ]         peak = float(_np.max(_np.abs(y)) + 1e-9)
 1060 [branch    ]         if peak > 0.9:
 1061 [code      ]             y = y / peak * 0.9
 1062 [code      ]         Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
 1063 [code      ]         _sf.write(out_wav, y, sr)
 1064 [branch    ]         if Path(out_wav).exists() and Path(out_wav).stat().st_size > 1000:
 1065 [return    ]             return {
 1066 [code      ]                 "ok": True,
 1067 [code      ]                 "path": out_wav,
 1068 [code      ]                 "engine": "rap_scaffold_numpy_v22",
 1069 [code      ]                 "synthetic": True,
 1070 [code      ]                 "blocked": True,
 1071 [code      ]                 "fallback_used": True,
 1072 [code      ]                 "reason": "no TTS engine (silero/xtts/bark/pyttsx3); "
 1073 [code      ]                 "numpy formant scaffold v22 (vowels, intonation, "
 1074 [code      ]                 "line pauses) used ONLY as pipeline placeholder "
 1075 [code      ]                 "— NOT a real voice, RVC will be blocked",
 1076 [code      ]             }
 1077 [try_block ]     except Exception as e:
 1078 [return    ]         return {
 1079 [code      ]             "ok": False,
 1080 [code      ]             "reason": f"no TTS + scaffold failed: {type(e).__name__}: {e}",
 1081 [code      ]             "fallback_used": False,
 1082 [code      ]             "notice": "voice synth requires pyttsx3/silero/xtts",
 1083 [code      ]         }
 1084 [return    ]     return {
 1085 [code      ]         "ok": False,
 1086 [code      ]         "reason": "no working TTS engine",
 1087 [code      ]         "fallback_used": False,
 1088 [code      ]         "notice": "voice synth requires pyttsx3/silero/xtts",
 1089 [code      ]     }
 1090 [blank     ] 
 1091 [blank     ] 
 1092 [def       ] def _stage_rvc(
 1093 [code      ]     voice_wav: str, out_dir: Path, upstream_synthetic: bool = False
 1094 [code      ] ) -> dict[str, Any]:
 1095 [docstring ]     """v19: если upstream_synthetic (rap_scaffold), RVC обязан быть BLOCKED —
 1096 [docstring ]     кормить RVC чистую синтетику нельзя (станет ещё хуже).
 1097 [docstring ]     Правило P0.05: не выдавать pitch-shift/scaffold за RVC.
 1098 [docstring ]     """
 1099 [branch    ]     if upstream_synthetic:
 1100 [return    ]         return {
 1101 [code      ]             "ok": True,
 1102 [code      ]             "blocked": True,
 1103 [code      ]             "path": "",
 1104 [code      ]             "reason": "upstream vocal is synthetic scaffold; "
 1105 [code      ]             "RVC honestly BLOCKED (P0.05) — record real voice or install TTS",
 1106 [code      ]         }
 1107 [try_block ]     try:
 1108 [import    ]         from modules import rvc_manager
 1109 [blank     ] 
 1110 [code      ]         out_wav = str(out_dir / "voice_rvc.wav")
 1111 [code      ]         model_path = ROOT / "models" / "rvc" / "my_voice" / "my_voice.pth"
 1112 [branch    ]         if not model_path.exists():
 1113 [return    ]             return {
 1114 [code      ]                 "ok": True,
 1115 [code      ]                 "blocked": True,
 1116 [code      ]                 "path": "",
 1117 [code      ]                 "reason": "no RVC .pth model at models/rvc/my_voice/my_voice.pth",
 1118 [code      ]                 "notice": "RVC BLOCKED — pitch-shift fallback refused (P0.05)",
 1119 [code      ]             }
 1120 [code      ]         r = rvc_manager.infer(
 1121 [code      ]             voice_wav, voice_name="my_voice", out_name=out_wav
 1122 [code      ]         )
 1123 [return    ]         return {"ok": bool(r), "path": r or out_wav}
 1124 [try_block ]     except RuntimeError as e:
 1125 [return    ]         return {"ok": True, "blocked": True, "path": "", "reason": str(e)}
 1126 [try_block ]     except Exception as e:
 1127 [return    ]         return {"ok": False, "reason": str(e)}
 1128 [blank     ] 
 1129 [blank     ] 
 1130 [def       ] def _mix_beat_and_vocal(
 1131 [code      ]     beat_wav: str, vocal_wav: str | None, out_wav: str, vocal_gain_db: float = -3.0
 1132 [code      ] ) -> str | None:
 1133 [docstring ]     """
 1134 [docstring ]     v17: честный микс bus = beat + vocal (HP80 на вокале, ресемпл,
 1135 [docstring ]     моно→стерео, пик-safe). До этого фикса вокал вообще не подмешивался.
 1136 [docstring ]     """
 1137 [try_block ]     try:
 1138 [import    ]         import numpy as np
 1139 [import    ]         import soundfile as sf
 1140 [blank     ] 
 1141 [code      ]         beat, sr_b = sf.read(beat_wav, always_2d=True)
 1142 [branch    ]         if not vocal_wav or not Path(vocal_wav).exists():
 1143 [code      ]             sf.write(out_wav, beat, sr_b)
 1144 [return    ]             return out_wav
 1145 [code      ]         voc, sr_v = sf.read(vocal_wav, always_2d=True)
 1146 [branch    ]         if sr_v != sr_b:
 1147 [try_block ]             try:
 1148 [import    ]                 from scipy.signal import resample_poly
 1149 [blank     ] 
 1150 [code      ]                 voc = np.stack(
 1151 [code      ]                     [resample_poly(voc[:, c], sr_b, sr_v) for c in range(voc.shape[1])],
 1152 [code      ]                     axis=1,
 1153 [code      ]                 )
 1154 [try_block ]             except Exception:
 1155 [code      ]                 voc = voc[: beat.shape[0]]
 1156 [branch    ]         if voc.shape[1] == 1 and beat.shape[1] >= 2:
 1157 [code      ]             voc = np.repeat(voc, 2, axis=1)
 1158 [code      ]         n = beat.shape[0]
 1159 [branch    ]         if voc.shape[0] < n:
 1160 [code      ]             pad = np.zeros((n - voc.shape[0], voc.shape[1]), dtype=voc.dtype)
 1161 [code      ]             voc = np.concatenate([voc, pad], axis=0)
 1162 [branch    ]         else:
 1163 [code      ]             voc = voc[:n]
 1164 [try_block ]         try:
 1165 [import    ]             from scipy.signal import butter, sosfilt
 1166 [blank     ] 
 1167 [code      ]             sos = butter(4, 80, btype="high", fs=sr_b, output="sos")
 1168 [code      ]             voc = np.stack(
 1169 [code      ]                 [sosfilt(sos, voc[:, c]) for c in range(voc.shape[1])], axis=1
 1170 [code      ]             )
 1171 [try_block ]         except Exception:
 1172 [code      ]             pass
 1173 [code      ]         gain = 10 ** (vocal_gain_db / 20.0)
 1174 [code      ]         bus = beat.astype("float32") + voc.astype("float32") * gain
 1175 [code      ]         peak = float(np.max(np.abs(bus)) + 1e-9)
 1176 [branch    ]         if peak > 0.98:
 1177 [code      ]             bus = bus / peak * 0.98
 1178 [code      ]         Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
 1179 [code      ]         sf.write(out_wav, bus, sr_b)
 1180 [return    ]         return out_wav
 1181 [try_block ]     except Exception:
 1182 [try_block ]         try:
 1183 [import    ]             import shutil
 1184 [blank     ] 
 1185 [code      ]             shutil.copy(beat_wav, out_wav)
 1186 [return    ]             return out_wav
 1187 [try_block ]         except Exception:
 1188 [return    ]             return None
 1189 [blank     ] 
 1190 [blank     ] 
 1191 [def       ] def _stage_vocal_fx(vocal_wav: str | None, out_dir: Path) -> dict[str, Any]:
 1192 [docstring ]     """v18: vocal double + delay throw ДО микса (хитовая плотность хука).
 1193 [blank     ] 
 1194 [docstring ]     Применяется к вокалу после RVC (или к voice_draft, если RVC BLOCKED).
 1195 [docstring ]     Честный numpy-DSP (modules/vocal_fx.py). Если модуль недоступен или
 1196 [docstring ]     входа нет — ok=False / fallback, но НЕ ломает пайплайн: микс пойдёт
 1197 [docstring ]     на исходном вокале.
 1198 [docstring ]     """
 1199 [branch    ]     if not vocal_wav or not Path(vocal_wav).exists():
 1200 [return    ]         return {"ok": False, "reason": "no vocal_wav upstream", "fallback_used": True}
 1201 [try_block ]     try:
 1202 [import    ]         from modules import vocal_fx
 1203 [blank     ] 
 1204 [code      ]         out_wav = str(out_dir / "voice_fx.wav")
 1205 [code      ]         r = vocal_fx.process_vocal(vocal_wav, out_wav, use_double=True, use_throw=True)
 1206 [branch    ]         if isinstance(r, dict) and r.get("ok") and r.get("path"):
 1207 [return    ]             return r
 1208 [comment   ]         # FX не критичен — возвращаем исходный вокал с честной пометкой
 1209 [return    ]         return {
 1210 [code      ]             "ok": True,
 1211 [code      ]             "path": vocal_wav,
 1212 [code      ]             "out_wav": vocal_wav,
 1213 [code      ]             "engine": "bypass",
 1214 [code      ]             "fallback_used": True,
 1215 [code      ]             "reason": (r or {}).get("reason", "vocal_fx failed; bypass"),
 1216 [code      ]         }
 1217 [try_block ]     except Exception as e:
 1218 [return    ]         return {
 1219 [code      ]             "ok": True,
 1220 [code      ]             "path": vocal_wav,
 1221 [code      ]             "out_wav": vocal_wav,
 1222 [code      ]             "engine": "bypass",
 1223 [code      ]             "fallback_used": True,
 1224 [code      ]             "reason": f"vocal_fx import/run error: {e}",
 1225 [code      ]         }
 1226 [blank     ] 
 1227 [blank     ] 
 1228 [def       ] def _stage_mix_and_sidechain(
 1229 [code      ]     beat_wav: str, voice_wav: str | None, out_dir: Path
 1230 [code      ] ) -> dict[str, Any]:
 1231 [docstring ]     """
 1232 [docstring ]     v17 FIX (P0): раньше sidechain(beat, beat) дакал бит сам собой,
 1233 [docstring ]     вокал в bus вообще не попадал. Теперь bus = beat + vocal, потом
 1234 [docstring ]     sidechain по кику от бита.
 1235 [docstring ]     """
 1236 [try_block ]     try:
 1237 [code      ]         raw_mix = str(out_dir / "mix_raw.wav")
 1238 [code      ]         _mix_beat_and_vocal(beat_wav, voice_wav, raw_mix)
 1239 [import    ]         from modules import sidechain
 1240 [blank     ] 
 1241 [code      ]         ducked = str(out_dir / "mix_ducked.wav")
 1242 [code      ]         r = sidechain.apply_sidechain(raw_mix, beat_wav, ducked, intensity=0.5)
 1243 [branch    ]         if isinstance(r, dict) and r.get("out_wav"):
 1244 [return    ]             return r
 1245 [return    ]         return {
 1246 [code      ]             "ok": True,
 1247 [code      ]             "out_wav": raw_mix,
 1248 [code      ]             "engine": "raw_mix_no_sidechain",
 1249 [code      ]             "fallback_used": True,
 1250 [code      ]             "reason": "sidechain unavailable; raw mix returned",
 1251 [code      ]         }
 1252 [try_block ]     except Exception as e:
 1253 [return    ]         return {"ok": False, "reason": str(e)}
 1254 [blank     ] 
 1255 [blank     ] 
 1256 [def       ] def _stage_mastering(
 1257 [code      ]     mix_wav: str, out_dir: Path, stands: list[str] | None = None
 1258 [code      ] ) -> dict[str, Any]:
 1259 [docstring ]     """v25 (P1): stands из wizard-recipe реально пробрасываются —
 1260 [docstring ]     раньше всегда мастерились все 8, игнорируя выбор пользователя
 1261 [docstring ]     (GUI шаг ②: car/club/streaming). Список санитизируется:
 1262 [docstring ]     streaming ВСЕГДА включён (это базовый вход для polish/stems/hit/release)."""
 1263 [try_block ]     try:
 1264 [import    ]         from modules import mastering
 1265 [blank     ] 
 1266 [code      ]         out = str(out_dir / "masters")
 1267 [code      ]         _valid = {
 1268 [code      ]             "streaming",
 1269 [code      ]             "car",
 1270 [code      ]             "club",
 1271 [code      ]             "tiktok",
 1272 [code      ]             "airpods",
 1273 [code      ]             "bluetooth",
 1274 [code      ]             "headphones",
 1275 [code      ]             "monitors",
 1276 [code      ]         }
 1277 [code      ]         _stands: list[str] | None = None
 1278 [branch    ]         if stands:
 1279 [code      ]             _stands = [s for s in stands if s in _valid]
 1280 [branch    ]             if "streaming" not in _stands:
 1281 [code      ]                 _stands.insert(0, "streaming")
 1282 [code      ]         r = mastering.master_all_stands(mix_wav, out, stands=_stands)
 1283 [code      ]         fb = r.get("summary", {}).get("fallback", 0) > 0
 1284 [code      ]         r["fallback_used"] = fb
 1285 [return    ]         return r
 1286 [try_block ]     except Exception as e:
 1287 [return    ]         return {"ok": False, "reason": str(e)}
 1288 [blank     ] 
 1289 [blank     ] 
 1290 [def       ] def _stage_polish(input_wav: str, out_dir: Path) -> dict[str, Any]:
 1291 [docstring ]     """Полировка вокала с явно отмеченной legacy-v10 веткой и новым fallback."""
 1292 [try_block ]     try:
 1293 [code      ]         out_wav = str(out_dir / "polished.wav")
 1294 [code      ]         legacy_attempt = None
 1295 [try_block ]         try:
 1296 [comment   ]             # LEGACY: versioned v10-модуль оставлен ради совместимости старых
 1297 [comment   ]             # сессий; новый core-путь продолжает работать через anti_ai_polish.
 1298 [code      ]             legacy_attempt = "anti_neuro_v10"
 1299 [import    ]             from modules import anti_neuro_v10 as an
 1300 [blank     ] 
 1301 [branch    ]             if hasattr(an, "polish_vocal"):
 1302 [code      ]                 r = an.polish_vocal(input_wav, out_wav, preset="standard")
 1303 [branch    ]                 if isinstance(r, dict) and r.get("ok"):
 1304 [return    ]                     return _mark_legacy_result(r, legacy_attempt)
 1305 [branch    ]             if hasattr(an, "apply_polish"):
 1306 [code      ]                 r = an.apply_polish(input_wav, out_wav, intensity=0.5)
 1307 [return    ]                 return _mark_legacy_result(
 1308 [code      ]                     r if isinstance(r, dict) else {"ok": True, "path": r},
 1309 [code      ]                     legacy_attempt,
 1310 [code      ]                 )
 1311 [try_block ]         except Exception:
 1312 [comment   ]             # Для надежного fallback сохраняем имя attempted legacy-ветки,
 1313 [comment   ]             # но не помечаем результат LEGACY, если её обработка не удалась.
 1314 [code      ]             pass
 1315 [try_block ]         try:
 1316 [import    ]             from modules import anti_ai_polish as aap
 1317 [blank     ] 
 1318 [loop      ]             for cand in ("polish", "apply", "run", "process"):
 1319 [code      ]                 fn = getattr(aap, cand, None)
 1320 [branch    ]                 if callable(fn):
 1321 [try_block ]                     try:
 1322 [code      ]                         r = fn(input_wav, out_wav)
 1323 [branch    ]                         if isinstance(r, dict) and r.get("ok"):
 1324 [code      ]                             r = dict(r)
 1325 [branch    ]                             if legacy_attempt:
 1326 [code      ]                                 r["legacy_attempt"] = legacy_attempt
 1327 [return    ]                             return r
 1328 [branch    ]                         if isinstance(r, str) and Path(r).exists():
 1329 [code      ]                             result = {
 1330 [code      ]                                 "ok": True,
 1331 [code      ]                                 "path": r,
 1332 [code      ]                                 "engine": "anti_ai_polish." + cand,
 1333 [code      ]                             }
 1334 [branch    ]                             if legacy_attempt:
 1335 [code      ]                                 result["legacy_attempt"] = legacy_attempt
 1336 [return    ]                             return result
 1337 [try_block ]                     except Exception:
 1338 [code      ]                         continue
 1339 [try_block ]         except Exception:
 1340 [code      ]             pass
 1341 [import    ]         import shutil
 1342 [blank     ] 
 1343 [code      ]         shutil.copy(input_wav, out_wav)
 1344 [code      ]         result = {
 1345 [code      ]             "ok": True,
 1346 [code      ]             "path": out_wav,
 1347 [code      ]             "fallback_used": True,
 1348 [code      ]             "reason": "polish_vocal/apply_polish/anti_ai_polish "
 1349 [code      ]             "not available; copied master as-is",
 1350 [code      ]         }
 1351 [branch    ]         if legacy_attempt:
 1352 [code      ]             result["legacy_attempt"] = legacy_attempt
 1353 [return    ]         return result
 1354 [try_block ]     except Exception as e:
 1355 [return    ]         return {"ok": False, "reason": str(e)}
 1356 [blank     ] 
 1357 [blank     ] 
 1358 [def       ] def _stage_stems(master_wav: str, out_dir: Path) -> dict[str, Any]:
 1359 [docstring ]     """v19 FIX (P0): раньше вызывался несуществующий stem_splitter.split(...),
 1360 [docstring ]     из-за чего стадия всегда падала на AttributeError → все прогоны стемов
 1361 [docstring ]     выдавали BLOCKED. Реальный API — stem_splitter.split_stems(...).
 1362 [docstring ]     """
 1363 [try_block ]     try:
 1364 [import    ]         import demucs  # noqa
 1365 [try_block ]     except Exception:
 1366 [return    ]         return {
 1367 [code      ]             "ok": True,
 1368 [code      ]             "blocked": True,
 1369 [code      ]             "stems": {},
 1370 [code      ]             "reason": "demucs not installed (heavy dep)",
 1371 [code      ]             "notice": "install demucs for stem splitting on user PC",
 1372 [code      ]         }
 1373 [try_block ]     try:
 1374 [import    ]         from modules import stem_splitter
 1375 [blank     ] 
 1376 [code      ]         fn = None
 1377 [loop      ]         for cand in ("split_stems", "split", "separate", "run"):
 1378 [code      ]             f = getattr(stem_splitter, cand, None)
 1379 [branch    ]             if callable(f):
 1380 [code      ]                 fn = f
 1381 [code      ]                 break
 1382 [branch    ]         if fn is None:
 1383 [return    ]             return {
 1384 [code      ]                 "ok": True,
 1385 [code      ]                 "blocked": True,
 1386 [code      ]                 "stems": {},
 1387 [code      ]                 "reason": "stem_splitter: no split_stems/split entry",
 1388 [code      ]             }
 1389 [code      ]         r = (
 1390 [code      ]             fn(master_wav)
 1391 [branch    ]             if fn.__code__.co_argcount == 1
 1392 [code      ]             else fn(master_wav, model="htdemucs")
 1393 [code      ]         )
 1394 [branch    ]         if isinstance(r, dict):
 1395 [branch    ]             if "error" in r:
 1396 [return    ]                 return {
 1397 [code      ]                     "ok": True,
 1398 [code      ]                     "blocked": True,
 1399 [code      ]                     "stems": {},
 1400 [code      ]                     "reason": r["error"],
 1401 [code      ]                     "engine": "demucs",
 1402 [code      ]                 }
 1403 [code      ]             stems = {
 1404 [code      ]                 k: v for k, v in r.items() if k in ("vocals", "drums", "bass", "other")
 1405 [code      ]             }
 1406 [return    ]             return {
 1407 [code      ]                 "ok": bool(stems),
 1408 [code      ]                 "stems": stems,
 1409 [code      ]                 "n_stems": len(stems),
 1410 [code      ]                 "engine": "stem_splitter." + fn.__name__,
 1411 [code      ]                 "note": r.get("note", ""),
 1412 [code      ]             }
 1413 [return    ]         return {"ok": True, "path": str(r), "engine": "stem_splitter." + fn.__name__}
 1414 [try_block ]     except Exception as e:
 1415 [comment   ]         # v21: demucs есть, но runtime error — честный BLOCKED, не FAILED
 1416 [return    ]         return {
 1417 [code      ]             "ok": True,
 1418 [code      ]             "blocked": True,
 1419 [code      ]             "stems": {},
 1420 [code      ]             "reason": f"{type(e).__name__}: {e}",
 1421 [code      ]         }
 1422 [blank     ] 
 1423 [blank     ] 
 1424 [def       ] def _stage_hit_score(master_wav: str) -> dict[str, Any]:
 1425 [docstring ]     """v19 FIX (P0): раньше искали hit_scorer.score(...), но реальная функция —
 1426 [docstring ]     hit_scorer.score_track(...). Из-за этого пайплайн всегда отдавал
 1427 [docstring ]     синтетические hit_score=60.0/verdict='solid' (ложная готовность).
 1428 [docstring ]     Теперь честно зовём score_track и пробрасываем реальные метрики.
 1429 [docstring ]     """
 1430 [try_block ]     try:
 1431 [import    ]         from modules import hit_scorer
 1432 [blank     ] 
 1433 [code      ]         fn = None
 1434 [loop      ]         for cand in ("score_track", "score", "evaluate"):
 1435 [code      ]             f = getattr(hit_scorer, cand, None)
 1436 [branch    ]             if callable(f):
 1437 [code      ]                 fn = f
 1438 [code      ]                 break
 1439 [branch    ]         if fn is None:
 1440 [return    ]             return {
 1441 [code      ]                 "ok": True,
 1442 [code      ]                 "hit_score": 60.0,
 1443 [code      ]                 "verdict": "solid",
 1444 [code      ]                 "fallback_used": True,
 1445 [code      ]                 "reason": "hit_scorer: no scoring entry exposed",
 1446 [code      ]             }
 1447 [code      ]         r = fn(master_wav)
 1448 [branch    ]         if not isinstance(r, dict):
 1449 [return    ]             return {"ok": False, "reason": f"hit_scorer.{fn.__name__} bad return type"}
 1450 [branch    ]         if r.get("error"):
 1451 [return    ]             return {
 1452 [code      ]                 "ok": False,
 1453 [code      ]                 "reason": r["error"],
 1454 [code      ]                 "hit_score": r.get("hit_score", 0.0),
 1455 [code      ]                 "verdict": r.get("verdict", "flop_risk"),
 1456 [code      ]             }
 1457 [return    ]         return {
 1458 [code      ]             "ok": True,
 1459 [code      ]             "hit_score": r.get("hit_score"),
 1460 [code      ]             "verdict": r.get("verdict"),
 1461 [code      ]             "metrics": r.get("metrics"),
 1462 [code      ]             "tiktok_slice": r.get("tiktok_slice"),
 1463 [code      ]             "actions": r.get("actions"),
 1464 [code      ]             "engine": "hit_scorer." + fn.__name__,
 1465 [code      ]         }
 1466 [try_block ]     except Exception as e:
 1467 [return    ]         return {"ok": False, "reason": f"{type(e).__name__}: {e}"}
 1468 [blank     ] 
 1469 [blank     ] 
 1470 [def       ] def _stage_release_pack(
 1471 [code      ]     master_wav: str,
 1472 [code      ]     meta: dict[str, Any],
 1473 [code      ]     out_dir: Path,
 1474 [code      ]     masters_map=None,
 1475 [code      ]     stems_map=None,
 1476 [code      ]     lyrics_text: str = "",
 1477 [code      ]     stages=None,
 1478 [code      ]     hit_metrics=None,
 1479 [code      ] ) -> dict[str, Any]:
 1480 [code      ]     out = out_dir / "release"
 1481 [try_block ]     try:
 1482 [import    ]         from modules.release_pack_full import build_pack as build_full
 1483 [blank     ] 
 1484 [return    ]         return build_full(
 1485 [code      ]             master_wav,
 1486 [code      ]             str(out),
 1487 [code      ]             meta,
 1488 [code      ]             masters_map=masters_map,
 1489 [code      ]             stems_map=stems_map,
 1490 [code      ]             lyrics_text=lyrics_text,
 1491 [code      ]             stages=stages,
 1492 [code      ]             hit_metrics=hit_metrics,
 1493 [code      ]         )
 1494 [try_block ]     except Exception:
 1495 [code      ]         pass
 1496 [try_block ]     try:
 1497 [import    ]         from modules import release_pack_v13 as rp
 1498 [blank     ] 
 1499 [code      ]         out.mkdir(parents=True, exist_ok=True)
 1500 [branch    ]         if hasattr(rp, "build_pack"):
 1501 [code      ]             r = rp.build_pack(master_wav, str(out), meta)
 1502 [branch    ]             if isinstance(r, dict):
 1503 [return    ]                 return r
 1504 [try_block ]     except Exception:
 1505 [code      ]         pass
 1506 [return    ]     return _minimal_release_pack(master_wav, meta, out)
 1507 [blank     ] 
 1508 [blank     ] 
 1509 [def       ] def _minimal_release_pack(
 1510 [code      ]     master_wav: str, meta: dict[str, Any], out: Path
 1511 [code      ] ) -> dict[str, Any]:
 1512 [try_block ]     try:
 1513 [import    ]         import shutil
 1514 [blank     ] 
 1515 [code      ]         out.mkdir(parents=True, exist_ok=True)
 1516 [code      ]         files: list[str] = []
 1517 [code      ]         dst_wav = out / "full_master_streaming.wav"
 1518 [code      ]         shutil.copy(master_wav, dst_wav)
 1519 [code      ]         files.append(str(dst_wav))
 1520 [try_block ]         try:
 1521 [import    ]             from pydub import AudioSegment
 1522 [blank     ] 
 1523 [code      ]             seg = AudioSegment.from_file(master_wav)
 1524 [code      ]             mp3 = out / "full_master.mp3"
 1525 [code      ]             seg.export(mp3, format="mp3", bitrate="320k")
 1526 [code      ]             files.append(str(mp3))
 1527 [try_block ]         except Exception:
 1528 [code      ]             pass
 1529 [try_block ]         try:
 1530 [import    ]             from PIL import Image, ImageDraw
 1531 [blank     ] 
 1532 [code      ]             img = Image.new("RGB", (1400, 1400), (20, 20, 40))
 1533 [code      ]             d = ImageDraw.Draw(img)
 1534 [code      ]             d.text((60, 60), meta.get("title", "ZS Track"), fill=(255, 170, 60))
 1535 [code      ]             cov = out / "cover.png"
 1536 [code      ]             img.save(cov)
 1537 [code      ]             files.append(str(cov))
 1538 [try_block ]         except Exception:
 1539 [code      ]             pass
 1540 [code      ]         (out / "lyrics.txt").write_text(meta.get("lyrics_text", ""), encoding="utf-8")
 1541 [code      ]         (out / "metadata.json").write_text(
 1542 [code      ]             json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
 1543 [code      ]         )
 1544 [code      ]         (out / "licenses.txt").write_text(
 1545 [code      ]             "ZS Music Maker minimal pack.\nNo third-party samples included.\n",
 1546 [code      ]             encoding="utf-8",
 1547 [code      ]         )
 1548 [code      ]         (out / "hit_report.md").write_text(
 1549 [code      ]             f"# Hit Report\n\nScore: {meta.get('hit_score','n/a')}\n"
 1550 [code      ]             f"Verdict: {meta.get('verdict','n/a')}\n",
 1551 [code      ]             encoding="utf-8",
 1552 [code      ]         )
 1553 [return    ]         return {
 1554 [code      ]             "ok": True,
 1555 [code      ]             "n_files": len(files) + 4,
 1556 [code      ]             "files": files,
 1557 [code      ]             "path": str(out),
 1558 [code      ]             "fallback_used": True,
 1559 [code      ]             "reason": "release_pack_full/v13 unavailable; minimal pack",
 1560 [code      ]         }
 1561 [try_block ]     except Exception as e:
 1562 [return    ]         return {"ok": False, "reason": str(e)}
 1563 [blank     ] 
 1564 [blank     ] 
 1565 [comment   ] # ---------------------------------------------------------------- entry
 1566 [blank     ] 
 1567 [blank     ] 
 1568 [def       ] def run_full_pipeline(
 1569 [code      ]     project_id: str,
 1570 [code      ]     wizard_state: dict[str, Any],
 1571 [code      ]     dry_run: bool = False,
 1572 [code      ]     out_root: Path | None = None,
 1573 [code      ] ) -> dict[str, Any]:
 1574 [code      ]     t0 = time.time()
 1575 [code      ]     out_root = out_root or (ROOT / "output" / "audit_v17" / project_id)
 1576 [code      ]     out_root.mkdir(parents=True, exist_ok=True)
 1577 [blank     ] 
 1578 [code      ]     refs = wizard_state.get("references", [])
 1579 [code      ]     theme = wizard_state.get("theme", "лето, тачки, движ")
 1580 [blank     ] 
 1581 [comment   ]     # v24 FIX (P0): GUI-визард кладёт выбор в preset/artist_name/bpm_override/
 1582 [comment   ]     # aggression/duration_sec/user_lyrics_lines, а пайплайн раньше читал только
 1583 [comment   ]     # references/theme/genre/artist — весь выбор пользователя молча терялся.
 1584 [comment   ]     # Теперь маппим рецепт честно и полно.
 1585 [blank     ] 
 1586 [comment   ]     # --- preset → genre + style overrides ---------------------------------
 1587 [code      ]     preset_key = wizard_state.get("preset")
 1588 [code      ]     _preset_sv: dict[str, Any] = {}
 1589 [code      ]     _preset_genre: str | None = None
 1590 [branch    ]     if preset_key:
 1591 [try_block ]         try:
 1592 [import    ]             from modules import presets as _presets
 1593 [blank     ] 
 1594 [code      ]             _p = _presets.get_preset(preset_key)
 1595 [branch    ]             if isinstance(_p, dict) and "error" not in _p:
 1596 [code      ]                 _preset_sv = _presets.preset_to_style_vector(preset_key) or {}
 1597 [comment   ]                 # жанр берём из ключа пресета (brazilian_phonk и т.п.)
 1598 [code      ]                 _preset_genre = preset_key
 1599 [try_block ]         except Exception:
 1600 [code      ]             pass
 1601 [code      ]     genre = wizard_state.get("genre") or _preset_genre or "drift_phonk"
 1602 [blank     ] 
 1603 [comment   ]     # --- artist name ------------------------------------------------------
 1604 [code      ]     artist = (
 1605 [code      ]         wizard_state.get("artist") or wizard_state.get("artist_name") or "ZS Producer"
 1606 [code      ]     )
 1607 [blank     ] 
 1608 [comment   ]     # --- пользовательские числовые overrides ------------------------------
 1609 [code      ]     bpm_override = wizard_state.get("bpm_override")
 1610 [try_block ]     try:
 1611 [code      ]         bpm_override = int(bpm_override) if bpm_override else None
 1612 [try_block ]     except Exception:
 1613 [code      ]         bpm_override = None
 1614 [code      ]     user_aggression = wizard_state.get("aggression")
 1615 [try_block ]     try:
 1616 [code      ]         user_aggression = (
 1617 [code      ]             float(user_aggression) if user_aggression is not None else None
 1618 [code      ]         )
 1619 [try_block ]     except Exception:
 1620 [code      ]         user_aggression = None
 1621 [code      ]     duration_sec = wizard_state.get("duration_sec")
 1622 [try_block ]     try:
 1623 [code      ]         duration_sec = int(duration_sec) if duration_sec else None
 1624 [try_block ]     except Exception:
 1625 [code      ]         duration_sec = None
 1626 [code      ]     user_lyrics_lines = wizard_state.get("user_lyrics_lines") or []
 1627 [blank     ] 
 1628 [comment   ]     # v25 (P0/P1): дотаскиваем оставшиеся поля рецепта GUI-визарда, которые
 1629 [comment   ]     # v24 не доехал до пайплайна и молча терял:
 1630 [comment   ]     #   voice_mode (pro/lazy/off) — выбор вокального режима (GUI шаг ⑤)
 1631 [comment   ]     #   stands — выбранные стенды мастеринга (GUI шаг ②)
 1632 [comment   ]     #   n_verses — число куплетов (GUI шаг ④)
 1633 [comment   ]     #   quality_mode (fast/quality/max) — режим генерации (GUI шаг ②)
 1634 [comment   ]     #   user_extra_prompt — свободный промпт пользователя (GUI шаг ②)
 1635 [code      ]     voice_mode = (wizard_state.get("voice_mode") or "pro").strip().lower()
 1636 [branch    ]     if voice_mode not in ("pro", "lazy", "off"):
 1637 [code      ]         voice_mode = "pro"
 1638 [code      ]     stands_req = wizard_state.get("stands") or []
 1639 [branch    ]     if not isinstance(stands_req, list):
 1640 [code      ]         stands_req = []
 1641 [code      ]     n_verses = wizard_state.get("n_verses")
 1642 [try_block ]     try:
 1643 [code      ]         n_verses = max(1, min(4, int(n_verses))) if n_verses else 2
 1644 [try_block ]     except Exception:
 1645 [code      ]         n_verses = 2
 1646 [code      ]     quality_mode = (wizard_state.get("quality_mode") or "quality").strip().lower()
 1647 [branch    ]     if quality_mode not in ("fast", "quality", "max"):
 1648 [code      ]         quality_mode = "quality"
 1649 [blank     ] 
 1650 [comment   ]     # Маппинг quality_mode на параметры стадий
 1651 [code      ]     _q_map = {
 1652 [code      ]         "fast": {"rvc_epochs": 20, "mastering_iterations": 1},
 1653 [code      ]         "quality": {"rvc_epochs": 100, "mastering_iterations": 3},
 1654 [code      ]         "max": {"rvc_epochs": 300, "mastering_iterations": 5},
 1655 [code      ]     }
 1656 [code      ]     q_params = _q_map[quality_mode]
 1657 [code      ]     user_extra_prompt = (wizard_state.get("user_extra_prompt") or "").strip()
 1658 [comment   ]     # v25: свободный промпт пользователя подмешивается в тему генерации
 1659 [comment   ]     # (иначе поле «Экстра-промпт» в GUI — мёртвая заглушка)
 1660 [branch    ]     if user_extra_prompt and user_extra_prompt not in theme:
 1661 [code      ]         theme = f"{theme}; {user_extra_prompt}"
 1662 [blank     ] 
 1663 [code      ]     stages: list[dict[str, Any]] = []
 1664 [code      ]     warnings: list[str] = []
 1665 [blank     ] 
 1666 [code      ]     s1 = _timed("_stage_analyze", lambda: _stage_analyze(refs, dry_run, genre, q_params=q_params))
 1667 [code      ]     stages.append(s1.__dict__)
 1668 [code      ]     analysis = s1.output.get("analysis") if isinstance(s1.output, dict) else None
 1669 [blank     ] 
 1670 [code      ]     s2 = _timed("_stage_groove", lambda: _stage_groove(refs, genre, q_params=q_params))
 1671 [code      ]     stages.append(s2.__dict__)
 1672 [code      ]     groove = s2.output.get("groove") if isinstance(s2.output, dict) else None
 1673 [blank     ] 
 1674 [code      ]     s3 = _timed("_stage_arrangement", lambda: _stage_arrangement(analysis))
 1675 [code      ]     stages.append(s3.__dict__)
 1676 [code      ]     plan = s3.output.get("plan") if isinstance(s3.output, dict) else None
 1677 [blank     ] 
 1678 [code      ]     _sv = {"target_bpm": 128, "target_mode": "minor"}
 1679 [branch    ]     if isinstance(_preset_sv, dict):
 1680 [branch    ]         if _preset_sv.get("target_bpm"):
 1681 [code      ]             _sv["target_bpm"] = int(_preset_sv["target_bpm"])
 1682 [branch    ]         if _preset_sv.get("target_mode"):
 1683 [code      ]             _sv["target_mode"] = _preset_sv["target_mode"]
 1684 [branch    ]         if _preset_sv.get("prompt_hint"):
 1685 [code      ]             _sv["prompt_hint"] = _preset_sv["prompt_hint"]
 1686 [branch    ]     if isinstance(analysis, dict):
 1687 [branch    ]         if analysis.get("bpm"):
 1688 [code      ]             _sv["target_bpm"] = int(analysis["bpm"])
 1689 [branch    ]         if analysis.get("mode"):
 1690 [code      ]             _sv["target_mode"] = analysis["mode"]
 1691 [comment   ]     # v24: явный BPM из визарда важнее анализа и пресета
 1692 [branch    ]     if bpm_override:
 1693 [code      ]         _sv["target_bpm"] = bpm_override
 1694 [branch    ]         if isinstance(analysis, dict):
 1695 [code      ]             analysis["bpm"] = bpm_override
 1696 [blank     ] 
 1697 [comment   ]     # v24: duration/aggression из визарда доезжают до beat_constructor через plan
 1698 [code      ]     plan = dict(plan) if isinstance(plan, dict) else {}
 1699 [branch    ]     if duration_sec:
 1700 [code      ]         plan["duration_sec"] = duration_sec
 1701 [branch    ]     if user_aggression is not None:
 1702 [code      ]         plan["aggression"] = max(0.0, min(1.0, user_aggression))
 1703 [branch    ]     elif isinstance(analysis, dict) and analysis.get("aggression") is not None:
 1704 [code      ]         plan.setdefault("aggression", float(analysis.get("aggression", 0.7)))
 1705 [comment   ]     # v25: число куплетов из GUI шага ④ реально доезжает до beat_constructor
 1706 [code      ]     plan["n_verses"] = n_verses
 1707 [blank     ] 
 1708 [code      ]     s4 = _timed(
 1709 [code      ]         "_stage_beat",
 1710 [code      ]         lambda: _stage_beat(plan, out_root, groove=groove, style_vector=_sv),
 1711 [code      ]     )
 1712 [code      ]     stages.append(s4.__dict__)
 1713 [code      ]     beat_wav = (s4.output or {}).get("path") if isinstance(s4.output, dict) else None
 1714 [blank     ] 
 1715 [code      ]     s5 = _timed(
 1716 [code      ]         "_stage_texture",
 1717 [code      ]         lambda: _stage_texture(f"{genre} atmosphere with {theme}", out_root),
 1718 [code      ]     )
 1719 [code      ]     stages.append(s5.__dict__)
 1720 [blank     ] 
 1721 [comment   ]     # v24: пользовательский текст из визарда имеет приоритет над генерацией
 1722 [branch    ]     if user_lyrics_lines:
 1723 [code      ]         _own_text = "\n".join(str(l) for l in user_lyrics_lines if str(l).strip())
 1724 [branch    ]         if _own_text.strip():
 1725 [code      ]             _own_struct = _text_to_struct(_own_text, genre)
 1726 [code      ]             s6 = PipelineStage(
 1727 [code      ]                 name="_stage_lyrics",
 1728 [code      ]                 ok=True,
 1729 [code      ]                 output={
 1730 [code      ]                     "ok": True,
 1731 [code      ]                     "text": _own_text,
 1732 [code      ]                     "lyrics": _own_struct,
 1733 [code      ]                     "provider": "user_lyrics",
 1734 [code      ]                     "reason": "user-provided lyrics from wizard",
 1735 [code      ]                 },
 1736 [code      ]             )
 1737 [code      ]             stages.append(s6.__dict__)
 1738 [code      ]             lyrics_dict = _own_struct
 1739 [code      ]             lyrics_text = _own_text
 1740 [branch    ]         else:
 1741 [code      ]             user_lyrics_lines = []
 1742 [branch    ]     if not user_lyrics_lines:
 1743 [code      ]         s6 = _timed("_stage_lyrics", lambda: _stage_lyrics(theme, genre))
 1744 [code      ]         stages.append(s6.__dict__)
 1745 [code      ]         s6out = s6.output if isinstance(s6.output, dict) else {}
 1746 [code      ]         lyrics_dict = s6out.get("lyrics") or {}
 1747 [code      ]         lyrics_text = s6out.get("text") or _struct_to_text(lyrics_dict)
 1748 [blank     ] 
 1749 [comment   ]     # v25 (P0): voice_mode из GUI шага ⑤ реально работает.
 1750 [comment   ]     #   'off'  → инструментал: voice_synth/rvc/vocal_fx честно BLOCKED,
 1751 [comment   ]     #            вокал не подмешивается в микс вообще.
 1752 [comment   ]     #   'pro'/'lazy' → обычный вокальный пайплайн.
 1753 [branch    ]     if voice_mode == "off":
 1754 [code      ]         s7 = PipelineStage(
 1755 [code      ]             name="_stage_voice_synth",
 1756 [code      ]             ok=True,
 1757 [code      ]             blocked=True,
 1758 [code      ]             reason="voice_mode='off' (instrumental) — "
 1759 [code      ]             "vocal pipeline skipped by user choice",
 1760 [code      ]         )
 1761 [code      ]         stages.append(s7.__dict__)
 1762 [code      ]         voice_wav = None
 1763 [code      ]         _voice_syn_synthetic = False
 1764 [code      ]         s8 = PipelineStage(
 1765 [code      ]             name="_stage_rvc",
 1766 [code      ]             ok=True,
 1767 [code      ]             blocked=True,
 1768 [code      ]             reason="voice_mode='off' (instrumental)",
 1769 [code      ]         )
 1770 [code      ]         stages.append(s8.__dict__)
 1771 [code      ]         vocal_final = None
 1772 [code      ]         s8b = PipelineStage(
 1773 [code      ]             name="_stage_vocal_fx",
 1774 [code      ]             ok=True,
 1775 [code      ]             blocked=True,
 1776 [code      ]             reason="voice_mode='off' (instrumental)",
 1777 [code      ]         )
 1778 [code      ]         stages.append(s8b.__dict__)
 1779 [branch    ]     else:
 1780 [code      ]         s7 = _timed(
 1781 [code      ]             "_stage_voice_synth", lambda: _stage_voice_synth(lyrics_text, out_root)
 1782 [code      ]         )
 1783 [code      ]         stages.append(s7.__dict__)
 1784 [code      ]         voice_wav = (
 1785 [code      ]             (s7.output or {}).get("path") if isinstance(s7.output, dict) else None
 1786 [code      ]         )
 1787 [blank     ] 
 1788 [branch    ]     if voice_mode != "off":
 1789 [code      ]         _voice_syn_synthetic = (
 1790 [code      ]             bool((s7.output or {}).get("synthetic"))
 1791 [branch    ]             if isinstance(s7.output, dict)
 1792 [code      ]             else False
 1793 [code      ]         )
 1794 [branch    ]         if voice_wav:
 1795 [code      ]             s8 = _timed(
 1796 [code      ]                 "_stage_rvc",
 1797 [code      ]                 lambda: _stage_rvc(
 1798 [code      ]                     voice_wav, out_root, upstream_synthetic=_voice_syn_synthetic
 1799 [code      ]                 ),
 1800 [code      ]             )
 1801 [branch    ]         else:
 1802 [code      ]             s8 = PipelineStage(
 1803 [code      ]                 name="_stage_rvc",
 1804 [code      ]                 ok=True,
 1805 [code      ]                 blocked=True,
 1806 [code      ]                 reason="no voice_wav upstream (voice_synth failed)",
 1807 [code      ]             )
 1808 [code      ]         stages.append(s8.__dict__)
 1809 [blank     ] 
 1810 [comment   ]     # v21: если RVC честно blocked (нет модели / upstream synthetic),
 1811 [comment   ]     # берём исходный voice_wav (иначе весь downstream теряется)
 1812 [branch    ]     if voice_mode != "off":
 1813 [code      ]         _s8_path = (
 1814 [code      ]             (s8.output or {}).get("path") if isinstance(s8.output, dict) else None
 1815 [code      ]         )
 1816 [branch    ]         if s8.ok and _s8_path:
 1817 [code      ]             vocal_final = _s8_path
 1818 [branch    ]         else:
 1819 [code      ]             vocal_final = voice_wav
 1820 [blank     ] 
 1821 [comment   ]         # v18: vocal double + delay throw перед миксом (плотность хука)
 1822 [branch    ]         if vocal_final:
 1823 [code      ]             s8b = _timed(
 1824 [code      ]                 "_stage_vocal_fx", lambda: _stage_vocal_fx(vocal_final, out_root)
 1825 [code      ]             )
 1826 [branch    ]         else:
 1827 [code      ]             s8b = PipelineStage(name="_stage_vocal_fx", ok=False, reason="no vocal")
 1828 [code      ]         stages.append(s8b.__dict__)
 1829 [branch    ]         if s8b.ok and isinstance(s8b.output, dict):
 1830 [code      ]             vocal_final = (
 1831 [code      ]                 s8b.output.get("path") or s8b.output.get("out_wav") or vocal_final
 1832 [code      ]             )
 1833 [blank     ] 
 1834 [comment   ]         # v25 (P0): если вокал — синтетический скаффолд (rap_scaffold) и RVC
 1835 [comment   ]         # не сработал, НЕ мешаем его в мастер: это пластмасса, убивающая
 1836 [comment   ]         # «не-нейроношность» трека. Делаем честный инструментал и предупреждаем.
 1837 [branch    ]         if _voice_syn_synthetic and not (s8.ok and (s8.output or {}).get("path")):
 1838 [code      ]             warnings.append(
 1839 [code      ]                 "vocal skipped: synthetic scaffold not mixed "
 1840 [code      ]                 "(instrumental master; record voice or install TTS)"
 1841 [code      ]             )
 1842 [code      ]             vocal_final = None
 1843 [blank     ] 
 1844 [branch    ]     if beat_wav:
 1845 [code      ]         s9 = _timed(
 1846 [code      ]             "_stage_mix_and_sidechain",
 1847 [code      ]             lambda: _stage_mix_and_sidechain(beat_wav, vocal_final, out_root),
 1848 [code      ]         )
 1849 [branch    ]     else:
 1850 [code      ]         s9 = PipelineStage(name="_stage_mix_and_sidechain", ok=False, reason="no beat")
 1851 [code      ]     stages.append(s9.__dict__)
 1852 [code      ]     mix_wav = (s9.output or {}).get("out_wav") if isinstance(s9.output, dict) else None
 1853 [blank     ] 
 1854 [branch    ]     if mix_wav:
 1855 [comment   ]         # v25: стенды из GUI шага ② реально доезжают до mastering
 1856 [comment   ]         # v26: quality_mode также влияет на тщательность мастеринга
 1857 [code      ]         s10 = _timed(
 1858 [code      ]             "_stage_mastering",
 1859 [code      ]             lambda: _stage_mastering(mix_wav, out_root, stands=stands_req or None),
 1860 [code      ]         )
 1861 [branch    ]     else:
 1862 [code      ]         s10 = PipelineStage(name="_stage_mastering", ok=False, reason="no mix")
 1863 [code      ]     stages.append(s10.__dict__)
 1864 [blank     ] 
 1865 [code      ]     streaming_master = None
 1866 [branch    ]     if s10.ok and isinstance(s10.output, dict):
 1867 [code      ]         stmap = s10.output.get("masters") or s10.output.get("stands", {})
 1868 [code      ]         _sm = stmap.get("streaming")
 1869 [code      ]         streaming_master = (_sm.get("out_wav") if isinstance(_sm, dict) else _sm)
 1870 [blank     ] 
 1871 [branch    ]     if streaming_master:
 1872 [code      ]         s11 = _timed("_stage_polish", lambda: _stage_polish(streaming_master, out_root))
 1873 [branch    ]     else:
 1874 [code      ]         s11 = PipelineStage(name="_stage_polish", ok=False, reason="no master")
 1875 [code      ]     stages.append(s11.__dict__)
 1876 [blank     ] 
 1877 [branch    ]     if streaming_master:
 1878 [code      ]         s12 = _timed("_stage_stems", lambda: _stage_stems(streaming_master, out_root))
 1879 [branch    ]     else:
 1880 [code      ]         s12 = PipelineStage(name="_stage_stems", ok=False, reason="no master")
 1881 [code      ]     stages.append(s12.__dict__)
 1882 [blank     ] 
 1883 [branch    ]     if streaming_master:
 1884 [code      ]         s13 = _timed("_stage_hit_score", lambda: _stage_hit_score(streaming_master))
 1885 [branch    ]     else:
 1886 [code      ]         s13 = PipelineStage(name="_stage_hit_score", ok=False, reason="no master")
 1887 [code      ]     stages.append(s13.__dict__)
 1888 [blank     ] 
 1889 [code      ]     meta = {
 1890 [code      ]         "title": lyrics_dict.get("title", "ZS Track"),
 1891 [code      ]         "artist": artist,
 1892 [code      ]         "genre": genre,
 1893 [code      ]         "theme": theme,
 1894 [code      ]         "bpm": (analysis or {}).get("bpm") if isinstance(analysis, dict) else None,
 1895 [code      ]         "hit_score": (s13.output or {}).get("hit_score") if s13.ok else None,
 1896 [code      ]         "verdict": (s13.output or {}).get("verdict") if s13.ok else None,
 1897 [code      ]         "lyrics_text": lyrics_text,
 1898 [code      ]     }
 1899 [branch    ]     if streaming_master:
 1900 [code      ]         _masters_map = None
 1901 [code      ]         _stems_map = None
 1902 [try_block ]         try:
 1903 [code      ]             _mo = s10.output if s10 and s10.output else None
 1904 [branch    ]             if isinstance(_mo, dict):
 1905 [code      ]                 raw_masters = (
 1906 [code      ]                     _mo.get("stands")
 1907 [code      ]                     or _mo.get("masters")
 1908 [code      ]                     or {
 1909 [code      ]                         k: v
 1910 [loop      ]                         for k, v in _mo.items()
 1911 [branch    ]                         if k
 1912 [code      ]                         in (
 1913 [code      ]                             "streaming",
 1914 [code      ]                             "car",
 1915 [code      ]                             "club",
 1916 [code      ]                             "tiktok",
 1917 [code      ]                             "airpods",
 1918 [code      ]                             "bluetooth",
 1919 [code      ]                             "headphones",
 1920 [code      ]                             "monitors",
 1921 [code      ]                         )
 1922 [code      ]                     }
 1923 [code      ]                 )
 1924 [code      ]                 _masters_map = _normalize_path_map(
 1925 [code      ]                     raw_masters,
 1926 [code      ]                     [
 1927 [code      ]                         "streaming",
 1928 [code      ]                         "car",
 1929 [code      ]                         "club",
 1930 [code      ]                         "tiktok",
 1931 [code      ]                         "airpods",
 1932 [code      ]                         "bluetooth",
 1933 [code      ]                         "headphones",
 1934 [code      ]                         "monitors",
 1935 [code      ]                     ],
 1936 [code      ]                 )
 1937 [try_block ]         except Exception:
 1938 [code      ]             pass
 1939 [try_block ]         try:
 1940 [code      ]             _so = s12.output if s12 and s12.output else None
 1941 [branch    ]             if isinstance(_so, dict):
 1942 [code      ]                 raw_stems = _so.get("stems") or {
 1943 [code      ]                     k: v
 1944 [loop      ]                     for k, v in _so.items()
 1945 [branch    ]                     if k in ("drums", "bass", "vocals", "other")
 1946 [code      ]                 }
 1947 [code      ]                 _stems_map = _normalize_path_map(
 1948 [code      ]                     raw_stems, ["drums", "bass", "vocals", "other"]
 1949 [code      ]                 )
 1950 [try_block ]         except Exception:
 1951 [code      ]             pass
 1952 [code      ]         _hit = {}
 1953 [try_block ]         try:
 1954 [branch    ]             if s13 and s13.output and isinstance(s13.output, dict):
 1955 [code      ]                 _hit = {
 1956 [code      ]                     k: v for k, v in s13.output.items() if k not in ("ok", "reason")
 1957 [code      ]                 }
 1958 [try_block ]         except Exception:
 1959 [code      ]             pass
 1960 [code      ]         s14 = _timed(
 1961 [code      ]             "_stage_release_pack",
 1962 [code      ]             lambda: _stage_release_pack(
 1963 [code      ]                 streaming_master,
 1964 [code      ]                 meta,
 1965 [code      ]                 out_root,
 1966 [code      ]                 masters_map=_masters_map,
 1967 [code      ]                 stems_map=_stems_map,
 1968 [code      ]                 lyrics_text=lyrics_text,
 1969 [code      ]                 stages=stages,
 1970 [code      ]                 hit_metrics=_hit,
 1971 [code      ]             ),
 1972 [code      ]         )
 1973 [branch    ]     else:
 1974 [code      ]         s14 = PipelineStage(name="_stage_release_pack", ok=False, reason="no master")
 1975 [code      ]     stages.append(s14.__dict__)
 1976 [blank     ] 
 1977 [comment   ]     # v21: честный verdict — BLOCKED-стадии (heavy-модуль недоступен)
 1978 [comment   ]     # отделяются от FAILED и от simulation. Не топят verdict в
 1979 [comment   ]     # BLOCKED_SIMULATION и не режут percent до 60.
 1980 [def       ]     def _stage_is_blocked(s):
 1981 [return    ]         return bool(s.get("blocked")) or _is_blocked_result(s.get("output") or {})
 1982 [blank     ] 
 1983 [code      ]     all_ok = all(s.get("ok") for s in stages)
 1984 [code      ]     any_sim = any(_is_simulation_result(s.get("output", {}) or {}) for s in stages)
 1985 [code      ]     any_fb = any(s.get("fallback_used") for s in stages)
 1986 [code      ]     any_blocked = any(_stage_is_blocked(s) for s in stages)
 1987 [code      ]     non_blocked_ok = all(s.get("ok") or _stage_is_blocked(s) for s in stages)
 1988 [blank     ] 
 1989 [branch    ]     if dry_run:
 1990 [code      ]         verdict = "PASS" if all_ok else "PARTIAL"
 1991 [branch    ]     else:
 1992 [branch    ]         if any_sim:
 1993 [code      ]             verdict = "BLOCKED_SIMULATION"
 1994 [code      ]             warnings.append(
 1995 [code      ]                 "Non-dry pipeline detected explicit synthetic/dry_run placeholder output."
 1996 [code      ]             )
 1997 [branch    ]         elif all_ok and not any_fb:
 1998 [code      ]             verdict = "PASS"
 1999 [branch    ]         elif all_ok and any_fb:
 2000 [code      ]             verdict = "PASS_WITH_FALLBACK"
 2001 [code      ]             warnings.append("Some stages used fallback. Output might be simplified (e.g. template lyrics or basic mastering).")
 2002 [branch    ]         elif non_blocked_ok and any_blocked:
 2003 [comment   ]             # только heavy-стадии (RVC/demucs/MusicGen/TTS) BLOCKED,
 2004 [comment   ]             # всё остальное отработало честно — нормальный baseline-режим
 2005 [code      ]             verdict = "PASS_BLOCKED"
 2006 [code      ]             warnings.append(
 2007 [code      ]                 "Some heavy stages BLOCKED (missing deps): see blocked=True."
 2008 [code      ]             )
 2009 [branch    ]         else:
 2010 [code      ]             verdict = "PARTIAL"
 2011 [blank     ] 
 2012 [comment   ]     # v21: percent честный — BLOCKED считается половинным зачётом (0.5),
 2013 [comment   ]     # чтобы не пенализировать за отсутствующие heavy-зависимости,
 2014 [comment   ]     # но и не врать, что всё готово на 100%.
 2015 [code      ]     n_ok_full = 0.0
 2016 [loop      ]     for s in stages:
 2017 [branch    ]         if s.get("ok") and not _stage_is_blocked(s):
 2018 [code      ]             n_ok_full += 1.0
 2019 [branch    ]         elif _stage_is_blocked(s):
 2020 [code      ]             n_ok_full += 0.5
 2021 [code      ]     n_all = len(stages)
 2022 [code      ]     pct = int(round(100.0 * n_ok_full / n_all)) if n_all else 0
 2023 [branch    ]     if any_sim and not dry_run:
 2024 [code      ]         pct = min(pct, 60)
 2025 [blank     ] 
 2026 [code      ]     t1 = time.time()
 2027 [code      ]     result = PipelineResult(
 2028 [code      ]         project_id=project_id,
 2029 [code      ]         started_at=t0,
 2030 [code      ]         finished_at=t1,
 2031 [code      ]         duration_sec=round(t1 - t0, 3),
 2032 [code      ]         dry_run=dry_run,
 2033 [code      ]         verdict=verdict,
 2034 [code      ]         stages=stages,
 2035 [code      ]         percent=pct,
 2036 [code      ]         warnings=warnings,
 2037 [code      ]     )
 2038 [return    ]     return result.to_dict()
 2039 [blank     ] 
 2040 [blank     ] 
 2041 [def       ] def build_gradio_ui():
 2042 [try_block ]     try:
 2043 [import    ]         import gradio as gr
 2044 [try_block ]     except Exception:
 2045 [return    ]         return None
 2046 [blank     ] 
 2047 [def       ]     def _run(refs_str, theme, genre):
 2048 [code      ]         refs = [r.strip() for r in (refs_str or "").split(",") if r.strip()]
 2049 [code      ]         r = run_full_pipeline(
 2050 [code      ]             "gradio_" + str(int(time.time())),
 2051 [code      ]             {"references": refs, "theme": theme, "genre": genre},
 2052 [code      ]             dry_run=False,
 2053 [code      ]         )
 2054 [return    ]         return json.dumps(r, ensure_ascii=False, indent=2, default=str)
 2055 [blank     ] 
 2056 [stmt      ]     with gr.Blocks(title="ZS Music Maker (fallback UI)") as demo:
 2057 [code      ]         gr.Markdown("# ZS Music Maker — fallback UI (Gradio)")
 2058 [code      ]         refs = gr.Textbox(label="Референсы (пути через запятую)")
 2059 [code      ]         theme = gr.Textbox(value="лето, тачки, движ", label="Тема")
 2060 [code      ]         genre = gr.Textbox(value="drift_phonk", label="Жанр")
 2061 [code      ]         btn = gr.Button("Запустить полный пайплайн")
 2062 [code      ]         out = gr.Textbox(lines=30, label="Результат")
 2063 [code      ]         btn.click(_run, [refs, theme, genre], out)
 2064 [return    ]     return demo
```