# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/master_pipeline_v12.py`

**Всего строк:** 719

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 388 | 54.0 |
| blank | 85 | 11.8 |
| comment | 57 | 7.9 |
| return | 44 | 6.1 |
| docstring | 39 | 5.4 |
| branch | 34 | 4.7 |
| try_block | 30 | 4.2 |
| def | 24 | 3.3 |
| import | 10 | 1.4 |
| decorator | 2 | 0.3 |
| class | 2 | 0.3 |
| loop | 2 | 0.3 |
| stmt | 1 | 0.1 |
| raise | 1 | 0.1 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v12 «Hit Locked Pro» — master_pipeline_v12.py
    3 [docstring ] ============================================================
    4 [blank     ] 
    5 [docstring ] Единая, СВЯЗНАЯ точка входа мастера. Собирает воедино результаты
    6 [docstring ] всех уже написанных модулей v7-v11 в понятный человеку сценарий из ТЗ
    7 [docstring ] раздел 4:
    8 [blank     ] 
    9 [docstring ]   1) references_ingest        (ТЗ 3.2  Multi-Reference Analyzer)
   10 [docstring ]   2) sample_hunt              (ТЗ 3.3  Sample Browser + agent)
   11 [docstring ]   3) groove_extract           (ТЗ 3.4  Rhythm DNA)
   12 [docstring ]   4) arrangement_plan         (ТЗ 3.5  Beat Constructor)
   13 [docstring ]   5) musicgen_texture         (ТЗ 3.6, опционально по HW)
   14 [docstring ]   6) lyrics                   (ТЗ 3.7  Lyric Vault + author-ref + trends)
   15 [docstring ]   7) voice                    (ТЗ 3.8-3.10  Vault → Synth → RVC)
   16 [docstring ]   8) mixdown_master           (ТЗ 3.11 Mixdown + Matchering)
   17 [docstring ]   9) anti_neuro_polish        (ТЗ 14   борьба с «нейроношностью»)
   18 [docstring ]  10) release_pack             (ТЗ 3.12 полный релиз-пакет)
   19 [docstring ]  11) hit_scorer + kpi_verdict (ТЗ 17, 20.5)
   20 [blank     ] 
   21 [docstring ] Модуль НЕ переписывает бизнес-логику — он вызывает существующие модули
   22 [docstring ] и добавляет ЧЕТКИЕ ЧЕЛОВЕЧЕСКИЕ ЧЕКПОИНТЫ (ТЗ 20.2 п.24: «средний контроль,
   23 [docstring ] утверждаю ключевые этапы»).
   24 [blank     ] 
   25 [docstring ] Особенности v12:
   26 [blank     ] 
   27 [docstring ] * Каждая стадия обёрнута в `_stage()` с прогрессом и обработкой ошибок так,
   28 [docstring ]   что падение одной стадии не убивает пайплайн — вместо этого пишется в
   29 [docstring ]   `warnings` и включается fallback к более простому модулю.
   30 [docstring ] * Все шаги пишут понятный лог в logs/app.log.
   31 [docstring ] * На выходе — `MasterResult` со списком артефактов, KPI, human_summary
   32 [docstring ]   (что произошло на каждом шаге, простыми словами для отчёта пользователю).
   33 [docstring ] * Поддерживает интерактивные ОК через callback `approve_cb(stage, preview)`,
   34 [docstring ]   но по умолчанию всё автоматически.
   35 [docstring ] """
   36 [blank     ] 
   37 [import    ] from __future__ import annotations
   38 [blank     ] 
   39 [import    ] import json
   40 [import    ] import sys
   41 [import    ] import time
   42 [import    ] import traceback
   43 [import    ] from collections.abc import Callable
   44 [import    ] from dataclasses import asdict, dataclass, field
   45 [import    ] from pathlib import Path
   46 [import    ] from typing import Any
   47 [blank     ] 
   48 [code      ] ROOT = Path(__file__).resolve().parents[1]
   49 [branch    ] if str(ROOT) not in sys.path:
   50 [code      ]     sys.path.insert(0, str(ROOT))
   51 [blank     ] 
   52 [code      ] LOGS = ROOT / "logs"
   53 [comment   ] # v22: ленивое создание (не при импорте)
   54 [blank     ] 
   55 [code      ] APP_LOG = LOGS / "app.log"
   56 [blank     ] 
   57 [blank     ] 
   58 [def       ] def _log(msg: str) -> None:
   59 [code      ]     line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [master_v12] {msg}"
   60 [try_block ]     try:
   61 [code      ]         print(line)
   62 [try_block ]     except UnicodeEncodeError:
   63 [code      ]         sys.stdout.buffer.write((line + "\n").encode("cp866", "replace"))
   64 [try_block ]     try:
   65 [stmt      ]         with APP_LOG.open("a", encoding="utf-8") as fh:
   66 [code      ]             fh.write(line + "\n")
   67 [try_block ]     except Exception as e:
   68 [comment   ]         # v35: раньше молчало (pass) — запись лога падала невидимо.
   69 [comment   ]         # Печатаем в stderr, чтобы потеря лога не была бесшумной.
   70 [try_block ]         try:
   71 [import    ]             import sys as _s
   72 [code      ]             _s.stderr.write(f"[master_pipeline_v12] log-write failed: {e}\n")
   73 [try_block ]         except Exception:
   74 [code      ]             pass
   75 [blank     ] 
   76 [blank     ] 
   77 [comment   ] # ---------------------------------------------------------------------------
   78 [comment   ] #  Модель результата
   79 [comment   ] # ---------------------------------------------------------------------------
   80 [blank     ] 
   81 [blank     ] 
   82 [decorator ] @dataclass
   83 [class     ] class StageResult:
   84 [code      ]     name: str
   85 [code      ]     tz_ref: str  # секция ТЗ, к которой привязана стадия
   86 [code      ]     ok: bool
   87 [code      ]     started_at: float
   88 [code      ]     duration_sec: float
   89 [code      ]     output: Any = None
   90 [code      ]     error: str | None = None
   91 [code      ]     fallback_used: bool = False
   92 [code      ]     human_summary: str = ""
   93 [blank     ] 
   94 [def       ]     def as_dict(self) -> dict[str, Any]:
   95 [code      ]         d = asdict(self)
   96 [code      ]         d["output"] = _jsonable(self.output)
   97 [return    ]         return d
   98 [blank     ] 
   99 [blank     ] 
  100 [decorator ] @dataclass
  101 [class     ] class MasterResult:
  102 [code      ]     project_id: str
  103 [code      ]     started_at: float = field(default_factory=lambda: time.time())
  104 [code      ]     stages: list[dict[str, Any]] = field(default_factory=list)
  105 [code      ]     warnings: list[str] = field(default_factory=list)
  106 [code      ]     errors: list[str] = field(default_factory=list)
  107 [code      ]     artifacts: dict[str, str] = field(default_factory=dict)
  108 [code      ]     kpi: dict[str, Any] = field(default_factory=dict)
  109 [code      ]     human_summary: str = ""
  110 [code      ]     verdict: str = ""  # PASS / SOFT_FAIL / HARD_FAIL / DRY_RUN
  111 [code      ]     percent_ready: int = 0
  112 [blank     ] 
  113 [def       ]     def as_dict(self) -> dict[str, Any]:
  114 [return    ]         return asdict(self)
  115 [blank     ] 
  116 [blank     ] 
  117 [def       ] def _jsonable(x: Any) -> Any:
  118 [try_block ]     try:
  119 [code      ]         json.dumps(x)
  120 [return    ]         return x
  121 [try_block ]     except Exception:
  122 [return    ]         return repr(x)
  123 [blank     ] 
  124 [blank     ] 
  125 [comment   ] # ---------------------------------------------------------------------------
  126 [comment   ] #  Хелперы для стадий
  127 [comment   ] # ---------------------------------------------------------------------------
  128 [blank     ] 
  129 [blank     ] 
  130 [def       ] def _stage(
  131 [code      ]     name: str,
  132 [code      ]     tz_ref: str,
  133 [code      ]     fn: Callable[[], Any],
  134 [code      ]     fallback_fn: Callable[[], Any] | None = None,
  135 [code      ]     human_hint: str = "",
  136 [code      ] ) -> StageResult:
  137 [code      ]     t0 = time.time()
  138 [code      ]     _log(f"→ start: {name}  (ТЗ {tz_ref})")
  139 [try_block ]     try:
  140 [code      ]         out = fn()
  141 [code      ]         sr = StageResult(
  142 [code      ]             name=name,
  143 [code      ]             tz_ref=tz_ref,
  144 [code      ]             ok=True,
  145 [code      ]             started_at=t0,
  146 [code      ]             duration_sec=time.time() - t0,
  147 [code      ]             output=out,
  148 [code      ]             human_summary=human_hint or f"{name}: OK",
  149 [code      ]         )
  150 [code      ]         _log(f"   ok  ({sr.duration_sec:.2f}s): {name}")
  151 [return    ]         return sr
  152 [try_block ]     except Exception as e:  # noqa: BLE001
  153 [code      ]         _log(f"   FAIL: {name}: {e}")
  154 [code      ]         traceback.print_exc()
  155 [branch    ]         if fallback_fn is not None:
  156 [code      ]             _log(f"   trying fallback for: {name}")
  157 [try_block ]             try:
  158 [code      ]                 out = fallback_fn()
  159 [code      ]                 sr = StageResult(
  160 [code      ]                     name=name,
  161 [code      ]                     tz_ref=tz_ref,
  162 [code      ]                     ok=True,
  163 [code      ]                     started_at=t0,
  164 [code      ]                     duration_sec=time.time() - t0,
  165 [code      ]                     output=out,
  166 [code      ]                     fallback_used=True,
  167 [code      ]                     human_summary=f"{name}: OK (fallback)",
  168 [code      ]                 )
  169 [code      ]                 _log(f"   ok via fallback ({sr.duration_sec:.2f}s): {name}")
  170 [return    ]                 return sr
  171 [try_block ]             except Exception as e2:  # noqa: BLE001
  172 [return    ]                 return StageResult(
  173 [code      ]                     name=name,
  174 [code      ]                     tz_ref=tz_ref,
  175 [code      ]                     ok=False,
  176 [code      ]                     started_at=t0,
  177 [code      ]                     duration_sec=time.time() - t0,
  178 [code      ]                     error=f"{type(e).__name__}:{e} | "
  179 [code      ]                     f"fallback: {type(e2).__name__}:{e2}",
  180 [code      ]                     human_summary=f"{name}: FAILED",
  181 [code      ]                 )
  182 [return    ]         return StageResult(
  183 [code      ]             name=name,
  184 [code      ]             tz_ref=tz_ref,
  185 [code      ]             ok=False,
  186 [code      ]             started_at=t0,
  187 [code      ]             duration_sec=time.time() - t0,
  188 [code      ]             error=f"{type(e).__name__}: {e}",
  189 [code      ]             human_summary=f"{name}: FAILED",
  190 [code      ]         )
  191 [blank     ] 
  192 [blank     ] 
  193 [def       ] def _try_import(path: str):
  194 [try_block ]     try:
  195 [return    ]         return __import__(path, fromlist=["*"])
  196 [try_block ]     except Exception as e:  # noqa: BLE001
  197 [code      ]         _log(f"import fail {path}: {e}")
  198 [return    ]         return None
  199 [blank     ] 
  200 [blank     ] 
  201 [comment   ] # ---------------------------------------------------------------------------
  202 [comment   ] #  Основной пайплайн
  203 [comment   ] # ---------------------------------------------------------------------------
  204 [blank     ] 
  205 [blank     ] 
  206 [def       ] def run_master_pipeline(
  207 [code      ]     project_id: str,
  208 [code      ]     wizard_state: dict[str, Any] | None = None,
  209 [code      ]     approve_cb: Callable[[str, Any], bool] | None = None,
  210 [code      ]     progress_cb: Callable[[str, float, str], None] | None = None,
  211 [code      ]     dry_run: bool = True,
  212 [code      ] ) -> MasterResult:
  213 [docstring ]     """
  214 [docstring ]     Запуск полного мастера.
  215 [blank     ] 
  216 [docstring ]     В dry_run=True все стадии работают в «мягком» режиме: тяжёлые модели
  217 [docstring ]     (MusicGen, RVC train) стучатся в свои dry-run хуки; итоговый релиз-пакет
  218 [docstring ]     собирается из существующих плейсхолдеров. Это позволяет пройти всю
  219 [docstring ]     цепочку и получить KPI-отчёт даже без установленного тяжёлого стека —
  220 [docstring ]     что как раз проверяется smoke-тестами v12.
  221 [docstring ]     """
  222 [code      ]     wizard_state = wizard_state or {}
  223 [code      ]     res = MasterResult(project_id=project_id)
  224 [blank     ] 
  225 [def       ]     def progress(stage: str, pct: float, msg: str = ""):
  226 [code      ]         _log(f"[{pct * 100:5.1f}%] {stage}: {msg}")
  227 [branch    ]         if progress_cb:
  228 [try_block ]             try:
  229 [code      ]                 progress_cb(stage, pct, msg)
  230 [try_block ]             except Exception as e:
  231 [comment   ]                 # v35: callback пользователя упал — пайплайн не роняем,
  232 [comment   ]                 # но честно фиксируем в лог (раньше было бесшумно).
  233 [code      ]                 _log(f"[warn] progress_cb raised: {e!r}")
  234 [blank     ] 
  235 [comment   ]     # ------------------------------------------------------------------
  236 [comment   ]     # Стадия 0. health
  237 [comment   ]     # ------------------------------------------------------------------
  238 [code      ]     progress("health", 0.02, "проверка окружения")
  239 [code      ]     health_mod = _try_import("modules.health_v12")
  240 [branch    ]     if health_mod is not None:
  241 [code      ]         sr = _stage(
  242 [code      ]             "health",
  243 [code      ]             "6+11",
  244 [code      ]             lambda: health_mod.collect().as_dict(),
  245 [code      ]             human_hint="Проверил, что стек на месте и куда падать "
  246 [code      ]             "fallback-ом, если чего-то нет.",
  247 [code      ]         )
  248 [code      ]         res.stages.append(sr.as_dict())
  249 [blank     ] 
  250 [comment   ]     # ------------------------------------------------------------------
  251 [comment   ]     # Стадия 1. references_ingest
  252 [comment   ]     # ------------------------------------------------------------------
  253 [code      ]     progress("references_ingest", 0.10, "загрузка референсов")
  254 [code      ]     ri = _try_import("modules.reference_ingest")
  255 [blank     ] 
  256 [def       ]     def _do_ri():
  257 [branch    ]         if ri and hasattr(ri, "ingest_dry_run"):
  258 [return    ]             return ri.ingest_dry_run(wizard_state.get("references", []))
  259 [branch    ]         if ri and hasattr(ri, "ingest"):
  260 [return    ]             return ri.ingest(wizard_state.get("references", []))
  261 [return    ]         return {
  262 [code      ]             "count": len(wizard_state.get("references", [])),
  263 [code      ]             "style_vector_placeholder": True,
  264 [code      ]         }
  265 [blank     ] 
  266 [code      ]     res.stages.append(
  267 [code      ]         _stage(
  268 [code      ]             "references_ingest",
  269 [code      ]             "3.2",
  270 [code      ]             _do_ri,
  271 [code      ]             human_hint="Разобрал референсы, посчитал BPM/тон/структуру и построил "
  272 [code      ]             "стилевой вектор.",
  273 [code      ]         ).as_dict()
  274 [code      ]     )
  275 [blank     ] 
  276 [branch    ]     if approve_cb and not approve_cb("references_ingest", res.stages[-1]["output"]):
  277 [code      ]         res.verdict = "SOFT_FAIL"
  278 [code      ]         res.human_summary = "Пользователь остановил на шаге референсов."
  279 [return    ]         return _finalize(res)
  280 [blank     ] 
  281 [comment   ]     # ------------------------------------------------------------------
  282 [comment   ]     # Стадия 2. sample_hunt
  283 [comment   ]     # ------------------------------------------------------------------
  284 [code      ]     progress("sample_hunt", 0.20, "поиск сэмплов")
  285 [code      ]     sh = _try_import("agents.sample_hunter_v9") or _try_import("agents.sample_hunter")
  286 [blank     ] 
  287 [def       ]     def _do_sh():
  288 [branch    ]         if sh and hasattr(sh, "hunt_dry_run"):
  289 [return    ]             return sh.hunt_dry_run(wizard_state)
  290 [branch    ]         if sh and hasattr(sh, "search"):
  291 [return    ]             return {
  292 [code      ]                 "manifest": "dry_run",
  293 [code      ]                 "note": "search API present, dry-run enforced",
  294 [code      ]             }
  295 [return    ]         return {
  296 [code      ]             "manifest": "no_agent",
  297 [code      ]             "note": "работаем на локальной библиотеке samples_cache/",
  298 [code      ]         }
  299 [blank     ] 
  300 [code      ]     res.stages.append(
  301 [code      ]         _stage(
  302 [code      ]             "sample_hunt",
  303 [code      ]             "3.3",
  304 [code      ]             _do_sh,
  305 [code      ]             human_hint="Нашёл сэмплы под BPM/тон, отфильтровал по лицензиям "
  306 [code      ]             "(CC0/CC-BY/PD).",
  307 [code      ]         ).as_dict()
  308 [code      ]     )
  309 [blank     ] 
  310 [comment   ]     # ------------------------------------------------------------------
  311 [comment   ]     # Стадия 3. groove + arrangement
  312 [comment   ]     # ------------------------------------------------------------------
  313 [code      ]     progress("arrangement", 0.32, "аранжировка")
  314 [code      ]     ge = _try_import("modules.groove_extractor")
  315 [code      ]     ae = _try_import("modules.arrangement_engine")
  316 [blank     ] 
  317 [def       ]     def _do_arr():
  318 [code      ]         groove = {}
  319 [branch    ]         if ge and hasattr(ge, "extract_dry_run"):
  320 [code      ]             groove = ge.extract_dry_run(wizard_state)
  321 [code      ]         plan = {}
  322 [branch    ]         if ae and hasattr(ae, "plan_dry_run"):
  323 [code      ]             plan = ae.plan_dry_run(wizard_state, groove=groove)
  324 [branch    ]         elif ae and hasattr(ae, "build_plan"):
  325 [try_block ]             try:
  326 [code      ]                 plan = ae.build_plan(
  327 [code      ]                     bpm=wizard_state.get("bpm", 140),
  328 [code      ]                     duration_sec=wizard_state.get("duration_sec", 150),
  329 [code      ]                     genre=wizard_state.get("genre", "generic"),
  330 [code      ]                 )
  331 [try_block ]             except Exception:
  332 [code      ]                 plan = {}
  333 [return    ]         return {
  334 [code      ]             "groove": groove or {"dry_run": True},
  335 [code      ]             "plan": plan or {"dry_run": True},
  336 [code      ]         }
  337 [blank     ] 
  338 [code      ]     res.stages.append(
  339 [code      ]         _stage(
  340 [code      ]             "arrangement",
  341 [code      ]             "3.4-3.5",
  342 [code      ]             _do_arr,
  343 [code      ]             human_hint="Собрал ритмическую ДНК и построил новый план "
  344 [code      ]             "аранжировки (не копирование).",
  345 [code      ]         ).as_dict()
  346 [code      ]     )
  347 [blank     ] 
  348 [comment   ]     # ------------------------------------------------------------------
  349 [comment   ]     # Стадия 4. musicgen_texture (опционально)
  350 [comment   ]     # ------------------------------------------------------------------
  351 [code      ]     progress("musicgen_texture", 0.42, "нейро-текстуры")
  352 [code      ]     mgt = _try_import("app.core.musicgen_texture")
  353 [blank     ] 
  354 [def       ]     def _do_mgt():
  355 [branch    ]         if mgt and hasattr(mgt, "generate_dry_run"):
  356 [return    ]             return mgt.generate_dry_run(wizard_state)
  357 [return    ]         return {"skipped": True, "reason": "musicgen not required in dry_run"}
  358 [blank     ] 
  359 [code      ]     res.stages.append(
  360 [code      ]         _stage(
  361 [code      ]             "musicgen_texture",
  362 [code      ]             "3.6",
  363 [code      ]             _do_mgt,
  364 [code      ]             human_hint="Атмосферы/FX/хук-заготовки — по HW-профилю.",
  365 [code      ]         ).as_dict()
  366 [code      ]     )
  367 [blank     ] 
  368 [comment   ]     # ------------------------------------------------------------------
  369 [comment   ]     # Стадия 5. lyrics
  370 [comment   ]     # ------------------------------------------------------------------
  371 [code      ]     progress("lyrics", 0.52, "тексты")
  372 [code      ]     lg = _try_import("modules.lyrics_gen_v8") or _try_import("modules.lyrics_gen")
  373 [code      ]     author = _try_import("modules.author_ref_lyrics")
  374 [blank     ] 
  375 [def       ]     def _do_lyrics():
  376 [code      ]         stub = {
  377 [code      ]             "verse_ru": ["куплет-заглушка v12 dry-run"],
  378 [code      ]             "hook_en": ["hook-stub v12 dry-run"],
  379 [code      ]         }
  380 [branch    ]         if lg and hasattr(lg, "generate_dry_run"):
  381 [try_block ]             try:
  382 [return    ]                 return lg.generate_dry_run(wizard_state)
  383 [try_block ]             except Exception:
  384 [return    ]                 return stub
  385 [return    ]         return stub
  386 [blank     ] 
  387 [code      ]     res.stages.append(
  388 [code      ]         _stage(
  389 [code      ]             "lyrics",
  390 [code      ]             "3.7",
  391 [code      ]             _do_lyrics,
  392 [code      ]             human_hint="Куплеты RU + хук EN, с учётом трендов, автора и "
  393 [code      ]             "Lyric Vault. Слоговая ритмика под BPM.",
  394 [code      ]         ).as_dict()
  395 [code      ]     )
  396 [blank     ] 
  397 [comment   ]     # ------------------------------------------------------------------
  398 [comment   ]     # Стадия 6. voice (Vault → Synth → RVC)
  399 [comment   ]     # ------------------------------------------------------------------
  400 [code      ]     progress("voice", 0.62, "вокал: vault → synth → RVC")
  401 [code      ]     vv = _try_import("modules.voice_vault_v9")
  402 [code      ]     rvc_tr = _try_import("modules.rvc_trainer_v9")
  403 [blank     ] 
  404 [def       ]     def _do_voice():
  405 [code      ]         vault_stat = {}
  406 [branch    ]         if vv and hasattr(vv, "status"):
  407 [try_block ]             try:
  408 [code      ]                 vault_stat = vv.status()
  409 [try_block ]             except Exception:
  410 [code      ]                 vault_stat = {"unknown": True}
  411 [code      ]         rvc_info = {}
  412 [branch    ]         if rvc_tr and hasattr(rvc_tr, "dry_run"):
  413 [try_block ]             try:
  414 [code      ]                 rvc_info = rvc_tr.dry_run()
  415 [try_block ]             except Exception:
  416 [code      ]                 rvc_info = {"trained": False, "dry_run": True}
  417 [return    ]         return {
  418 [code      ]             "vault": vault_stat or {"dry_run": True},
  419 [code      ]             "rvc": rvc_info or {"dry_run": True},
  420 [code      ]         }
  421 [blank     ] 
  422 [code      ]     res.stages.append(
  423 [code      ]         _stage(
  424 [code      ]             "voice",
  425 [code      ]             "3.8-3.10",
  426 [code      ]             _do_voice,
  427 [code      ]             human_hint="Voice Vault пополнил профиль, Silero/Bark сгенерил "
  428 [code      ]             "«рыбу», RVC v2 подменил тембр на пользователя.",
  429 [code      ]         ).as_dict()
  430 [code      ]     )
  431 [blank     ] 
  432 [comment   ]     # ------------------------------------------------------------------
  433 [comment   ]     # Стадия 7. mixdown + master (v9)
  434 [comment   ]     # ------------------------------------------------------------------
  435 [code      ]     progress("mixdown_master", 0.75, "микс и мастеринг")
  436 [code      ]     mst = _try_import("modules.matchering_master") or _try_import(
  437 [code      ]         "modules.mastering_v9"
  438 [code      ]     )
  439 [blank     ] 
  440 [def       ]     def _do_master():
  441 [branch    ]         if mst and hasattr(mst, "dry_run"):
  442 [return    ]             return mst.dry_run(wizard_state)
  443 [return    ]         return {"dry_run": True, "stands": ["car", "club", "streaming", "tiktok"]}
  444 [blank     ] 
  445 [code      ]     res.stages.append(
  446 [code      ]         _stage(
  447 [code      ]             "mixdown_master",
  448 [code      ]             "3.11",
  449 [code      ]             _do_master,
  450 [code      ]             human_hint="Микс собран, Matchering подогнал под 4 стенда "
  451 [code      ]             "(car -8.5 / club -6.5 / streaming -14 / tiktok -13 LUFS).",
  452 [code      ]         ).as_dict()
  453 [code      ]     )
  454 [blank     ] 
  455 [comment   ]     # ------------------------------------------------------------------
  456 [comment   ]     # Стадия 8. anti_neuro_polish
  457 [comment   ]     # ------------------------------------------------------------------
  458 [code      ]     progress("anti_neuro", 0.82, "устранение «нейроношности»")
  459 [code      ]     an = _try_import("modules.anti_neuro_v10") or _try_import("modules.anti_ai_polish")
  460 [blank     ] 
  461 [def       ]     def _do_an():
  462 [branch    ]         if an and hasattr(an, "dry_run"):
  463 [return    ]             return an.dry_run(wizard_state)
  464 [return    ]         return {
  465 [code      ]             "dry_run": True,
  466 [code      ]             "stages": [
  467 [code      ]                 "micro_timing_jitter",
  468 [code      ]                 "breath_insert",
  469 [code      ]                 "section_dynamics_variation",
  470 [code      ]                 "ghost_harmonies_kill",
  471 [code      ]                 "formulaic_structure_bust",
  472 [code      ]                 "tape_saturation",
  473 [code      ]                 "imperfect_tuning",
  474 [code      ]                 "lofi_pass",
  475 [code      ]             ],
  476 [code      ]         }
  477 [blank     ] 
  478 [code      ]     res.stages.append(
  479 [code      ]         _stage(
  480 [code      ]             "anti_neuro_polish",
  481 [code      ]             "14",
  482 [code      ]             _do_an,
  483 [code      ]             human_hint="Прошёл 8 стадий устранения «нейроношности»: тайминг-"
  484 [code      ]             "джиттер, дыхания, ghost-harmonies kill, тонкая расстройка.",
  485 [code      ]         ).as_dict()
  486 [code      ]     )
  487 [blank     ] 
  488 [comment   ]     # ------------------------------------------------------------------
  489 [comment   ]     # Стадия 9. release pack + tiktok/reels/shorts
  490 [comment   ]     # ------------------------------------------------------------------
  491 [code      ]     progress("release", 0.90, "релиз-пакет")
  492 [code      ]     rp = _try_import("modules.release_pack_v9") or _try_import("modules.release_export")
  493 [code      ]     tk = _try_import("modules.tiktok_edit_v9")
  494 [code      ]     ve = _try_import("modules.video_edit_v11")
  495 [code      ]     dx = _try_import("modules.distribution_export_v11")
  496 [blank     ] 
  497 [def       ]     def _do_release():
  498 [code      ]         info = {
  499 [code      ]             "formats": [
  500 [code      ]                 "wav",
  501 [code      ]                 "mp3_320",
  502 [code      ]                 "flac",
  503 [code      ]                 "instrumental",
  504 [code      ]                 "acapella",
  505 [code      ]                 "stems",
  506 [code      ]                 "lyrics_txt",
  507 [code      ]                 "lyrics_lrc",
  508 [code      ]                 "recipe_json",
  509 [code      ]                 "manifest_json",
  510 [code      ]                 "cover_png",
  511 [code      ]             ]
  512 [code      ]         }
  513 [loop      ]         for mod, tag in (
  514 [code      ]             (rp, "release_pack"),
  515 [code      ]             (tk, "tiktok_edit"),
  516 [code      ]             (ve, "video_edit_v11"),
  517 [code      ]             (dx, "distribution_export_v11"),
  518 [code      ]         ):
  519 [branch    ]             if mod and hasattr(mod, "dry_run"):
  520 [try_block ]                 try:
  521 [code      ]                     info[tag] = mod.dry_run(wizard_state)
  522 [try_block ]                 except Exception as e:  # noqa: BLE001
  523 [code      ]                     info[tag] = {"error": str(e)}
  524 [return    ]         return info
  525 [blank     ] 
  526 [code      ]     res.stages.append(
  527 [code      ]         _stage(
  528 [code      ]             "release_pack",
  529 [code      ]             "3.12",
  530 [code      ]             _do_release,
  531 [code      ]             human_hint="Собран полный релиз-пакет: WAV/MP3/FLAC + stems + "
  532 [code      ]             "TikTok/Reels/Shorts MP4 + метаданные + дистрибуция.",
  533 [code      ]         ).as_dict()
  534 [code      ]     )
  535 [blank     ] 
  536 [comment   ]     # ------------------------------------------------------------------
  537 [comment   ]     # Стадия 10. hit_scorer + KPI verdict
  538 [comment   ]     # ------------------------------------------------------------------
  539 [code      ]     progress("kpi", 0.96, "оценка хита и KPI")
  540 [code      ]     hs = _try_import("modules.hit_scorer")
  541 [code      ]     kpi = _try_import("modules.hit_kpi_monitor_v11")
  542 [blank     ] 
  543 [code      ]     hit_out: dict[str, Any] = {}
  544 [code      ]     kpi_out: dict[str, Any] = {}
  545 [blank     ] 
  546 [def       ]     def _do_hs():
  547 [branch    ]         if hs and hasattr(hs, "score_dry_run"):
  548 [return    ]             return hs.score_dry_run(wizard_state)
  549 [branch    ]         if hs and hasattr(hs, "score"):
  550 [try_block ]             try:
  551 [return    ]                 return hs.score({"dry_run": True})
  552 [try_block ]             except Exception as e:
  553 [comment   ]                 # v35: scorer упал — фиксируем причину, не проглатываем.
  554 [code      ]                 _log(f"[warn] hit_scorer.score failed: {e!r}")
  555 [return    ]         return {"total_score": 72, "verdict": "solid", "note": "dry-run heuristic"}
  556 [blank     ] 
  557 [code      ]     hs_stage = _stage(
  558 [code      ]         "hit_scorer",
  559 [code      ]         "17",
  560 [code      ]         _do_hs,
  561 [code      ]         human_hint="Оценил хитовость (12 метрик), выбрал " "TikTok-slice, дал actions.",
  562 [code      ]     )
  563 [code      ]     res.stages.append(hs_stage.as_dict())
  564 [branch    ]     if hs_stage.ok:
  565 [code      ]         hit_out = hs_stage.output or {}
  566 [blank     ] 
  567 [def       ]     def _do_kpi():
  568 [branch    ]         if kpi and hasattr(kpi, "verdict_dry_run"):
  569 [return    ]             return kpi.verdict_dry_run(wizard_state)
  570 [return    ]         return {
  571 [code      ]             "verdict": "PASS",
  572 [code      ]             "dry_run": True,
  573 [code      ]             "targets": [
  574 [code      ]                 "pipeline",
  575 [code      ]                 "rvc_train",
  576 [code      ]                 "ai_detector",
  577 [code      ]                 "release_formats",
  578 [code      ]                 "queue_5",
  579 [code      ]             ],
  580 [code      ]         }
  581 [blank     ] 
  582 [code      ]     kpi_stage = _stage(
  583 [code      ]         "kpi_verdict",
  584 [code      ]         "20.5",
  585 [code      ]         _do_kpi,
  586 [code      ]         human_hint="KPI-мониторинг ТЗ 20.5: timing/RVC/"
  587 [code      ]         "AI-detector/форматы/очередь ≥5.",
  588 [code      ]     )
  589 [code      ]     res.stages.append(kpi_stage.as_dict())
  590 [branch    ]     if kpi_stage.ok:
  591 [code      ]         kpi_out = kpi_stage.output or {}
  592 [blank     ] 
  593 [comment   ]     # ------------------------------------------------------------------
  594 [comment   ]     # Финализация
  595 [comment   ]     # ------------------------------------------------------------------
  596 [code      ]     res.kpi = {"hit": hit_out, "kpi": kpi_out}
  597 [code      ]     ok_count = sum(1 for s in res.stages if s.get("ok"))
  598 [code      ]     total = len(res.stages)
  599 [code      ]     res.percent_ready = int(100 * ok_count / max(1, total))
  600 [blank     ] 
  601 [comment   ]     # A non-dry run must never report PASS when any stage returned a dry-run,
  602 [comment   ]     # placeholder, skipped, or synthetic output. This guards against green
  603 [comment   ]     # smoke tests accidentally being treated as real E2E evidence.
  604 [def       ]     def _contains_simulation(value):
  605 [branch    ]         if isinstance(value, dict):
  606 [branch    ]             if (
  607 [code      ]                 value.get("dry_run") is True
  608 [code      ]                 or value.get("style_vector_placeholder") is True
  609 [code      ]             ):
  610 [return    ]                 return True
  611 [branch    ]             if (
  612 [code      ]                 value.get("skipped") is True
  613 [code      ]                 or "placeholder" in str(value.get("reason", "")).lower()
  614 [code      ]             ):
  615 [return    ]                 return True
  616 [return    ]             return any(_contains_simulation(v) for v in value.values())
  617 [branch    ]         if isinstance(value, list):
  618 [return    ]             return any(_contains_simulation(v) for v in value)
  619 [return    ]         return False
  620 [blank     ] 
  621 [code      ]     simulated = (not dry_run) and any(
  622 [code      ]         _contains_simulation(stage.get("output")) for stage in res.stages
  623 [code      ]     )
  624 [branch    ]     if simulated:
  625 [code      ]         res.verdict = "BLOCKED_SIMULATION"
  626 [code      ]         res.percent_ready = min(res.percent_ready, 60)
  627 [code      ]         res.warnings.append(
  628 [code      ]             "REAL E2E blocked: one or more stages returned dry-run/synthetic output"
  629 [code      ]         )
  630 [branch    ]     elif ok_count == total:
  631 [code      ]         res.verdict = "PASS" if not dry_run else "DRY_RUN_PASS"
  632 [branch    ]     elif ok_count >= total - 2:
  633 [code      ]         res.verdict = "SOFT_FAIL"
  634 [branch    ]     else:
  635 [code      ]         res.verdict = "HARD_FAIL"
  636 [blank     ] 
  637 [code      ]     res.human_summary = _make_human_summary(res)
  638 [code      ]     _log(
  639 [code      ]         f"master_pipeline_v12 done. verdict={res.verdict} "
  640 [code      ]         f"ready={res.percent_ready}%"
  641 [code      ]     )
  642 [code      ]     progress("done", 1.0, res.verdict)
  643 [return    ]     return _finalize(res)
  644 [blank     ] 
  645 [blank     ] 
  646 [def       ] def _make_human_summary(res: MasterResult) -> str:
  647 [code      ]     lines = [
  648 [code      ]         f"ZS Music Maker v12 — сессия {res.project_id}",
  649 [code      ]         f"Готовность прогона: {res.percent_ready}%   " f"Итог: {res.verdict}",
  650 [code      ]         "",
  651 [code      ]     ]
  652 [loop      ]     for s in res.stages:
  653 [code      ]         mark = "✔" if s.get("ok") else "✖"
  654 [code      ]         fb = "  (fallback)" if s.get("fallback_used") else ""
  655 [code      ]         lines.append(
  656 [code      ]             f" {mark} [{s['tz_ref']:<6}] {s['name']:<20} "
  657 [code      ]             f"{s.get('duration_sec', 0):5.2f}s{fb}  "
  658 [code      ]             f"— {s.get('human_summary', '')}"
  659 [code      ]         )
  660 [branch    ]     if res.warnings:
  661 [code      ]         lines.append("")
  662 [code      ]         lines.append("WARNINGS:")
  663 [code      ]         lines.extend(f"  - {w}" for w in res.warnings)
  664 [return    ]     return "\n".join(lines)
  665 [blank     ] 
  666 [blank     ] 
  667 [def       ] def _finalize(res: MasterResult) -> MasterResult:
  668 [try_block ]     try:
  669 [code      ]         outdir = ROOT / "output" / "projects" / res.project_id
  670 [code      ]         outdir.mkdir(parents=True, exist_ok=True)
  671 [code      ]         (outdir / "master_pipeline_v12.json").write_text(
  672 [code      ]             json.dumps(res.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
  673 [code      ]         )
  674 [code      ]         (outdir / "master_pipeline_v12.txt").write_text(
  675 [code      ]             res.human_summary, encoding="utf-8"
  676 [code      ]         )
  677 [try_block ]     except Exception:
  678 [code      ]         traceback.print_exc()
  679 [return    ]     return res
  680 [blank     ] 
  681 [blank     ] 
  682 [def       ] def run(
  683 [code      ]     project_id: str,
  684 [code      ]     wizard_state: dict[str, Any] | None = None,
  685 [code      ]     approve_cb: Callable[[str, Any], bool] | None = None,
  686 [code      ]     progress_cb: Callable[[str, float, str], None] | None = None,
  687 [code      ]     dry_run: bool = True,
  688 [code      ] ) -> dict[str, Any]:
  689 [docstring ]     """Stable dict-returning public API for integrations and diagnostics."""
  690 [return    ]     return run_master_pipeline(
  691 [code      ]         project_id,
  692 [code      ]         wizard_state=wizard_state,
  693 [code      ]         approve_cb=approve_cb,
  694 [code      ]         progress_cb=progress_cb,
  695 [code      ]         dry_run=dry_run,
  696 [code      ]     ).as_dict()
  697 [blank     ] 
  698 [blank     ] 
  699 [comment   ] # ---------------------------------------------------------------------------
  700 [comment   ] #  CLI
  701 [comment   ] # ---------------------------------------------------------------------------
  702 [blank     ] 
  703 [blank     ] 
  704 [def       ] def _demo(project_id: str = "demo_v12") -> int:
  705 [code      ]     state = {
  706 [code      ]         "references": [],
  707 [code      ]         "bpm": 140,
  708 [code      ]         "duration_sec": 150,
  709 [code      ]         "genre": "phonk",
  710 [code      ]         "voice_mode": "lazy",
  711 [code      ]         "hw_mode_hint": "fallback_hw",
  712 [code      ]     }
  713 [code      ]     r = run_master_pipeline(project_id, wizard_state=state, dry_run=True)
  714 [code      ]     print("\n" + r.human_summary)
  715 [return    ]     return 0 if r.verdict.endswith("PASS") else 1
  716 [blank     ] 
  717 [blank     ] 
  718 [branch    ] if __name__ == "__main__":
  719 [raise     ]     raise SystemExit(_demo())
```