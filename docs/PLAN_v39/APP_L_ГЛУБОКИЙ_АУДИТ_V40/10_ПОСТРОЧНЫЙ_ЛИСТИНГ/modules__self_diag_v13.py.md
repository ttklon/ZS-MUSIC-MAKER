# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/self_diag_v13.py`

**Всего строк:** 333

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 167 | 50.2 |
| blank | 49 | 14.7 |
| branch | 31 | 9.3 |
| docstring | 24 | 7.2 |
| comment | 17 | 5.1 |
| return | 12 | 3.6 |
| def | 10 | 3.0 |
| loop | 10 | 3.0 |
| import | 8 | 2.4 |
| try_block | 4 | 1.2 |
| raise | 1 | 0.3 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v13 — self_diag_v13.py
    3 [docstring ] =====================================
    4 [blank     ] 
    5 [docstring ] Единая CLI-ДИАГНОСТИКА **для пользователя**, который «ничего не понимает
    6 [docstring ] в технологиях» (ТЗ 4 финальное замечание).
    7 [blank     ] 
    8 [docstring ] v12 уже имеет `health_v12` и `kpi_dashboard_v12`. Эти два дают
    9 [docstring ] машиночитаемые JSON. Но пользователь видит консоль. Ему нужны
   10 [docstring ] цветные строки, понятный Action Plan и чтобы не нужно было знать
   11 [docstring ] про pip, json, venv.
   12 [blank     ] 
   13 [docstring ] self_diag_v13 читает:
   14 [docstring ]   · data/health_v12.json
   15 [docstring ]   · data/kpi_dashboard_v12.json
   16 [docstring ]   · data/hw_profile*.json
   17 [docstring ]   · проверяет наличие 6 обязательных папок/файлов
   18 [docstring ]   · проверяет последний smoke-отчёт (v37 FIX: smoke_v12_report.json давно
   19 [docstring ]     не пишется — активные: smoke_v29_report.json / smoke_v26_report.json)
   20 [blank     ] 
   21 [docstring ] И выдаёт:
   22 [docstring ]   · цветную ASCII-таблицу (зелёный/жёлтый/красный);
   23 [docstring ]   · Action Plan: список конкретных «сделай это» строк;
   24 [docstring ]   · сохранение в logs/self_diag_v13.txt для истории.
   25 [blank     ] 
   26 [docstring ] Никаких тяжёлых зависимостей — работает на голом Python 3.8+.
   27 [docstring ] """
   28 [blank     ] 
   29 [import    ] from __future__ import annotations
   30 [blank     ] 
   31 [import    ] import json
   32 [import    ] import os
   33 [import    ] import sys
   34 [import    ] import time
   35 [import    ] from pathlib import Path
   36 [import    ] from typing import Any
   37 [blank     ] 
   38 [code      ] ROOT = Path(__file__).resolve().parents[1]
   39 [code      ] LOGS = ROOT / "logs"
   40 [comment   ] # v22: ленивое создание (не при импорте)
   41 [blank     ] 
   42 [comment   ] # ANSI codes (с деградацией на Windows <10 / non-tty)
   43 [code      ] _USE_ANSI = sys.stdout.isatty() and os.environ.get("TERM", "") != "dumb"
   44 [branch    ] if os.name == "nt" and not _USE_ANSI:
   45 [comment   ]     # Разрешаем enable VT-mode, cmd поддерживает с Win10 Anniversary
   46 [try_block ]     try:
   47 [import    ]         import ctypes
   48 [blank     ] 
   49 [code      ]         kernel32 = ctypes.windll.kernel32
   50 [code      ]         kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
   51 [code      ]         _USE_ANSI = True
   52 [try_block ]     except Exception:
   53 [code      ]         _USE_ANSI = False
   54 [blank     ] 
   55 [blank     ] 
   56 [def       ] def _c(code: str, text: str) -> str:
   57 [return    ]     return f"\x1b[{code}m{text}\x1b[0m" if _USE_ANSI else text
   58 [blank     ] 
   59 [blank     ] 
   60 [code      ] GREEN = lambda t: _c("32", t)
   61 [code      ] RED = lambda t: _c("31;1", t)
   62 [code      ] YELLOW = lambda t: _c("33;1", t)
   63 [code      ] BOLD = lambda t: _c("1", t)
   64 [code      ] CYAN = lambda t: _c("36", t)
   65 [blank     ] 
   66 [blank     ] 
   67 [comment   ] # Обязательные папки/файлы, которые должны быть в любой инсталляции
   68 [code      ] EXPECTED_PATHS: list[tuple[str, str, str]] = [
   69 [code      ]     ("main.py", "OK", "Файл запуска приложения"),
   70 [code      ]     ("modules/reference_ingest.py", "OK", "Multi-references analyzer (ТЗ 3.2)"),
   71 [code      ]     ("modules/arrangement_engine.py", "OK", "Beat constructor / arrangement (ТЗ 3.5)"),
   72 [code      ]     ("modules/rvc_manager.py", "OK", "RVC v2 (ТЗ 3.10)"),
   73 [code      ]     ("modules/release_pack_v9.py", "OK", "Release pack (ТЗ 3.12)"),
   74 [code      ]     ("modules/health_v12.py", "OK", "Health-check v12"),
   75 [code      ]     ("modules/master_pipeline_v12.py", "OK", "Master pipeline v12"),
   76 [code      ]     ("modules/kpi_dashboard_v12.py", "OK", "KPI dashboard v12"),
   77 [code      ]     ("app/core/orchestrator_v12_patch.py", "OK", "Orchestrator v12"),
   78 [code      ]     ("data/", "FLEX", "Локальная БД (создаётся)"),
   79 [code      ]     ("output/", "FLEX", "Артефакты (создаётся)"),
   80 [code      ]     ("voice_vault/", "OK", "Voice Vault (ТЗ 3.8)"),
   81 [code      ]     ("lyric_vault/", "OK", "Lyric Vault (ТЗ 3.7)"),
   82 [code      ]     ("logs/", "FLEX", "Логи (создаётся)"),
   83 [code      ]     ("models/rvc/", "OK", "Папка для голосовых моделей RVC"),
   84 [code      ]     ("models/musicgen_cache/", "FLEX", "Кэш MusicGen (опционально)"),
   85 [code      ]     ("references/", "FLEX", "Пользовательские референсы (опционально)"),
   86 [code      ] ]
   87 [blank     ] 
   88 [blank     ] 
   89 [def       ] def _read_json_silent(p: Path) -> dict[str, Any] | None:
   90 [try_block ]     try:
   91 [return    ]         return json.loads(p.read_text(encoding="utf-8"))
   92 [try_block ]     except Exception:
   93 [return    ]         return None
   94 [blank     ] 
   95 [blank     ] 
   96 [def       ] def check_layout() -> list[dict[str, Any]]:
   97 [docstring ]     """Возвращает список {path, status, message, severity}."""
   98 [code      ]     out: list[dict[str, Any]] = []
   99 [loop      ]     for rel, need, descr in EXPECTED_PATHS:
  100 [code      ]         p = ROOT / rel
  101 [branch    ]         if p.exists():
  102 [branch    ]             if need == "OK":
  103 [code      ]                 out.append(
  104 [code      ]                     {"path": rel, "status": "OK", "message": descr, "severity": "green"}
  105 [code      ]                 )
  106 [branch    ]             else:
  107 [code      ]                 out.append(
  108 [code      ]                     {
  109 [code      ]                         "path": rel,
  110 [code      ]                         "status": "PRESENT",
  111 [code      ]                         "message": descr,
  112 [code      ]                         "severity": "green",
  113 [code      ]                     }
  114 [code      ]                 )
  115 [branch    ]         else:
  116 [branch    ]             if need == "OK":
  117 [code      ]                 out.append(
  118 [code      ]                     {
  119 [code      ]                         "path": rel,
  120 [code      ]                         "status": "MISSING",
  121 [code      ]                         "message": f"❌ {descr} — нужно создать",
  122 [code      ]                         "severity": "red",
  123 [code      ]                     }
  124 [code      ]                 )
  125 [branch    ]             else:
  126 [code      ]                 out.append(
  127 [code      ]                     {
  128 [code      ]                         "path": rel,
  129 [code      ]                         "status": "AUTO",
  130 [code      ]                         "message": f"⚠ {descr} — будет создан при первом запуске",
  131 [code      ]                         "severity": "yellow",
  132 [code      ]                     }
  133 [code      ]                 )
  134 [return    ]     return out
  135 [blank     ] 
  136 [blank     ] 
  137 [def       ] def check_health() -> dict[str, Any] | None:
  138 [return    ]     return _read_json_silent(ROOT / "data" / "health_v12.json")
  139 [blank     ] 
  140 [blank     ] 
  141 [def       ] def check_kpi() -> dict[str, Any] | None:
  142 [return    ]     return _read_json_silent(ROOT / "data" / "kpi_dashboard_v12.json")
  143 [blank     ] 
  144 [blank     ] 
  145 [def       ] def check_smoke_recent() -> dict[str, Any] | None:
  146 [comment   ]     # v33 FIX (P1, SESSION_LOG v31.7): smoke_v12_report.json больше не
  147 [comment   ]     # существует — smoke_v26/v29 теперь пишут собственные отчёты в logs/.
  148 [comment   ]     # Берём самый свежий доступный; старый v12 — только как fallback.
  149 [loop      ]     for name in ("smoke_v29_report.json", "smoke_v26_report.json", "smoke_v12_report.json"):
  150 [code      ]         rep = _read_json_silent(LOGS / name)
  151 [branch    ]         if rep:
  152 [return    ]             return rep
  153 [return    ]     return None
  154 [blank     ] 
  155 [blank     ] 
  156 [def       ] def collect_action_plan(
  157 [code      ]     layout: list[dict[str, Any]],
  158 [code      ]     health: dict[str, Any] | None,
  159 [code      ]     kpi: dict[str, Any] | None,
  160 [code      ]     smoke: dict[str, Any] | None,
  161 [code      ] ) -> list[str]:
  162 [docstring ]     """Краткий список конкретных действий для пользователя."""
  163 [code      ]     plan: list[str] = []
  164 [blank     ] 
  165 [comment   ]     # 1) layout
  166 [code      ]     red_layout = [it for it in layout if it["severity"] == "red"]
  167 [branch    ]     if red_layout:
  168 [code      ]         plan.append(BOLD("🔴 СРОЧНО: восстановить недостающие файлы:"))
  169 [loop      ]         for it in red_layout:
  170 [code      ]             plan.append(f"    ✗ {it['path']}  —  {it['message']}")
  171 [blank     ] 
  172 [code      ]     yellow_layout = [it for it in layout if it["severity"] == "yellow"]
  173 [branch    ]     if yellow_layout:
  174 [code      ]         plan.append("🟡 Эти папки появятся автоматически при первом запуске:")
  175 [loop      ]         for it in yellow_layout:
  176 [code      ]             plan.append(f"    · {it['path']}")
  177 [blank     ] 
  178 [comment   ]     # 2) health
  179 [branch    ]     if health is None:
  180 [code      ]         plan.append(
  181 [code      ]             "🟡 Не запускался health_v12 — рекомендую прогнать "
  182 [code      ]             "`python -m modules.health_v12`"
  183 [code      ]         )
  184 [branch    ]     else:
  185 [code      ]         verdict = health.get("verdict", "?")
  186 [code      ]         adv = health.get("advice", [])
  187 [branch    ]         if verdict == "GREEN":
  188 [code      ]             plan.append("🟢 Стек в порядке (health GREEN) — можно делать трек.")
  189 [branch    ]         elif verdict == "YELLOW":
  190 [code      ]             plan.append("🟡 Стек работает, но без этих модулей качество ниже:")
  191 [loop      ]             for a in (adv or [])[:5]:
  192 [code      ]                 plan.append(f"    · {a}")
  193 [branch    ]         elif verdict == "RED":
  194 [code      ]             plan.append("🔴 Стек сломан (health RED) — сначала поставь:")
  195 [loop      ]             for a in (adv or [])[:5]:
  196 [code      ]                 plan.append(f"    · {a}")
  197 [blank     ] 
  198 [comment   ]     # 3) kpi
  199 [branch    ]     if kpi is None:
  200 [code      ]         plan.append(
  201 [code      ]             "🟡 KPI дашборд ещё не строился — " "`python -m modules.kpi_dashboard_v12`"
  202 [code      ]         )
  203 [branch    ]     else:
  204 [code      ]         verdict = kpi.get("verdict", "?")
  205 [code      ]         pct = kpi.get("percent_tz", 0)
  206 [branch    ]         if verdict == "GREEN" and pct >= 95:
  207 [code      ]             plan.append(f"🟢 Готовность ТЗ {pct}% — отлично, можно релизить.")
  208 [branch    ]         elif verdict == "YELLOW":
  209 [code      ]             plan.append(f"🟡 Готовность ТЗ {pct}% — есть место для роста:")
  210 [loop      ]             for a in (kpi.get("advice", []) or [])[:3]:
  211 [code      ]                 plan.append(f"    · {a}")
  212 [branch    ]         elif verdict == "RED":
  213 [code      ]             plan.append(f"🔴 Готовность ТЗ {pct}% — нужно доработать модули:")
  214 [loop      ]             for a in (kpi.get("advice", []) or [])[:3]:
  215 [code      ]                 plan.append(f"    · {a}")
  216 [blank     ] 
  217 [comment   ]     # 4) smoke
  218 [branch    ]     if smoke is None:
  219 [code      ]         plan.append("🟡 Smoke ещё не гонялся — запусти `python tools/smoke_v26.py` и `python tools/smoke_v29.py`.")
  220 [branch    ]     else:
  221 [code      ]         passed = smoke.get("passed", 0)
  222 [code      ]         failed = smoke.get("failed", 0)
  223 [code      ]         total = smoke.get("total", 0)
  224 [branch    ]         if failed == 0 and total > 0:
  225 [code      ]             plan.append(f"🟢 Smoke {passed}/{total} PASS — стабильно.")
  226 [branch    ]         elif failed > 0:
  227 [code      ]             plan.append(
  228 [code      ]                 f"🔴 Smoke {passed}/{total} PASS, {failed} FAIL — " "нужны исправления."
  229 [code      ]             )
  230 [blank     ] 
  231 [branch    ]     if not plan:
  232 [code      ]         plan.append("🟢 Все системы в порядке. Запускай wizard!")
  233 [return    ]     return plan
  234 [blank     ] 
  235 [blank     ] 
  236 [def       ] def render_report(
  237 [code      ]     layout: list[dict[str, Any]],
  238 [code      ]     health: dict[str, Any] | None,
  239 [code      ]     kpi: dict[str, Any] | None,
  240 [code      ]     smoke: dict[str, Any] | None,
  241 [code      ]     plan: list[str],
  242 [code      ] ) -> str:
  243 [code      ]     lines: list[str] = []
  244 [code      ]     lines.append(BOLD(CYAN("=" * 70)))
  245 [code      ]     lines.append(BOLD(CYAN("  ZS Music Maker v13 — Self-Diagnostic (для человека)")))
  246 [code      ]     lines.append(BOLD(CYAN("=" * 70)))
  247 [blank     ] 
  248 [comment   ]     # 1. Общая сводка
  249 [code      ]     lines.append("")
  250 [code      ]     lines.append(BOLD("Сводка состояния:"))
  251 [code      ]     n_red_layout = sum(1 for it in layout if it["severity"] == "red")
  252 [code      ]     n_yel_layout = sum(1 for it in layout if it["severity"] == "yellow")
  253 [code      ]     n_grn_layout = sum(1 for it in layout if it["severity"] == "green")
  254 [code      ]     health_verdict = (health or {}).get("verdict", "—")
  255 [code      ]     health_pct = (health or {}).get("percent_ready", "—")
  256 [code      ]     kpi_verdict = (kpi or {}).get("verdict", "—")
  257 [code      ]     kpi_pct = (kpi or {}).get("percent_tz", "—")
  258 [code      ]     smoke_str = (
  259 [code      ]         f"{smoke.get('passed','?')}/{smoke.get('total','?')}"
  260 [branch    ]         if smoke
  261 [code      ]         else "не запускался"
  262 [code      ]     )
  263 [code      ]     lines.append(
  264 [code      ]         f"  • layout:     🟢 {n_grn_layout}  🟡 {n_yel_layout}  " f"🔴 {n_red_layout}"
  265 [code      ]     )
  266 [code      ]     lines.append(f"  • health_v12: {health_verdict} ({health_pct}%)")
  267 [code      ]     lines.append(f"  • KPI ТЗ:     {kpi_verdict} ({kpi_pct}%)")
  268 [code      ]     lines.append(f"  • smoke:      {smoke_str}")
  269 [blank     ] 
  270 [comment   ]     # 2. Action Plan
  271 [code      ]     lines.append("")
  272 [code      ]     lines.append(BOLD("Что делать дальше:"))
  273 [loop      ]     for line in plan:
  274 [code      ]         lines.append("  " + line)
  275 [blank     ] 
  276 [comment   ]     # 3. Подробная таблица слоя
  277 [code      ]     lines.append("")
  278 [code      ]     lines.append(BOLD("Структура проекта (раздел за разделом):"))
  279 [code      ]     lines.append(f"  [{'СТАТУС':<11}] {'ПУТЬ':<45} ОПИСАНИЕ")
  280 [loop      ]     for it in layout:
  281 [branch    ]         if it["severity"] == "green":
  282 [code      ]             mark = GREEN("✓ OK")
  283 [branch    ]         elif it["severity"] == "yellow":
  284 [code      ]             mark = YELLOW("~ AUTO")
  285 [branch    ]         else:
  286 [code      ]             mark = RED("✗ MISSING")
  287 [code      ]         lines.append(f"  [{mark:<11}] {it['path']:<45} {it['message']}")
  288 [blank     ] 
  289 [code      ]     lines.append("")
  290 [code      ]     lines.append(BOLD(CYAN("=" * 70)))
  291 [return    ]     return "\n".join(lines)
  292 [blank     ] 
  293 [blank     ] 
  294 [def       ] def run(save_to_log: bool = True) -> dict[str, Any]:
  295 [code      ]     layout = check_layout()
  296 [code      ]     health = check_health()
  297 [code      ]     kpi = check_kpi()
  298 [code      ]     smoke = check_smoke_recent()
  299 [code      ]     plan = collect_action_plan(layout, health, kpi, smoke)
  300 [blank     ] 
  301 [code      ]     report = render_report(layout, health, kpi, smoke, plan)
  302 [code      ]     print(report)
  303 [blank     ] 
  304 [code      ]     out = {
  305 [code      ]         "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
  306 [code      ]         "layout": layout,
  307 [code      ]         "health_present": bool(health),
  308 [code      ]         "kpi_present": bool(kpi),
  309 [code      ]         "smoke_present": bool(smoke),
  310 [code      ]         "action_plan": plan,
  311 [code      ]     }
  312 [blank     ] 
  313 [branch    ]     if save_to_log:
  314 [comment   ]         # v30 FIX (P1): раньше при отсутствии каталога logs/ (свежий clone)
  315 [comment   ]         # write_text падал с FileNotFoundError и main.py --self-diag завершался
  316 [comment   ]         # с "failed: [Errno 2]". Создаём каталог лениво перед записью.
  317 [code      ]         LOGS.mkdir(parents=True, exist_ok=True)
  318 [code      ]         (LOGS / "self_diag_v13.txt").write_text(
  319 [code      ]             report
  320 [code      ]             + "\n\n# JSON snapshot #\n"
  321 [code      ]             + json.dumps(out, ensure_ascii=False, indent=2),
  322 [code      ]             encoding="utf-8",
  323 [code      ]         )
  324 [return    ]     return out
  325 [blank     ] 
  326 [blank     ] 
  327 [def       ] def main_entry() -> int:
  328 [code      ]     run(save_to_log=True)
  329 [return    ]     return 0
  330 [blank     ] 
  331 [blank     ] 
  332 [branch    ] if __name__ == "__main__":
  333 [raise     ]     raise SystemExit(main_entry())
```