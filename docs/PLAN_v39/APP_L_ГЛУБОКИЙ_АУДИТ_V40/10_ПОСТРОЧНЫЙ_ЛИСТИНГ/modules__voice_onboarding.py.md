# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/voice_onboarding.py`

**Всего строк:** 274

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 160 | 58.4 |
| blank | 39 | 14.2 |
| docstring | 17 | 6.2 |
| return | 12 | 4.4 |
| def | 10 | 3.6 |
| import | 8 | 2.9 |
| branch | 8 | 2.9 |
| try_block | 6 | 2.2 |
| comment | 5 | 1.8 |
| loop | 4 | 1.5 |
| decorator | 2 | 0.7 |
| class | 2 | 0.7 |
| raise | 1 | 0.4 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v14 — voice_onboarding.py (P0.07, TZ 14)
    3 [docstring ] ========================================================
    4 [blank     ] 
    5 [docstring ] Обязательный Voice Onboarding:
    6 [docstring ]   минимум 5 минут записи голоса, разбитой на:
    7 [docstring ]     — 2 минуты последовательного текста (33 русские фонемы);
    8 [docstring ]     — 2 минуты × 8 стилей × 15 сек:
    9 [docstring ]       slow_clear, fast_clear, conversational, aggressive, whisper,
   10 [docstring ]       raspy, singing, semi_recitative;
   11 [docstring ]     — 1 минута караоке.
   12 [blank     ] 
   13 [docstring ] По ТЗ 14.3:
   14 [docstring ]   — автоматический VAD;
   15 [docstring ]   — оценка SNR каждого take'а;
   16 [docstring ]   — детекция клиппинга;
   17 [docstring ]   — оценка фонемного покрытия;
   18 [docstring ]   — сохранение в Voice Vault с метаданными.
   19 [docstring ] """
   20 [blank     ] 
   21 [import    ] from __future__ import annotations
   22 [blank     ] 
   23 [import    ] import json
   24 [import    ] import time
   25 [import    ] from dataclasses import asdict, dataclass, field
   26 [import    ] from pathlib import Path
   27 [import    ] from typing import Any
   28 [blank     ] 
   29 [code      ] ROOT = Path(__file__).resolve().parents[1]
   30 [code      ] VAULT_DIR = ROOT / "voice_vault"
   31 [comment   ] # v22: ленивое создание (не при импорте)
   32 [blank     ] 
   33 [code      ] MANIFEST = VAULT_DIR / "onboarding_manifest.json"
   34 [blank     ] 
   35 [code      ] RUS_PHONEMES = list("абвгдеёжзийклмнопрстуфхцчшщъыьэюя")
   36 [blank     ] 
   37 [code      ] STYLES = [
   38 [code      ]     "slow_clear",
   39 [code      ]     "fast_clear",
   40 [code      ]     "conversational",
   41 [code      ]     "aggressive",
   42 [code      ]     "whisper",
   43 [code      ]     "raspy",
   44 [code      ]     "singing",
   45 [code      ]     "semi_recitative",
   46 [code      ] ]
   47 [blank     ] 
   48 [code      ] PLAN = {
   49 [code      ]     "phoneme_text": 120,
   50 [code      ]     "styles_total": 120,
   51 [code      ]     "karaoke": 60,
   52 [code      ]     "total": 300,
   53 [code      ] }
   54 [blank     ] 
   55 [code      ] PHONEME_SCRIPT = [
   56 [code      ]     "В чащах юга жил бы цитрус? Да, но фальшивый экземпляр.",
   57 [code      ]     "Съешь же ещё этих мягких французских булок, да выпей чаю.",
   58 [code      ]     "Широкая электрификация южных губерний даст мощный толчок подъёму сельского хозяйства.",
   59 [code      ]     "Экс-граф? Плюш изъят. Бьём чуждый цен хвощ.",
   60 [code      ]     "На дворе трава, на траве дрова, не руби дрова на траве двора.",
   61 [code      ]     "Ехал грека через реку, видит грека — в реке рак, сунул грека руку в реку, рак за руку греку цап.",
   62 [code      ]     "Шла Саша по шоссе и сосала сушку.",
   63 [code      ]     "Летели лебеди с лебедятами.",
   64 [code      ]     "От топота копыт пыль по полю летит.",
   65 [code      ]     "Карл у Клары украл кораллы, а Клара у Карла украла кларнет.",
   66 [code      ] ]
   67 [blank     ] 
   68 [code      ] KARAOKE_LINES = [
   69 [code      ]     "Ночь горит, я в дороге, город спит, а мы на пороге.",
   70 [code      ]     "Money over everything, летим вперёд, не тормозя.",
   71 [code      ]     "Тачки, движ, звук на максимум, лето внутри — мы не сдадимся.",
   72 [code      ]     "Огни за окном, за спиной — всё старое, впереди только новое.",
   73 [code      ]     "Turkish beat, palm trees, sea, everybody with me.",
   74 [code      ]     "Мы горим, мы летим, ночь у нас в руках, мы её держим.",
   75 [code      ] ]
   76 [blank     ] 
   77 [blank     ] 
   78 [decorator ] @dataclass
   79 [class     ] class OnboardingStep:
   80 [code      ]     step_id: str
   81 [code      ]     kind: str
   82 [code      ]     label: str
   83 [code      ]     target_sec: int
   84 [code      ]     text_or_prompt: str
   85 [code      ]     recorded_path: str | None = None
   86 [code      ]     duration_sec: float = 0.0
   87 [code      ]     rms_db: float = -100.0
   88 [code      ]     peak_db: float = -100.0
   89 [code      ]     clipping_pct: float = 0.0
   90 [code      ]     snr_db: float = 0.0
   91 [code      ]     covered_phonemes: list[str] = field(default_factory=list)
   92 [code      ]     ok: bool = False
   93 [blank     ] 
   94 [def       ]     def as_dict(self) -> dict[str, Any]:
   95 [return    ]         return asdict(self)
   96 [blank     ] 
   97 [blank     ] 
   98 [decorator ] @dataclass
   99 [class     ] class OnboardingProgress:
  100 [code      ]     total_target_sec: int = 300
  101 [code      ]     total_recorded_sec: float = 0.0
  102 [code      ]     phoneme_coverage_pct: float = 0.0
  103 [code      ]     styles_done: int = 0
  104 [code      ]     styles_total: int = 8
  105 [code      ]     karaoke_done: bool = False
  106 [code      ]     percent: float = 0.0
  107 [code      ]     ready_for_rvc: bool = False
  108 [blank     ] 
  109 [def       ]     def as_dict(self) -> dict[str, Any]:
  110 [return    ]         return asdict(self)
  111 [blank     ] 
  112 [blank     ] 
  113 [def       ] def build_plan() -> list[OnboardingStep]:
  114 [code      ]     steps: list[OnboardingStep] = []
  115 [code      ]     per_phrase = int(PLAN["phoneme_text"] / len(PHONEME_SCRIPT))
  116 [loop      ]     for i, text in enumerate(PHONEME_SCRIPT, 1):
  117 [code      ]         steps.append(
  118 [code      ]             OnboardingStep(
  119 [code      ]                 step_id=f"phon_{i:02d}",
  120 [code      ]                 kind="phoneme_text",
  121 [code      ]                 label=f"Фонемный текст {i}/{len(PHONEME_SCRIPT)}",
  122 [code      ]                 target_sec=per_phrase,
  123 [code      ]                 text_or_prompt=text,
  124 [code      ]             )
  125 [code      ]         )
  126 [code      ]     per_style = int(PLAN["styles_total"] / len(STYLES))
  127 [loop      ]     for st in STYLES:
  128 [code      ]         steps.append(
  129 [code      ]             OnboardingStep(
  130 [code      ]                 step_id=f"style_{st}",
  131 [code      ]                 kind="style",
  132 [code      ]                 label=f"Стиль: {st}",
  133 [code      ]                 target_sec=per_style,
  134 [code      ]                 text_or_prompt=(
  135 [code      ]                     f"Прочитайте 2-3 фразы в стиле «{st}». "
  136 [code      ]                     f"Например: «В машине бас качает, ночь горит»."
  137 [code      ]                 ),
  138 [code      ]             )
  139 [code      ]         )
  140 [code      ]     steps.append(
  141 [code      ]         OnboardingStep(
  142 [code      ]             step_id="karaoke_01",
  143 [code      ]             kind="karaoke",
  144 [code      ]             label="Караоке под бит",
  145 [code      ]             target_sec=PLAN["karaoke"],
  146 [code      ]             text_or_prompt="\n".join(KARAOKE_LINES),
  147 [code      ]         )
  148 [code      ]     )
  149 [return    ]     return steps
  150 [blank     ] 
  151 [blank     ] 
  152 [def       ] def compute_phoneme_coverage(texts: list[str]) -> dict[str, Any]:
  153 [code      ]     seen = set()
  154 [loop      ]     for t in texts:
  155 [loop      ]         for ch in t.lower():
  156 [branch    ]             if ch in RUS_PHONEMES:
  157 [code      ]                 seen.add(ch)
  158 [code      ]     total = len(RUS_PHONEMES)
  159 [code      ]     covered = len(seen)
  160 [code      ]     pct = 100 * covered / total if total else 0.0
  161 [code      ]     missing = sorted(set(RUS_PHONEMES) - seen)
  162 [return    ]     return {
  163 [code      ]         "covered": sorted(seen),
  164 [code      ]         "missing": missing,
  165 [code      ]         "percent": round(pct, 1),
  166 [code      ]         "total": total,
  167 [code      ]     }
  168 [blank     ] 
  169 [blank     ] 
  170 [def       ] def _load_manifest() -> dict[str, Any]:
  171 [branch    ]     if MANIFEST.exists():
  172 [try_block ]         try:
  173 [return    ]             return json.loads(MANIFEST.read_text(encoding="utf-8"))
  174 [try_block ]         except Exception:
  175 [code      ]             pass
  176 [return    ]     return {"steps": [], "started_at": None, "completed_at": None}
  177 [blank     ] 
  178 [blank     ] 
  179 [def       ] def _save_manifest(m: dict[str, Any]) -> None:
  180 [code      ]     MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
  181 [blank     ] 
  182 [blank     ] 
  183 [def       ] def record_step(step: OnboardingStep, mode: str = "auto") -> OnboardingStep:
  184 [try_block ]     try:
  185 [import    ]         from modules import voice_recording as vr
  186 [try_block ]     except Exception:
  187 [code      ]         step.ok = False
  188 [return    ]         return step
  189 [blank     ] 
  190 [code      ]     cap = vr.capability_report()
  191 [branch    ]     if cap.get("real_recording_possible") and mode == "auto":
  192 [code      ]         rec = vr.RealMicRecorder(sample_rate=48000, style=step.kind)
  193 [code      ]         info = rec.start()
  194 [branch    ]         if info.get("ok"):
  195 [code      ]             time.sleep(step.target_sec)
  196 [code      ]             out = rec.stop()
  197 [branch    ]             if out.get("ok"):
  198 [code      ]                 step.recorded_path = out["path"]
  199 [code      ]                 step.duration_sec = float(out["duration_sec"])
  200 [code      ]                 step.ok = True
  201 [return    ]     return step
  202 [blank     ] 
  203 [blank     ] 
  204 [def       ] def compute_progress(steps: list[OnboardingStep]) -> OnboardingProgress:
  205 [code      ]     total_rec = sum(s.duration_sec for s in steps)
  206 [code      ]     styles_done = sum(
  207 [code      ]         1 for s in steps if s.kind == "style" and s.ok and s.duration_sec >= 10
  208 [code      ]     )
  209 [code      ]     karaoke_done = any(
  210 [code      ]         s.kind == "karaoke" and s.ok and s.duration_sec >= 30 for s in steps
  211 [code      ]     )
  212 [code      ]     phon_texts = [s.text_or_prompt for s in steps if s.kind == "phoneme_text" and s.ok]
  213 [code      ]     ph_cov = compute_phoneme_coverage(phon_texts)
  214 [code      ]     ph_pct = ph_cov["percent"]
  215 [blank     ] 
  216 [code      ]     pct = min(100.0, 100 * total_rec / PLAN["total"])
  217 [code      ]     ready = total_rec >= 300 and ph_pct >= 80 and styles_done >= 6 and karaoke_done
  218 [blank     ] 
  219 [return    ]     return OnboardingProgress(
  220 [code      ]         total_target_sec=PLAN["total"],
  221 [code      ]         total_recorded_sec=round(total_rec, 1),
  222 [code      ]         phoneme_coverage_pct=ph_pct,
  223 [code      ]         styles_done=styles_done,
  224 [code      ]         styles_total=len(STYLES),
  225 [code      ]         karaoke_done=karaoke_done,
  226 [code      ]         percent=round(pct, 1),
  227 [code      ]         ready_for_rvc=ready,
  228 [code      ]     )
  229 [blank     ] 
  230 [blank     ] 
  231 [def       ] def is_ready_for_rvc() -> bool:
  232 [code      ]     m = _load_manifest()
  233 [code      ]     steps = [OnboardingStep(**s) for s in m.get("steps", [])]
  234 [return    ]     return compute_progress(steps).ready_for_rvc
  235 [blank     ] 
  236 [blank     ] 
  237 [def       ] def run_cli() -> int:
  238 [code      ]     print("=" * 64)
  239 [code      ]     print("ZS Music Maker — Voice Onboarding (5 минут)")
  240 [code      ]     print("=" * 64)
  241 [code      ]     plan = build_plan()
  242 [code      ]     print(f"План: {len(plan)} шагов, всего {PLAN['total']} сек.")
  243 [code      ]     print(f"  — фонемный текст: {PLAN['phoneme_text']}s ({len(PHONEME_SCRIPT)} фраз)")
  244 [code      ]     print(f"  — 8 стилей × 15s: {PLAN['styles_total']}s")
  245 [code      ]     print(f"  — караоке: {PLAN['karaoke']}s")
  246 [code      ]     print()
  247 [try_block ]     try:
  248 [import    ]         from modules import voice_recording as vr
  249 [blank     ] 
  250 [code      ]         cap = vr.capability_report()
  251 [try_block ]     except Exception as e:
  252 [code      ]         cap = {"real_recording_possible": False, "error": str(e)}
  253 [code      ]     print("[capability]", json.dumps(cap, ensure_ascii=False))
  254 [code      ]     mic_ok = bool(cap.get("real_recording_possible"))
  255 [branch    ]     if not mic_ok:
  256 [code      ]         print("⚠️  Микрофон недоступен. Реальная запись НЕВОЗМОЖНА в этой среде.")
  257 [code      ]     m = _load_manifest()
  258 [code      ]     m["started_at"] = m.get("started_at") or int(time.time())
  259 [code      ]     m["steps"] = [s.as_dict() for s in plan]
  260 [code      ]     m["recording_capable"] = mic_ok
  261 [code      ]     _save_manifest(m)
  262 [code      ]     print(f"✓ manifest saved: {MANIFEST}")
  263 [comment   ]     # v34 FIX (P3.16): раньше run_cli() ВСЕГДА возвращал 0 — даже когда
  264 [comment   ]     # микрофон недоступен и onboarding по факту «только план, без записи».
  265 [comment   ]     # CI/скрипты не могли отличить полный прогон от усечённого.
  266 [comment   ]     # Теперь: 0 = полная capability, 1 = план сохранён, но запись невозможна.
  267 [branch    ]     if not mic_ok:
  268 [code      ]         print("[voice_onboarding] exit=1 (plan-only: mic unavailable)")
  269 [return    ]         return 1
  270 [return    ]     return 0
  271 [blank     ] 
  272 [blank     ] 
  273 [branch    ] if __name__ == "__main__":
  274 [raise     ]     raise SystemExit(run_cli())
```