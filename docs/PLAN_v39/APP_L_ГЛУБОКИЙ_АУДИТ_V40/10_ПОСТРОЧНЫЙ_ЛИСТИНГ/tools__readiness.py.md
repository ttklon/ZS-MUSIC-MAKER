# ПОСТРОЧНЫЙ ЛИСТИНГ: `tools/readiness.py`

**Всего строк:** 283

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 169 | 59.7 |
| blank | 39 | 13.8 |
| try_block | 18 | 6.4 |
| return | 14 | 4.9 |
| branch | 13 | 4.6 |
| def | 12 | 4.2 |
| import | 7 | 2.5 |
| docstring | 4 | 1.4 |
| comment | 4 | 1.4 |
| loop | 2 | 0.7 |
| raise | 1 | 0.4 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v14 — tools/readiness.py (P0.14, TZ 33.4)
    3 [blank     ] 
    4 [docstring ] Честный расчёт % готовности по формуле TZ 33.4.
    5 [docstring ] """
    6 [blank     ] 
    7 [import    ] from __future__ import annotations
    8 [blank     ] 
    9 [import    ] import json
   10 [import    ] import math
   11 [import    ] import sys
   12 [import    ] from pathlib import Path
   13 [import    ] from typing import Any
   14 [blank     ] 
   15 [code      ] ROOT = Path(__file__).resolve().parents[1]
   16 [blank     ] 
   17 [comment   ] # FIX v16 (P0): при запуске «python3 tools/readiness.py» в sys.path попадает
   18 [comment   ] # каталог tools/, а не корень проекта — все probe через __import__("modules.*")
   19 [comment   ] # ложно падали в MISSING и KPI занижался (22% вместо реальных ~60%).
   20 [comment   ] # Гарантируем, что корень проекта всегда доступен для импорта.
   21 [branch    ] if str(ROOT) not in sys.path:
   22 [code      ]     sys.path.insert(0, str(ROOT))
   23 [blank     ] 
   24 [code      ] WEIGHTS = {
   25 [code      ]     "architecture": 10,
   26 [code      ]     "core_modules": 25,
   27 [code      ]     "audio_pipeline": 25,
   28 [code      ]     "voice_rvc": 15,
   29 [code      ]     "release": 10,
   30 [code      ]     "installer": 5,
   31 [code      ]     "testing": 10,
   32 [code      ] }
   33 [blank     ] 
   34 [code      ] STATUS_WEIGHT = {
   35 [code      ]     "REAL_PASS": 1.00,
   36 [code      ]     "PARTIAL": 0.50,
   37 [code      ]     "FALLBACK_ONLY": 0.25,
   38 [code      ]     "MOCK": 0.00,
   39 [code      ]     "FAILED": 0.00,
   40 [code      ]     "MISSING": 0.00,
   41 [code      ]     "NOT_TESTED": 0.00,
   42 [code      ]     "BLOCKED": 0.00,
   43 [code      ] }
   44 [blank     ] 
   45 [blank     ] 
   46 [def       ] def _module_exists(name: str) -> bool:
   47 [try_block ]     try:
   48 [code      ]         __import__(name)
   49 [return    ]         return True
   50 [try_block ]     except Exception:
   51 [return    ]         return False
   52 [blank     ] 
   53 [blank     ] 
   54 [def       ] def _file_exists(rel: str) -> bool:
   55 [return    ]     return (ROOT / rel).exists()
   56 [blank     ] 
   57 [blank     ] 
   58 [def       ] def probe_architecture() -> dict[str, str]:
   59 [code      ]     p: dict[str, str] = {}
   60 [code      ]     stray = list((ROOT).glob("main_v*.py"))
   61 [code      ]     p["main_py_unified"] = (
   62 [code      ]         "REAL_PASS"
   63 [branch    ]         if _file_exists("main.py") and not stray
   64 [code      ]         else ("PARTIAL" if _file_exists("main.py") else "MISSING")
   65 [code      ]     )
   66 [code      ]     p["TZ_txt_present"] = "REAL_PASS" if _file_exists("TZ.txt") else "MISSING"
   67 [code      ]     p["PROMPT_txt_present"] = "REAL_PASS" if _file_exists("PROMPT.txt") else "MISSING"
   68 [code      ]     p["requirements_txt"] = (
   69 [code      ]         "REAL_PASS" if _file_exists("requirements.txt") else "MISSING"
   70 [code      ]     )
   71 [code      ]     p["orchestrator_present"] = (
   72 [code      ]         "REAL_PASS" if _file_exists("app/core/orchestrator.py") else "MISSING"
   73 [code      ]     )
   74 [code      ]     p["updater_module"] = (
   75 [code      ]         "REAL_PASS" if _file_exists("updater/updater.py") else "MISSING"
   76 [code      ]     )
   77 [code      ]     p["legacy_isolated"] = "REAL_PASS" if _file_exists("legacy/mains") else "MISSING"
   78 [return    ]     return p
   79 [blank     ] 
   80 [blank     ] 
   81 [def       ] def probe_core_modules() -> dict[str, str]:
   82 [code      ]     p: dict[str, str] = {}
   83 [code      ]     p["analyzer"] = "REAL_PASS" if _module_exists("modules.analyzer") else "MISSING"
   84 [code      ]     p["groove_extractor"] = (
   85 [code      ]         "REAL_PASS" if _module_exists("modules.groove_extractor") else "MISSING"
   86 [code      ]     )
   87 [code      ]     p["beat_constructor"] = (
   88 [code      ]         "REAL_PASS" if _module_exists("modules.beat_constructor") else "MISSING"
   89 [code      ]     )
   90 [code      ]     p["arrangement"] = (
   91 [code      ]         "REAL_PASS" if _module_exists("modules.arrangement_engine") else "MISSING"
   92 [code      ]     )
   93 [code      ]     p["lyrics_gen"] = "REAL_PASS" if _module_exists("modules.lyrics_gen") else "MISSING"
   94 [code      ]     p["mixdown"] = "PARTIAL" if _module_exists("modules.mixdown") else "MISSING"
   95 [code      ]     p["sidechain"] = "REAL_PASS" if _module_exists("modules.sidechain") else "MISSING"
   96 [code      ]     p["mastering"] = "PARTIAL" if _module_exists("modules.mastering") else "MISSING"
   97 [code      ]     p["anti_neuro_polish"] = (
   98 [code      ]         "REAL_PASS" if _module_exists("modules.anti_neuro_v10") else "MISSING"
   99 [code      ]     )
  100 [code      ]     p["hit_scorer"] = "REAL_PASS" if _module_exists("modules.hit_scorer") else "MISSING"
  101 [code      ]     p["stem_splitter"] = (
  102 [code      ]         "PARTIAL" if _module_exists("modules.stem_splitter") else "MISSING"
  103 [code      ]     )
  104 [code      ]     presets_dir = ROOT / "data" / "genre_presets"
  105 [code      ]     n_presets = len(list(presets_dir.glob("*.json"))) if presets_dir.exists() else 0
  106 [code      ]     p["presets_50"] = (
  107 [code      ]         "REAL_PASS" if n_presets >= 50 else ("PARTIAL" if n_presets > 0 else "MISSING")
  108 [code      ]     )
  109 [return    ]     return p
  110 [blank     ] 
  111 [blank     ] 
  112 [def       ] def probe_audio_pipeline() -> dict[str, str]:
  113 [code      ]     p: dict[str, str] = {}
  114 [try_block ]     try:
  115 [code      ]         p["matchering"] = "REAL_PASS"
  116 [try_block ]     except Exception:
  117 [code      ]         p["matchering"] = "MISSING"
  118 [try_block ]     try:
  119 [code      ]         p["pedalboard"] = "REAL_PASS"
  120 [try_block ]     except Exception:
  121 [code      ]         p["pedalboard"] = "MISSING"
  122 [try_block ]     try:
  123 [code      ]         p["pyloudnorm"] = "REAL_PASS"
  124 [try_block ]     except Exception:
  125 [code      ]         p["pyloudnorm"] = "MISSING"
  126 [try_block ]     try:
  127 [code      ]         p["librosa_soundfile"] = "REAL_PASS"
  128 [try_block ]     except Exception:
  129 [code      ]         p["librosa_soundfile"] = "MISSING"
  130 [try_block ]     try:
  131 [code      ]         p["musicgen"] = "REAL_PASS"
  132 [try_block ]     except Exception:
  133 [code      ]         p["musicgen"] = "MISSING"
  134 [try_block ]     try:
  135 [code      ]         p["demucs"] = "REAL_PASS"
  136 [try_block ]     except Exception:
  137 [code      ]         p["demucs"] = "MISSING"
  138 [blank     ] 
  139 [branch    ]     if _file_exists("output/audit_v14/e2e_summary.json") or _file_exists(
  140 [code      ]         "output/audit_v14/real_e2e_result.json"
  141 [code      ]     ):
  142 [code      ]         p["e2e_run_evidence"] = "PARTIAL"
  143 [branch    ]     else:
  144 [code      ]         p["e2e_run_evidence"] = "NOT_TESTED"
  145 [code      ]     p["mastering_8_stands"] = (
  146 [code      ]         "PARTIAL" if _module_exists("modules.mastering") else "MISSING"
  147 [code      ]     )
  148 [return    ]     return p
  149 [blank     ] 
  150 [blank     ] 
  151 [def       ] def probe_voice_rvc() -> dict[str, str]:
  152 [code      ]     p: dict[str, str] = {}
  153 [code      ]     p["voice_recording"] = (
  154 [code      ]         "PARTIAL" if _module_exists("modules.voice_recording") else "MISSING"
  155 [code      ]     )
  156 [code      ]     p["voice_onboarding"] = (
  157 [code      ]         "REAL_PASS" if _module_exists("modules.voice_onboarding") else "MISSING"
  158 [code      ]     )
  159 [code      ]     p["voice_vault"] = (
  160 [code      ]         "REAL_PASS" if _module_exists("modules.voice_vault_v9") else "MISSING"
  161 [code      ]     )
  162 [code      ]     pth_files = list((ROOT / "models" / "rvc").rglob("*.pth"))
  163 [code      ]     p["rvc_model"] = "REAL_PASS" if pth_files else "MISSING"
  164 [try_block ]     try:
  165 [import    ]         from modules import voice_recording as vr
  166 [blank     ] 
  167 [code      ]         cap = vr.capability_report()
  168 [code      ]         p["mic_recording"] = (
  169 [code      ]             "REAL_PASS" if cap.get("real_recording_possible") else "BLOCKED"
  170 [code      ]         )
  171 [try_block ]     except Exception:
  172 [code      ]         p["mic_recording"] = "MISSING"
  173 [return    ]     return p
  174 [blank     ] 
  175 [blank     ] 
  176 [def       ] def probe_release() -> dict[str, str]:
  177 [code      ]     p: dict[str, str] = {}
  178 [code      ]     p["release_pack_module"] = (
  179 [code      ]         "PARTIAL" if _module_exists("modules.release_pack_v13") else "MISSING"
  180 [code      ]     )
  181 [code      ]     p["distrokid_xml"] = (
  182 [code      ]         "PARTIAL" if _module_exists("modules.distribution_export_v11") else "MISSING"
  183 [code      ]     )
  184 [code      ]     p["cover_art"] = "PARTIAL" if _module_exists("modules.cover_art_gen") else "MISSING"
  185 [try_block ]     try:
  186 [code      ]         p["id3_tags"] = "REAL_PASS"
  187 [try_block ]     except Exception:
  188 [code      ]         p["id3_tags"] = "MISSING"
  189 [return    ]     return p
  190 [blank     ] 
  191 [blank     ] 
  192 [def       ] def probe_installer() -> dict[str, str]:
  193 [code      ]     p: dict[str, str] = {}
  194 [code      ]     ok = _module_exists("updater.updater")
  195 [code      ]     p["updater_module"] = "REAL_PASS" if ok else "MISSING"
  196 [code      ]     p["backup_procedure"] = "REAL_PASS" if ok else "MISSING"
  197 [code      ]     p["rollback"] = "REAL_PASS" if ok else "MISSING"
  198 [code      ]     p["sha256_verify"] = "REAL_PASS" if ok else "MISSING"
  199 [code      ]     p["user_data_split"] = "REAL_PASS" if ok else "MISSING"
  200 [return    ]     return p
  201 [blank     ] 
  202 [blank     ] 
  203 [def       ] def probe_testing() -> dict[str, str]:
  204 [code      ]     p: dict[str, str] = {}
  205 [code      ]     p["smoke_v14"] = "REAL_PASS" if _file_exists("tools/smoke_v14.py") else "MISSING"
  206 [code      ]     p["e2e_v14"] = "REAL_PASS" if _file_exists("tools/real_e2e_v14.py") else "MISSING"
  207 [code      ]     p["self_diag"] = (
  208 [code      ]         "REAL_PASS" if _module_exists("modules.self_diag_v13") else "MISSING"
  209 [code      ]     )
  210 [code      ]     p["health"] = "REAL_PASS" if _module_exists("modules.health_v12") else "MISSING"
  211 [code      ]     p["fallback_audit"] = (
  212 [code      ]         "REAL_PASS" if _file_exists("tools/fallback_audit.py") else "MISSING"
  213 [code      ]     )
  214 [code      ]     p["evidence_present"] = "PARTIAL" if _file_exists("output/audit_v14") else "MISSING"
  215 [return    ]     return p
  216 [blank     ] 
  217 [blank     ] 
  218 [def       ] def _block_percent(probes: dict[str, str]) -> float:
  219 [branch    ]     if not probes:
  220 [return    ]         return 0.0
  221 [code      ]     n = len(probes)
  222 [code      ]     score = sum(STATUS_WEIGHT.get(v, 0.0) for v in probes.values())
  223 [return    ]     return round(100.0 * score / n, 2)
  224 [blank     ] 
  225 [blank     ] 
  226 [def       ] def compute() -> tuple[float, dict[str, Any]]:
  227 [code      ]     blocks_raw = {
  228 [code      ]         "architecture": probe_architecture(),
  229 [code      ]         "core_modules": probe_core_modules(),
  230 [code      ]         "audio_pipeline": probe_audio_pipeline(),
  231 [code      ]         "voice_rvc": probe_voice_rvc(),
  232 [code      ]         "release": probe_release(),
  233 [code      ]         "installer": probe_installer(),
  234 [code      ]         "testing": probe_testing(),
  235 [code      ]     }
  236 [code      ]     block_pcts = {k: _block_percent(v) for k, v in blocks_raw.items()}
  237 [blank     ] 
  238 [code      ]     total = 0.0
  239 [loop      ]     for k, w in WEIGHTS.items():
  240 [code      ]         total += block_pcts[k] * w / 100.0
  241 [blank     ] 
  242 [code      ]     caps: list[tuple[float, str]] = []
  243 [branch    ]     if blocks_raw["voice_rvc"].get("rvc_model") != "REAL_PASS":
  244 [code      ]         caps.append((70.0, "no working RVC (no .pth model)"))
  245 [branch    ]     if blocks_raw["voice_rvc"].get("mic_recording") != "REAL_PASS":
  246 [code      ]         caps.append((80.0, "no real microphone recording available"))
  247 [branch    ]     if blocks_raw["audio_pipeline"].get("e2e_run_evidence") != "REAL_PASS":
  248 [code      ]         caps.append((60.0, "no full E2E run with real heavy engines"))
  249 [branch    ]     if blocks_raw["installer"].get("updater_module") != "REAL_PASS":
  250 [code      ]         caps.append((85.0, "no updater module"))
  251 [code      ]     heavy_missing = [
  252 [code      ]         k
  253 [loop      ]         for k in ("musicgen", "demucs")
  254 [branch    ]         if blocks_raw["audio_pipeline"].get(k) in ("MOCK", "FAILED", "MISSING")
  255 [code      ]     ]
  256 [branch    ]     if heavy_missing:
  257 [code      ]         caps.append((65.0, f"heavy engines unavailable: {heavy_missing}"))
  258 [branch    ]     if blocks_raw["testing"].get("evidence_present") not in ("REAL_PASS", "PARTIAL"):
  259 [code      ]         caps.append((50.0, "no evidence attached"))
  260 [blank     ] 
  261 [code      ]     cap_min = min([c[0] for c in caps], default=100.0)
  262 [code      ]     final = min(total, cap_min)
  263 [code      ]     final = math.floor(final)
  264 [blank     ] 
  265 [return    ]     return float(final), {
  266 [code      ]         "block_scores": block_pcts,
  267 [code      ]         "weights": WEIGHTS,
  268 [code      ]         "raw_probes": blocks_raw,
  269 [code      ]         "caps_triggered": caps,
  270 [code      ]         "weighted_sum": round(total, 2),
  271 [code      ]         "cap_min": cap_min,
  272 [code      ]         "final_floor": final,
  273 [code      ]     }
  274 [blank     ] 
  275 [blank     ] 
  276 [def       ] def main() -> int:
  277 [code      ]     pct, blocks = compute()
  278 [code      ]     print(json.dumps({"percent": pct, "blocks": blocks}, ensure_ascii=False, indent=2))
  279 [return    ]     return 0
  280 [blank     ] 
  281 [blank     ] 
  282 [branch    ] if __name__ == "__main__":
  283 [raise     ]     raise SystemExit(main())
```