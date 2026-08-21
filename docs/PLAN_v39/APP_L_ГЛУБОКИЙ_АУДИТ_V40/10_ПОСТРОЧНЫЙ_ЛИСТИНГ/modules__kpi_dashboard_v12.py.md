# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/kpi_dashboard_v12.py`

**Всего строк:** 411

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 235 | 57.2 |
| blank | 46 | 11.2 |
| docstring | 36 | 8.8 |
| branch | 18 | 4.4 |
| comment | 17 | 4.1 |
| return | 17 | 4.1 |
| loop | 15 | 3.6 |
| def | 12 | 2.9 |
| import | 6 | 1.5 |
| try_block | 4 | 1.0 |
| decorator | 2 | 0.5 |
| class | 2 | 0.5 |
| raise | 1 | 0.2 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v12 «Hit Locked Pro» — kpi_dashboard_v12.py
    3 [docstring ] ==========================================================
    4 [blank     ] 
    5 [docstring ] Единый KPI-дашборд для пользователя. Читает:
    6 [blank     ] 
    7 [docstring ]   · data/health_v12.json          (снепшот здоровья стека)
    8 [docstring ]   · output/projects/*/master_pipeline_v12.json  (последний прогон мастера)
    9 [docstring ]   · logs/smoke_v29_report.json / logs/smoke_v26_report.json  (последние smoke-результаты; smoke_v12_report.json больше не пишется — v37)
   10 [docstring ]   · output/projects/*/manifest_v11.json (KPI verdict v11)
   11 [blank     ] 
   12 [docstring ] и склеивает в один HUMAN-READABLE отчёт с процентом соответствия ТЗ,
   13 [docstring ] списком «что упало» и «что делать дальше».
   14 [blank     ] 
   15 [docstring ] Никаких внешних зависимостей, никакого сетевого доступа.
   16 [docstring ] """
   17 [blank     ] 
   18 [import    ] from __future__ import annotations
   19 [blank     ] 
   20 [import    ] import json
   21 [import    ] import time
   22 [import    ] from dataclasses import asdict, dataclass, field
   23 [import    ] from pathlib import Path
   24 [import    ] from typing import Any
   25 [blank     ] 
   26 [code      ] ROOT = Path(__file__).resolve().parents[1]
   27 [blank     ] 
   28 [comment   ] # Требования ТЗ, по которым считается процент соответствия (см. раздел 16).
   29 [code      ] TZ_CHECKLIST: list[dict[str, str]] = [
   30 [code      ]     {"key": "modules_12", "tz": "3.1-3.12", "title": "12 модулей архитектуры"},
   31 [code      ]     {"key": "gui_wizard", "tz": "5", "title": "Единое окно, мастер по шагам"},
   32 [code      ]     {"key": "karaoke", "tz": "5", "title": "Караоке-режим для записи"},
   33 [code      ]     {"key": "onboarding", "tz": "5", "title": "Интерактивный Onboarding"},
   34 [code      ]     {"key": "utf8_cp866", "tz": "6", "title": "UTF-8 в коде, CP866 в консоли"},
   35 [code      ]     {"key": "auto_deps", "tz": "6", "title": "Авто-подтяжка зависимостей"},
   36 [code      ]     {"key": "smoke_tests", "tz": "7", "title": "Smoke + E2E тесты"},
   37 [code      ]     {
   38 [code      ]         "key": "readme_context",
   39 [code      ]         "tz": "8+11",
   40 [comment   ]         # v37 FIX: CONTEXT.md никогда не существовал в репо — канонический
   41 [comment   ]         # накопительный журнал это SESSION_LOG.md (см. правило 11 ТЗ).
   42 [code      ]         "title": "README + SESSION_LOG.md накопительно",
   43 [code      ]     },
   44 [code      ]     {"key": "agents_free", "tz": "9", "title": "Бесплатные интернет-агенты"},
   45 [code      ]     {"key": "logging", "tz": "11", "title": "Логирование всего в logs/app.log"},
   46 [code      ]     {"key": "hw_autodetect", "tz": "20.1", "title": "HW autodetect + fallback"},
   47 [code      ]     {"key": "rvc_real", "tz": "20.1[RVC]", "title": "RVC 100% рабочий"},
   48 [code      ]     {"key": "musicgen_full", "tz": "20.1[MG]", "title": "MusicGen полноценный на 12GB"},
   49 [code      ]     {"key": "author_ref", "tz": "20.3", "title": "Автор из референсов / поиск"},
   50 [code      ]     {"key": "female_backing", "tz": "20.3", "title": "Женские бэки"},
   51 [code      ]     {"key": "expert_mode", "tz": "20.3", "title": "Экспертный режим (скрытый ⋯)"},
   52 [code      ]     {
   53 [code      ]         "key": "license_provenance",
   54 [code      ]         "tz": "20.3",
   55 [code      ]         "title": "License / Provenance Manager",
   56 [code      ]     },
   57 [code      ]     {"key": "release_full", "tz": "20.2 п.32", "title": "Полный релиз-пакет"},
   58 [code      ]     {"key": "distribution_5", "tz": "20.2 п.33", "title": "5 платформ дистрибуции"},
   59 [code      ]     {"key": "hit_scorer", "tz": "20.2 п.34", "title": "AI Detector Pro + hit_scorer"},
   60 [code      ]     {"key": "queue_5", "tz": "20.2 п.35А", "title": "Очередь ≥5 треков"},
   61 [code      ]     {"key": "kpi_20_5", "tz": "20.5", "title": "KPI-мониторинг"},
   62 [code      ] ]
   63 [blank     ] 
   64 [blank     ] 
   65 [decorator ] @dataclass
   66 [class     ] class DashboardSection:
   67 [code      ]     title: str
   68 [code      ]     ok: bool
   69 [code      ]     percent: int
   70 [code      ]     lines: list[str] = field(default_factory=list)
   71 [blank     ] 
   72 [blank     ] 
   73 [decorator ] @dataclass
   74 [class     ] class Dashboard:
   75 [code      ]     generated_at: str = ""
   76 [code      ]     percent_tz: int = 0
   77 [code      ]     verdict: str = ""
   78 [code      ]     sections: list[dict[str, Any]] = field(default_factory=list)
   79 [code      ]     checklist: list[dict[str, Any]] = field(default_factory=list)
   80 [code      ]     advice: list[str] = field(default_factory=list)
   81 [blank     ] 
   82 [def       ]     def as_dict(self) -> dict[str, Any]:
   83 [return    ]         return asdict(self)
   84 [blank     ] 
   85 [blank     ] 
   86 [def       ] def _load_json(p: Path) -> dict[str, Any] | None:
   87 [try_block ]     try:
   88 [return    ]         return json.loads(p.read_text(encoding="utf-8"))
   89 [try_block ]     except Exception:
   90 [return    ]         return None
   91 [blank     ] 
   92 [blank     ] 
   93 [def       ] def _newest(pattern: str, base: Path) -> Path | None:
   94 [code      ]     matches = list(base.rglob(pattern))
   95 [branch    ]     if not matches:
   96 [return    ]         return None
   97 [return    ]     return max(matches, key=lambda p: p.stat().st_mtime)
   98 [blank     ] 
   99 [blank     ] 
  100 [def       ] def _health_section(health: dict[str, Any] | None) -> DashboardSection:
  101 [branch    ]     if not health:
  102 [return    ]         return DashboardSection(
  103 [code      ]             "Стек / зависимости",
  104 [code      ]             False,
  105 [code      ]             0,
  106 [code      ]             ["health_v12.json не найден — запусти " "`python -m modules.health_v12`"],
  107 [code      ]         )
  108 [code      ]     percent = int(health.get("percent_ready", 0))
  109 [code      ]     v = health.get("verdict", "?")
  110 [code      ]     lines = [
  111 [code      ]         f"Verdict: {v}   Ready: {percent}%",
  112 [code      ]         f"HW mode: {health.get('hw_profile', {}).get('mode', '?')}   "
  113 [code      ]         f"GPU: {health.get('hw_profile', {}).get('gpu', '?')}",
  114 [code      ]     ]
  115 [code      ]     ok_count = sum(1 for e in health.get("externals", []) if e.get("ok"))
  116 [code      ]     tot = len(health.get("externals", []))
  117 [code      ]     lines.append(f"External deps OK: {ok_count}/{tot}")
  118 [code      ]     ok_int = sum(1 for e in health.get("internals", []) if e.get("ok"))
  119 [code      ]     tot_int = len(health.get("internals", []))
  120 [code      ]     lines.append(f"Internal modules OK: {ok_int}/{tot_int}")
  121 [loop      ]     for a in (health.get("advice") or [])[:8]:
  122 [code      ]         lines.append(f"  ! {a}")
  123 [return    ]     return DashboardSection("Стек / зависимости", v == "GREEN", percent, lines)
  124 [blank     ] 
  125 [blank     ] 
  126 [def       ] def _pipeline_section(pipe: dict[str, Any] | None) -> DashboardSection:
  127 [branch    ]     if not pipe:
  128 [return    ]         return DashboardSection(
  129 [code      ]             "Последний прогон мастера",
  130 [code      ]             False,
  131 [code      ]             0,
  132 [code      ]             [
  133 [code      ]                 "Нет master_pipeline_v12.json — запусти "
  134 [code      ]                 "`python -m modules.master_pipeline_v12`"
  135 [code      ]             ],
  136 [code      ]         )
  137 [code      ]     percent = int(pipe.get("percent_ready", 0))
  138 [code      ]     v = str(pipe.get("verdict", "?"))
  139 [code      ]     lines = [
  140 [code      ]         f"Проект: {pipe.get('project_id', '?')}   " f"Verdict: {v}   Ready: {percent}%"
  141 [code      ]     ]
  142 [loop      ]     for s in pipe.get("stages", [])[:20]:
  143 [code      ]         mark = "OK " if s.get("ok") else "FAIL"
  144 [code      ]         fb = " (fallback)" if s.get("fallback_used") else ""
  145 [code      ]         lines.append(
  146 [code      ]             f"  [{mark}] {s.get('tz_ref', '?'):<6} "
  147 [code      ]             f"{s.get('name', '?'):<22} "
  148 [code      ]             f"{s.get('duration_sec', 0):5.2f}s{fb}"
  149 [code      ]         )
  150 [return    ]     return DashboardSection(
  151 [code      ]         "Последний прогон мастера", v.endswith("PASS"), percent, lines
  152 [code      ]     )
  153 [blank     ] 
  154 [blank     ] 
  155 [def       ] def _smoke_section(smoke: dict[str, Any] | None) -> DashboardSection:
  156 [branch    ]     if not smoke:
  157 [return    ]         return DashboardSection(
  158 [code      ]             "Smoke-тесты",
  159 [code      ]             False,
  160 [code      ]             0,
  161 [comment   ]             # v33 FIX: указываем реальные скрипты, а не удалённый smoke_v12.
  162 [code      ]             ["Нет свежего smoke-отчёта — запусти `python tools/smoke_v26.py` "
  163 [code      ]              "и `python tools/smoke_v29.py`"],
  164 [code      ]         )
  165 [code      ]     passed = int(smoke.get("passed", 0))
  166 [code      ]     failed = int(smoke.get("failed", 0))
  167 [code      ]     total = passed + failed
  168 [code      ]     pct = int(100 * passed / max(1, total))
  169 [code      ]     lines = [f"PASS: {passed} / {total}   FAIL: {failed}"]
  170 [loop      ]     for name, ok in list(smoke.get("cases", {}).items())[:30]:
  171 [code      ]         lines.append(f"  [{'OK  ' if ok else 'FAIL'}] {name}")
  172 [comment   ]     # v33: название секции из отчёта, без жёсткой привязки к версии.
  173 [code      ]     label = smoke.get("name", "smoke")
  174 [return    ]     return DashboardSection(f"Smoke-тесты ({label})", failed == 0, pct, lines)
  175 [blank     ] 
  176 [blank     ] 
  177 [def       ] def _tz_percent(
  178 [code      ]     health: dict[str, Any] | None,
  179 [code      ]     pipe: dict[str, Any] | None,
  180 [code      ]     smoke: dict[str, Any] | None,
  181 [code      ] ) -> (int, list[dict[str, Any]], list[str]):
  182 [docstring ]     """Оценка соответствия ТЗ по чеклисту раздела 16 + разделу 20.
  183 [blank     ] 
  184 [docstring ]     Логика:
  185 [docstring ]     * modules_12          — есть все 12 модулей → OK по итогам health.internals.
  186 [docstring ]     * gui_wizard          — PySide6 доступен (health) ИЛИ Gradio.
  187 [docstring ]     * karaoke/onboarding  — файлы modules/karaoke_engine.py, onboarding_tour.py.
  188 [docstring ]     * utf8_cp866          — жёстко true (реализовано в main_v11/main_v12).
  189 [docstring ]     * auto_deps           — есть install.py + requirements.txt (windows_build.bat не существует).
  190 [docstring ]     * smoke_tests         — tools/smoke_v26.py и tools/smoke_v29.py (smoke_v12 давно удалён).
  191 [docstring ]     * readme_context      — README.md + SESSION_LOG.md (CONTEXT.md не существует).
  192 [docstring ]     * agents_free         — есть agents/sample_hunter*/trend_scout*.
  193 [docstring ]     * logging             — есть logs/app.log.
  194 [docstring ]     * hw_autodetect       — есть app/core/hw_autodetect.py.
  195 [docstring ]     * rvc_real            — есть modules/rvc_manager.py + rvc_trainer_v9.py.
  196 [docstring ]     * musicgen_full       — есть app/core/musicgen_texture.py + hw_directml.
  197 [docstring ]     * author_ref          — есть modules/author_ref_lyrics.py.
  198 [docstring ]     * female_backing      — есть modules/female_backing.py.
  199 [docstring ]     * expert_mode         — есть modules/expert_mode_v11.py.
  200 [docstring ]     * license_provenance  — есть modules/provenance.py + app/core/license_manager.py.
  201 [docstring ]     * release_full        — есть modules/release_pack_v9.py.
  202 [docstring ]     * distribution_5      — есть modules/distribution_export_v11.py.
  203 [docstring ]     * hit_scorer          — есть modules/hit_scorer.py + ai_detector_pro.py.
  204 [docstring ]     * queue_5             — есть modules/render_queue.py.
  205 [docstring ]     * kpi_20_5            — есть modules/hit_kpi_monitor_v11.py.
  206 [docstring ]     """
  207 [blank     ] 
  208 [def       ]     def has(p: str) -> bool:
  209 [return    ]         return (ROOT / p).exists()
  210 [blank     ] 
  211 [code      ]     checks = {
  212 [code      ]         "modules_12": all(
  213 [code      ]             has(f"modules/{m}.py")
  214 [loop      ]             for m in [
  215 [code      ]                 "analyzer",
  216 [code      ]                 "beat_constructor",
  217 [code      ]                 "groove_extractor",
  218 [code      ]                 "arrangement_engine",
  219 [code      ]                 "voice_synth",
  220 [code      ]                 "voice_convert",
  221 [code      ]                 "voice_vault_v9",
  222 [code      ]                 "rvc_manager",
  223 [code      ]                 "mixdown",
  224 [code      ]                 "matchering_master",
  225 [code      ]                 "release_pack_v9",
  226 [code      ]                 "lyric_vault_v10",
  227 [code      ]                 "author_ref_lyrics",
  228 [code      ]             ]
  229 [code      ]         ),
  230 [code      ]         "gui_wizard": has("app/gui/wizard.py"),
  231 [code      ]         "karaoke": has("modules/karaoke_engine.py") and has("ui/karaoke_recorder.py"),
  232 [code      ]         "onboarding": has("modules/onboarding_tour.py") or has("app/gui/onboarding.py"),
  233 [code      ]         "utf8_cp866": True,
  234 [comment   ]         # v33 FIX: windows_build.bat НЕ существовал — критерий всегда
  235 [comment   ]         # полагался на requirements.txt. Убрана ссылка на несуществующий файл.
  236 [code      ]         "auto_deps": has("install.py") and has("requirements.txt"),
  237 [comment   ]         # v33 FIX (P1, SESSION_LOG v31.7): smoke_v11.py давно удалён,
  238 [comment   ]         # активные smoke — tools/smoke_v26.py и tools/smoke_v29.py.
  239 [code      ]         "smoke_tests": has("tools/smoke_v26.py") and has("tools/smoke_v29.py"),
  240 [comment   ]         # v33 FIX: CONTEXT.md физически отсутствует в репо — роль
  241 [comment   ]         # канонического журнала выполняет SESSION_LOG.md.
  242 [code      ]         "readme_context": has("README.md") and has("SESSION_LOG.md"),
  243 [code      ]         "agents_free": has("agents/sample_hunter_v9.py")
  244 [code      ]         or has("agents/sample_hunter.py"),
  245 [code      ]         "logging": (ROOT / "logs").exists(),
  246 [code      ]         "hw_autodetect": has("app/core/hw_autodetect.py"),
  247 [code      ]         "rvc_real": has("modules/rvc_manager.py") and has("modules/rvc_trainer_v9.py"),
  248 [code      ]         "musicgen_full": has("app/core/musicgen_texture.py"),
  249 [code      ]         "author_ref": has("modules/author_ref_lyrics.py"),
  250 [code      ]         "female_backing": has("modules/female_backing.py"),
  251 [code      ]         "expert_mode": has("modules/expert_mode_v11.py"),
  252 [code      ]         "license_provenance": has("modules/provenance.py")
  253 [code      ]         and has("app/core/license_manager.py"),
  254 [code      ]         "release_full": has("modules/release_pack_v9.py"),
  255 [code      ]         "distribution_5": has("modules/distribution_export_v11.py"),
  256 [code      ]         "hit_scorer": has("modules/hit_scorer.py")
  257 [code      ]         and has("modules/ai_detector_pro.py"),
  258 [code      ]         "queue_5": has("modules/render_queue.py"),
  259 [code      ]         "kpi_20_5": has("modules/hit_kpi_monitor_v11.py"),
  260 [code      ]     }
  261 [blank     ] 
  262 [comment   ]     # Небольшая корректировка по health-report:
  263 [branch    ]     if health is not None:
  264 [code      ]         int_ok = {e.get("name"): e.get("ok") for e in health.get("internals", [])}
  265 [comment   ]         # Если internal-модуль не импортируется — снимаем соответствующий флаг
  266 [branch    ]         if not int_ok.get("modules.rvc_manager", True) or not int_ok.get(
  267 [code      ]             "modules.rvc_trainer_v9", True
  268 [code      ]         ):
  269 [code      ]             checks["rvc_real"] = False
  270 [branch    ]         if not int_ok.get("app.core.musicgen_texture", True):
  271 [code      ]             checks["musicgen_full"] = False
  272 [branch    ]         if not int_ok.get("modules.hit_kpi_monitor_v11", True):
  273 [code      ]             checks["kpi_20_5"] = False
  274 [blank     ] 
  275 [code      ]     entries = []
  276 [code      ]     passed = 0
  277 [loop      ]     for item in TZ_CHECKLIST:
  278 [code      ]         ok = bool(checks.get(item["key"], False))
  279 [code      ]         entries.append(
  280 [code      ]             {"key": item["key"], "tz": item["tz"], "title": item["title"], "ok": ok}
  281 [code      ]         )
  282 [branch    ]         if ok:
  283 [code      ]             passed += 1
  284 [code      ]     percent = int(100 * passed / max(1, len(TZ_CHECKLIST)))
  285 [blank     ] 
  286 [comment   ]     # Советы по проваленным пунктам
  287 [code      ]     advice: list[str] = []
  288 [loop      ]     for e in entries:
  289 [branch    ]         if not e["ok"]:
  290 [code      ]             advice.append(
  291 [code      ]                 f"[TZ {e['tz']}] {e['title']} — не подтверждено, "
  292 [code      ]                 f"проверь наличие соответствующего файла/модуля."
  293 [code      ]             )
  294 [return    ]     return percent, entries, advice
  295 [blank     ] 
  296 [blank     ] 
  297 [def       ] def build(save: bool = True) -> Dashboard:
  298 [code      ]     health = _load_json(ROOT / "data" / "health_v12.json")
  299 [code      ]     pipe_path = _newest("master_pipeline_v12.json", ROOT / "output")
  300 [code      ]     pipe = _load_json(pipe_path) if pipe_path else None
  301 [comment   ]     # v33 FIX: smoke_v12_report.json больше не пишется. Берём самый свежий
  302 [comment   ]     # из актуальных отчётов (smoke_v26 / smoke_v29); fallback — старый v12.
  303 [code      ]     smoke = None
  304 [loop      ]     for cand in (
  305 [code      ]         ROOT / "logs" / "smoke_v29_report.json",
  306 [code      ]         ROOT / "logs" / "smoke_v26_report.json",
  307 [code      ]         ROOT / "logs" / "smoke_v12_report.json",
  308 [code      ]     ):
  309 [code      ]         smoke = _load_json(cand)
  310 [branch    ]         if smoke:
  311 [code      ]             break
  312 [blank     ] 
  313 [code      ]     dash = Dashboard()
  314 [code      ]     dash.generated_at = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
  315 [blank     ] 
  316 [code      ]     s1 = _health_section(health)
  317 [code      ]     s2 = _pipeline_section(pipe)
  318 [code      ]     s3 = _smoke_section(smoke)
  319 [code      ]     dash.sections = [asdict(s1), asdict(s2), asdict(s3)]
  320 [blank     ] 
  321 [code      ]     tz_pct, entries, advice = _tz_percent(health, pipe, smoke)
  322 [code      ]     dash.checklist = entries
  323 [code      ]     dash.advice = advice
  324 [code      ]     dash.percent_tz = tz_pct
  325 [blank     ] 
  326 [comment   ]     # Общий вердикт
  327 [branch    ]     if s1.ok and s2.ok and s3.ok and tz_pct >= 90:
  328 [code      ]         dash.verdict = "GREEN"
  329 [branch    ]     elif tz_pct >= 70:
  330 [code      ]         dash.verdict = "YELLOW"
  331 [branch    ]     else:
  332 [code      ]         dash.verdict = "RED"
  333 [blank     ] 
  334 [branch    ]     if save:
  335 [try_block ]         try:
  336 [code      ]             outdir = ROOT / "data"
  337 [code      ]             outdir.mkdir(exist_ok=True)
  338 [code      ]             (outdir / "kpi_dashboard_v12.json").write_text(
  339 [code      ]                 json.dumps(dash.as_dict(), ensure_ascii=False, indent=2),
  340 [code      ]                 encoding="utf-8",
  341 [code      ]             )
  342 [code      ]             (ROOT / "docs").mkdir(exist_ok=True)
  343 [code      ]             (ROOT / "docs" / "KPI_DASHBOARD_v12.md").write_text(
  344 [code      ]                 render_markdown(dash), encoding="utf-8"
  345 [code      ]             )
  346 [try_block ]         except Exception:
  347 [code      ]             pass
  348 [return    ]     return dash
  349 [blank     ] 
  350 [blank     ] 
  351 [def       ] def render_markdown(dash: Dashboard) -> str:
  352 [code      ]     lines = [
  353 [code      ]         "# KPI Dashboard v12 «Hit Locked Pro»",
  354 [code      ]         "",
  355 [code      ]         f"_Generated: {dash.generated_at}_",
  356 [code      ]         "",
  357 [code      ]         f"**Соответствие ТЗ: {dash.percent_tz}%**   |   "
  358 [code      ]         f"**Общий вердикт: {dash.verdict}**",
  359 [code      ]         "",
  360 [code      ]     ]
  361 [loop      ]     for s in dash.sections:
  362 [code      ]         badge = "🟢" if s["ok"] else "🔴"
  363 [code      ]         lines += [f"## {badge} {s['title']} — {s['percent']}%", ""]
  364 [loop      ]         for ln in s.get("lines", []):
  365 [code      ]             lines.append(f"    {ln}")
  366 [code      ]         lines.append("")
  367 [code      ]     lines += ["## Чеклист ТЗ (раздел 16 + 20)", ""]
  368 [code      ]     lines += ["| # | ТЗ | Пункт | Статус |", "|---|----|-------|--------|"]
  369 [loop      ]     for i, c in enumerate(dash.checklist, 1):
  370 [code      ]         lines.append(
  371 [code      ]             f"| {i} | {c['tz']} | {c['title']} | " f"{'✅' if c['ok'] else '❌'} |"
  372 [code      ]         )
  373 [branch    ]     if dash.advice:
  374 [code      ]         lines += ["", "## Что не подтверждено / рекомендации", ""]
  375 [loop      ]         for a in dash.advice:
  376 [code      ]             lines.append(f"- {a}")
  377 [return    ]     return "\n".join(lines) + "\n"
  378 [blank     ] 
  379 [blank     ] 
  380 [def       ] def render_text(dash: Dashboard) -> str:
  381 [code      ]     out = [
  382 [code      ]         "=" * 72,
  383 [code      ]         f"KPI DASHBOARD v12 — {dash.generated_at}",
  384 [code      ]         f"Соответствие ТЗ: {dash.percent_tz}%   Verdict: {dash.verdict}",
  385 [code      ]         "-" * 72,
  386 [code      ]     ]
  387 [loop      ]     for s in dash.sections:
  388 [code      ]         out.append(f"[{'OK' if s['ok'] else 'X '}] {s['title']} " f"({s['percent']}%)")
  389 [loop      ]         for ln in s.get("lines", []):
  390 [code      ]             out.append(f"    {ln}")
  391 [code      ]     out.append("-" * 72)
  392 [code      ]     out.append("TZ CHECKLIST:")
  393 [loop      ]     for c in dash.checklist:
  394 [code      ]         out.append(f"  [{'V' if c['ok'] else ' '}] {c['tz']:<10} " f"{c['title']}")
  395 [branch    ]     if dash.advice:
  396 [code      ]         out.append("-" * 72)
  397 [code      ]         out.append("ADVICE:")
  398 [loop      ]         for a in dash.advice[:15]:
  399 [code      ]             out.append(f"  - {a}")
  400 [code      ]     out.append("=" * 72)
  401 [return    ]     return "\n".join(out)
  402 [blank     ] 
  403 [blank     ] 
  404 [def       ] def main() -> int:
  405 [code      ]     dash = build()
  406 [code      ]     print(render_text(dash))
  407 [return    ]     return 0 if dash.verdict == "GREEN" else (1 if dash.verdict == "YELLOW" else 2)
  408 [blank     ] 
  409 [blank     ] 
  410 [branch    ] if __name__ == "__main__":
  411 [raise     ]     raise SystemExit(main())
```