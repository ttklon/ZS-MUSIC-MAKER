# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/health_v12.py`

**Всего строк:** 381

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 201 | 52.8 |
| blank | 52 | 13.6 |
| comment | 40 | 10.5 |
| docstring | 20 | 5.2 |
| branch | 20 | 5.2 |
| import | 11 | 2.9 |
| return | 10 | 2.6 |
| def | 8 | 2.1 |
| loop | 8 | 2.1 |
| try_block | 6 | 1.6 |
| decorator | 2 | 0.5 |
| class | 2 | 0.5 |
| raise | 1 | 0.3 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v12 «Hit Locked Pro» — health_v12.py
    3 [docstring ] ====================================================
    4 [blank     ] 
    5 [docstring ] Единый health-check всей системы. Запускается ПЕРЕД мастером и перед
    6 [docstring ] release-пайплайном, чтобы:
    7 [blank     ] 
    8 [docstring ] * сообщить пользователю, что реально работает, что деградирует, что упало;
    9 [docstring ] * дать понятные советы «как включить эту фичу»;
   10 [docstring ] * составить машиночитаемый snapshot (`data/health_v12.json`), который потом
   11 [docstring ]   читает KPI-dashboard и оркестратор для маршрутизации fallback-ов.
   12 [blank     ] 
   13 [docstring ] ТЗ-привязка:
   14 [docstring ]   · раздел 6  — «никаких ошибок при установке»;
   15 [docstring ]   · раздел 11 — логирование всего в logs/app.log;
   16 [docstring ]   · раздел 20.1 [RVC/MUSICGEN] — честная диагностика режимов;
   17 [docstring ]   · раздел 20.5 — KPI-контроль требует знать реальное состояние стека.
   18 [blank     ] 
   19 [docstring ] Никаких платных сервисов, никакого сетевого доступа во время health-check —
   20 [docstring ] только импорт локальных модулей и опрос железа через уже установленный
   21 [docstring ] `app.core.hw_autodetect`.
   22 [docstring ] """
   23 [blank     ] 
   24 [import    ] from __future__ import annotations
   25 [blank     ] 
   26 [import    ] import importlib
   27 [import    ] import json
   28 [import    ] import platform
   29 [import    ] import sys
   30 [import    ] import time
   31 [import    ] import traceback
   32 [import    ] from dataclasses import asdict, dataclass, field
   33 [import    ] from pathlib import Path
   34 [import    ] from typing import Any
   35 [blank     ] 
   36 [code      ] ROOT = Path(__file__).resolve().parents[1]
   37 [blank     ] 
   38 [comment   ] # ---------------------------------------------------------------------------
   39 [comment   ] #  1. Регистр проверок
   40 [comment   ] # ---------------------------------------------------------------------------
   41 [comment   ] #
   42 [comment   ] # Каждая запись: (module_path, human_name, requirement_tag).
   43 [comment   ] # requirement_tag:
   44 [comment   ] #   "core"     — без этого приложение не запустится (RED, если нет);
   45 [comment   ] #   "quality"  — без этого качество упадёт, но пайплайн выживет (YELLOW);
   46 [comment   ] #   "optional" — необязательно (GREEN даже при отсутствии).
   47 [comment   ] #
   48 [blank     ] 
   49 [code      ] CHECKS: list[dict[str, str]] = [
   50 [comment   ]     # ---- core ----
   51 [code      ]     {"mod": "numpy", "name": "numpy", "req": "core"},
   52 [code      ]     {"mod": "soundfile", "name": "soundfile", "req": "core"},
   53 [code      ]     {"mod": "scipy", "name": "scipy", "req": "core"},
   54 [comment   ]     # GUI: любое из двух даёт зелёный, оба — идеально
   55 [code      ]     {"mod": "PySide6", "name": "PySide6 (native)", "req": "core_alt", "group": "gui"},
   56 [code      ]     {"mod": "gradio", "name": "Gradio (fallback)", "req": "core_alt", "group": "gui"},
   57 [comment   ]     # ---- quality ----
   58 [code      ]     {"mod": "librosa", "name": "librosa", "req": "quality"},
   59 [code      ]     {"mod": "pydub", "name": "pydub", "req": "quality"},
   60 [code      ]     {"mod": "matchering", "name": "matchering", "req": "quality"},
   61 [code      ]     {"mod": "pyttsx3", "name": "pyttsx3 (TTS fallback)", "req": "quality"},
   62 [code      ]     {"mod": "mutagen", "name": "mutagen (ID3)", "req": "quality"},
   63 [code      ]     {"mod": "PIL", "name": "Pillow", "req": "quality"},
   64 [comment   ]     # ---- optional (heavy) ----
   65 [code      ]     {"mod": "essentia", "name": "essentia", "req": "optional"},
   66 [code      ]     {"mod": "torch", "name": "torch", "req": "optional"},
   67 [code      ]     {"mod": "torch_directml", "name": "torch-directml (AMD)", "req": "optional"},
   68 [code      ]     {"mod": "demucs", "name": "demucs v4", "req": "optional"},
   69 [code      ]     {"mod": "whisper", "name": "openai-whisper", "req": "optional"},
   70 [code      ]     {"mod": "TTS", "name": "Coqui XTTS-v2", "req": "optional"},
   71 [code      ]     {"mod": "bark", "name": "suno-bark", "req": "optional"},
   72 [code      ]     {"mod": "rvc_python", "name": "rvc-python", "req": "optional"},
   73 [code      ] ]
   74 [blank     ] 
   75 [comment   ] # Внутренние модули проекта: должны быть на месте (проверка накопительности).
   76 [code      ] INTERNAL_MODULES: list[str] = [
   77 [comment   ]     # v7-v11 базовые
   78 [code      ]     "modules.analyzer",
   79 [code      ]     "modules.beat_constructor",
   80 [code      ]     "modules.groove_extractor",
   81 [code      ]     "modules.reference_ingest",
   82 [code      ]     "modules.arrangement_engine",
   83 [code      ]     "modules.hit_scorer",
   84 [code      ]     "modules.voice_vault_v9",
   85 [code      ]     "modules.rvc_manager",
   86 [code      ]     "modules.rvc_trainer_v9",
   87 [code      ]     "modules.lyrics_gen_v8",
   88 [code      ]     "modules.author_ref_lyrics",
   89 [code      ]     "modules.mastering_v9",
   90 [code      ]     "modules.matchering_master",
   91 [code      ]     "modules.anti_neuro_v10",
   92 [code      ]     "modules.anti_ai_polish",
   93 [code      ]     "modules.release_pack_v9",
   94 [code      ]     "modules.tiktok_edit_v9",
   95 [code      ]     "modules.hit_kpi_monitor_v11",
   96 [code      ]     "modules.video_edit_v11",
   97 [code      ]     "modules.distribution_export_v11",
   98 [code      ]     "modules.expert_mode_v11",
   99 [code      ]     "app.core.hw_autodetect",
  100 [code      ]     "app.core.orchestrator",
  101 [code      ]     "app.core.orchestrator_v11_patch",
  102 [code      ] ]
  103 [blank     ] 
  104 [blank     ] 
  105 [comment   ] # ---------------------------------------------------------------------------
  106 [comment   ] #  2. Модель отчёта
  107 [comment   ] # ---------------------------------------------------------------------------
  108 [blank     ] 
  109 [blank     ] 
  110 [decorator ] @dataclass
  111 [class     ] class ProbeResult:
  112 [code      ]     key: str
  113 [code      ]     name: str
  114 [code      ]     requirement: str
  115 [code      ]     ok: bool
  116 [code      ]     version: str | None = None
  117 [code      ]     error: str | None = None
  118 [blank     ] 
  119 [def       ]     def as_dict(self) -> dict[str, Any]:
  120 [return    ]         return asdict(self)
  121 [blank     ] 
  122 [blank     ] 
  123 [decorator ] @dataclass
  124 [class     ] class HealthReport:
  125 [code      ]     generated_at: float = field(default_factory=lambda: time.time())
  126 [code      ]     generated_at_human: str = ""
  127 [code      ]     platform: str = ""
  128 [code      ]     python: str = ""
  129 [code      ]     hw_profile: dict[str, Any] = field(default_factory=dict)
  130 [code      ]     externals: list[dict[str, Any]] = field(default_factory=list)
  131 [code      ]     internals: list[dict[str, Any]] = field(default_factory=list)
  132 [code      ]     core_ok: bool = False
  133 [code      ]     quality_ok: bool = False
  134 [code      ]     optional_ok_count: int = 0
  135 [code      ]     optional_total: int = 0
  136 [code      ]     verdict: str = ""  # GREEN / YELLOW / RED
  137 [code      ]     percent_ready: int = 0  # 0..100
  138 [code      ]     advice: list[str] = field(default_factory=list)
  139 [blank     ] 
  140 [def       ]     def as_dict(self) -> dict[str, Any]:
  141 [return    ]         return asdict(self)
  142 [blank     ] 
  143 [blank     ] 
  144 [comment   ] # ---------------------------------------------------------------------------
  145 [comment   ] #  3. Пробы
  146 [comment   ] # ---------------------------------------------------------------------------
  147 [blank     ] 
  148 [blank     ] 
  149 [def       ] def _probe(mod_path: str, name: str, req: str) -> ProbeResult:
  150 [try_block ]     try:
  151 [code      ]         m = importlib.import_module(mod_path)
  152 [code      ]         ver = getattr(m, "__version__", None) or getattr(m, "VERSION", None)
  153 [branch    ]         if ver is None and hasattr(m, "version"):
  154 [code      ]             v = m.version
  155 [code      ]             ver = v if isinstance(v, str) else None
  156 [return    ]         return ProbeResult(mod_path, name, req, True, str(ver) if ver else None)
  157 [try_block ]     except Exception as e:  # noqa: BLE001
  158 [return    ]         return ProbeResult(mod_path, name, req, False, None, f"{type(e).__name__}: {e}")
  159 [blank     ] 
  160 [blank     ] 
  161 [def       ] def _hw_probe() -> dict[str, Any]:
  162 [code      ]     profile: dict[str, Any] = {}
  163 [try_block ]     try:
  164 [import    ]         from app.core import hw_autodetect  # type: ignore
  165 [blank     ] 
  166 [loop      ]         for m in ("detect_hardware", "detect", "probe"):
  167 [branch    ]             if hasattr(hw_autodetect, m):
  168 [code      ]                 p = getattr(hw_autodetect, m)()
  169 [branch    ]                 if isinstance(p, dict):
  170 [code      ]                     profile = p
  171 [code      ]                     break
  172 [try_block ]     except Exception as e:  # noqa: BLE001
  173 [code      ]         profile = {"error": f"{type(e).__name__}: {e}"}
  174 [blank     ] 
  175 [comment   ]     # На всякий случай — минимальный fallback
  176 [branch    ]     if not profile:
  177 [code      ]         profile = {
  178 [code      ]             "cpu": platform.processor() or "unknown",
  179 [code      ]             "os": platform.platform(),
  180 [code      ]             "ram_gb_est": None,
  181 [code      ]             "gpu": "unknown",
  182 [code      ]             "mode": "fallback_hw",
  183 [code      ]         }
  184 [return    ]     return profile
  185 [blank     ] 
  186 [blank     ] 
  187 [comment   ] # ---------------------------------------------------------------------------
  188 [comment   ] #  4. Сборка отчёта
  189 [comment   ] # ---------------------------------------------------------------------------
  190 [blank     ] 
  191 [blank     ] 
  192 [def       ] def _advice_for(probe: ProbeResult) -> str | None:
  193 [docstring ]     """Человеко-понятный совет — что делать, если проба упала."""
  194 [branch    ]     if probe.ok:
  195 [return    ]         return None
  196 [code      ]     hint = {
  197 [code      ]         "PySide6": "GUI не запустится. Установи: pip install PySide6>=6.7",
  198 [code      ]         "gradio": "Экспертный режим (Ctrl+E) не откроется. pip install gradio",
  199 [comment   ]         # v37 FIX: пин <2.0 устарел (v33 снял его из requirements — стек тестируется на numpy 2.x).
  200 [code      ]         "numpy": 'Ядро не поднимется. pip install "numpy>=1.26"',
  201 [code      ]         "soundfile": "Не сможем читать/писать wav. pip install soundfile",
  202 [code      ]         "scipy": "Часть DSP работать не будет. pip install scipy",
  203 [code      ]         "librosa": "Analyzer уйдёт в очень грубый fallback. pip install librosa",
  204 [code      ]         "pydub": "Микс и mp3-экспорт деградируют. pip install pydub + ffmpeg",
  205 [code      ]         "matchering": "Мастеринг под референс отключится. pip install matchering",
  206 [code      ]         "pyttsx3": "Гарантированный TTS-fallback пропадёт. pip install pyttsx3",
  207 [code      ]         "mutagen": "ID3-теги не пропишутся. pip install mutagen",
  208 [code      ]         "PIL": "Обложки не нарисуются. pip install Pillow",
  209 [code      ]         "essentia": "Аналитика упадёт на librosa-only (это ок).",
  210 [code      ]         "torch": "Тяжёлые модели (MusicGen/RVC full) не поднимутся.",
  211 [code      ]         "torch_directml": "AMD-ускорение отключится, будет CPU.",
  212 [code      ]         "demucs": "Стемов из референса не будет — только для анализа.",
  213 [code      ]         "whisper": "Транскрипции текстов референсов не будет.",
  214 [code      ]         "TTS": "XTTS-v2 клонирование недоступно, используем Silero/Bark.",
  215 [code      ]         "bark": "Bark speakers недоступны, используем Silero/pyttsx3.",
  216 [code      ]         "rvc_python": "RVC-инференс уходит в rvc_manager fallback (форки).",
  217 [code      ]     }
  218 [return    ]     return hint.get(probe.key)
  219 [blank     ] 
  220 [blank     ] 
  221 [def       ] def collect(save_to: Path | None = None) -> HealthReport:
  222 [docstring ]     """Собрать полный health-report."""
  223 [code      ]     rep = HealthReport()
  224 [code      ]     rep.generated_at_human = time.strftime(
  225 [code      ]         "%Y-%m-%d %H:%M:%S UTC", time.gmtime(rep.generated_at)
  226 [code      ]     )
  227 [code      ]     rep.platform = platform.platform()
  228 [code      ]     rep.python = sys.version.split()[0]
  229 [code      ]     rep.hw_profile = _hw_probe()
  230 [blank     ] 
  231 [comment   ]     # 4.1 внешние зависимости
  232 [code      ]     gui_group_ok = False
  233 [loop      ]     for entry in CHECKS:
  234 [code      ]         r = _probe(entry["mod"], entry["name"], entry["req"])
  235 [code      ]         rep.externals.append(r.as_dict())
  236 [branch    ]         if entry.get("group") == "gui" and r.ok:
  237 [code      ]             gui_group_ok = True
  238 [blank     ] 
  239 [comment   ]     # 4.2 внутренние
  240 [loop      ]     for mp in INTERNAL_MODULES:
  241 [code      ]         r = _probe(mp, mp, "internal")
  242 [code      ]         rep.internals.append(r.as_dict())
  243 [blank     ] 
  244 [comment   ]     # 4.3 сводка
  245 [code      ]     core_missing = [
  246 [code      ]         e for e in rep.externals if e["requirement"] == "core" and not e["ok"]
  247 [code      ]     ]
  248 [code      ]     quality_missing = [
  249 [code      ]         e for e in rep.externals if e["requirement"] == "quality" and not e["ok"]
  250 [code      ]     ]
  251 [code      ]     optional_ok = [
  252 [code      ]         e for e in rep.externals if e["requirement"] == "optional" and e["ok"]
  253 [code      ]     ]
  254 [code      ]     optional_all = [e for e in rep.externals if e["requirement"] == "optional"]
  255 [blank     ] 
  256 [code      ]     rep.core_ok = (not core_missing) and gui_group_ok
  257 [code      ]     rep.quality_ok = not quality_missing
  258 [code      ]     rep.optional_ok_count = len(optional_ok)
  259 [code      ]     rep.optional_total = len(optional_all)
  260 [blank     ] 
  261 [code      ]     internal_ok = sum(1 for e in rep.internals if e["ok"])
  262 [code      ]     internal_total = max(1, len(rep.internals))
  263 [blank     ] 
  264 [comment   ]     # Взвешенный процент готовности
  265 [code      ]     core_w = 40  # ядро
  266 [code      ]     qual_w = 30  # качество
  267 [code      ]     opt_w = 15  # тяжёлые модели
  268 [code      ]     int_w = 15  # внутренние модули проекта
  269 [blank     ] 
  270 [code      ]     core_score = core_w if rep.core_ok else 0
  271 [code      ]     qual_score = int(
  272 [code      ]         qual_w
  273 [code      ]         * (
  274 [code      ]             1
  275 [code      ]             - len(quality_missing)
  276 [code      ]             / max(1, len([e for e in rep.externals if e["requirement"] == "quality"]))
  277 [code      ]         )
  278 [code      ]     )
  279 [code      ]     opt_score = int(opt_w * rep.optional_ok_count / max(1, rep.optional_total))
  280 [code      ]     int_score = int(int_w * internal_ok / internal_total)
  281 [blank     ] 
  282 [code      ]     rep.percent_ready = core_score + qual_score + opt_score + int_score
  283 [blank     ] 
  284 [branch    ]     if not rep.core_ok:
  285 [code      ]         rep.verdict = "RED"
  286 [branch    ]     elif not rep.quality_ok or rep.percent_ready < 70:
  287 [code      ]         rep.verdict = "YELLOW"
  288 [branch    ]     else:
  289 [code      ]         rep.verdict = "GREEN"
  290 [blank     ] 
  291 [comment   ]     # 4.4 советы
  292 [loop      ]     for e in rep.externals:
  293 [branch    ]         if not e["ok"]:
  294 [comment   ]             # Быстро сконструируем псевдо-ProbeResult для _advice_for
  295 [code      ]             r = ProbeResult(
  296 [code      ]                 e["key"], e["name"], e["requirement"], False, None, e.get("error")
  297 [code      ]             )
  298 [code      ]             adv = _advice_for(r)
  299 [branch    ]             if adv:
  300 [code      ]                 rep.advice.append(f"[{e['requirement'].upper()}] {e['name']}: {adv}")
  301 [loop      ]     for e in rep.internals:
  302 [branch    ]         if not e["ok"]:
  303 [code      ]             rep.advice.append(
  304 [code      ]                 f"[INTERNAL] {e['name']} не импортируется: {e.get('error')}"
  305 [code      ]             )
  306 [blank     ] 
  307 [branch    ]     if save_to is None:
  308 [code      ]         save_to = ROOT / "data" / "health_v12.json"
  309 [try_block ]     try:
  310 [code      ]         save_to.parent.mkdir(parents=True, exist_ok=True)
  311 [code      ]         save_to.write_text(
  312 [code      ]             json.dumps(rep.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
  313 [code      ]         )
  314 [try_block ]     except Exception:  # noqa: BLE001
  315 [code      ]         traceback.print_exc()
  316 [blank     ] 
  317 [return    ]     return rep
  318 [blank     ] 
  319 [blank     ] 
  320 [comment   ] # ---------------------------------------------------------------------------
  321 [comment   ] #  5. CLI
  322 [comment   ] # ---------------------------------------------------------------------------
  323 [blank     ] 
  324 [blank     ] 
  325 [def       ] def _fmt_row(name: str, ok: bool, ver: str | None, req: str) -> str:
  326 [code      ]     mark = "OK " if ok else "MISS"
  327 [code      ]     v = f"v{ver}" if ver else ""
  328 [return    ]     return f"  [{mark}] [{req:<8}] {name} {v}"
  329 [blank     ] 
  330 [blank     ] 
  331 [def       ] def main(argv: list[str] | None = None) -> int:
  332 [code      ]     argv = argv or sys.argv[1:]
  333 [code      ]     rep = collect()
  334 [code      ]     print("=" * 72)
  335 [code      ]     print("ZS Music Maker v12 — Health Check")
  336 [code      ]     print(f"Generated: {rep.generated_at_human}")
  337 [code      ]     print(f"Platform : {rep.platform}   Python: {rep.python}")
  338 [code      ]     print(
  339 [code      ]         f"HW mode  : {rep.hw_profile.get('mode', '?')}   "
  340 [code      ]         f"GPU: {rep.hw_profile.get('gpu', '?')}"
  341 [code      ]     )
  342 [code      ]     print("-" * 72)
  343 [code      ]     print("EXTERNAL DEPENDENCIES:")
  344 [loop      ]     for e in rep.externals:
  345 [code      ]         print(_fmt_row(e["name"], e["ok"], e.get("version"), e["requirement"]))
  346 [code      ]     print("-" * 72)
  347 [code      ]     print("INTERNAL MODULES:")
  348 [loop      ]     for e in rep.internals:
  349 [code      ]         print(_fmt_row(e["name"], e["ok"], None, e["requirement"]))
  350 [code      ]     print("-" * 72)
  351 [code      ]     print(
  352 [code      ]         f"VERDICT: {rep.verdict}  |  READY: {rep.percent_ready}%  |  "
  353 [code      ]         f"core_ok={rep.core_ok} quality_ok={rep.quality_ok}  "
  354 [code      ]         f"optional={rep.optional_ok_count}/{rep.optional_total}"
  355 [code      ]     )
  356 [comment   ]     # v33 FIX (P0-UX, SESSION_LOG v31.2): RED почти всегда означает
  357 [comment   ]     # отсутствие GUI (PySide6/Gradio) или quality-зависимостей, а НЕ
  358 [comment   ]     # сломанное аудио-ядро. Без этого пояснения пользователь читал RED
  359 [comment   ]     # как «продукт не работает», хотя beat→mix→mastering полностью живы.
  360 [branch    ]     if rep.verdict == "RED":
  361 [code      ]         core_missing = [e["name"] for e in rep.externals
  362 [branch    ]                         if e["requirement"] == "core" and not e["ok"]]
  363 [code      ]         gui_missing = [e["name"] for e in rep.externals
  364 [branch    ]                        if e.get("requirement") == "core_alt" and not e["ok"]]
  365 [branch    ]         if core_missing:
  366 [code      ]             print(f"  ! RED причина: отсутствует ЯДРО: {', '.join(core_missing)}")
  367 [branch    ]         elif gui_missing:
  368 [code      ]             print(f"  ! RED причина: нет GUI-бэкенда ({', '.join(gui_missing)}).")
  369 [code      ]             print("    Аудио-ядро (beat/mix/mastering) при этом может быть полностью")
  370 [code      ]             print("    рабочим — проверь `python tools/smoke_v29.py`. Установи GUI:")
  371 [code      ]             print("    `pip install PySide6` или `pip install gradio`.")
  372 [branch    ]     if rep.advice:
  373 [code      ]         print("ADVICE:")
  374 [loop      ]         for a in rep.advice[:20]:
  375 [code      ]             print(f"  - {a}")
  376 [code      ]     print("=" * 72)
  377 [return    ]     return 0 if rep.core_ok else 2
  378 [blank     ] 
  379 [blank     ] 
  380 [branch    ] if __name__ == "__main__":
  381 [raise     ]     raise SystemExit(main())
```