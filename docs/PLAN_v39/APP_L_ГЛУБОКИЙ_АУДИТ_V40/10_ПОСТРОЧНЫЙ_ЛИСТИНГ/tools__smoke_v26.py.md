# ПОСТРОЧНЫЙ ЛИСТИНГ: `tools/smoke_v26.py`

**Всего строк:** 217

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 114 | 52.5 |
| blank | 30 | 13.8 |
| docstring | 19 | 8.8 |
| branch | 17 | 7.8 |
| import | 11 | 5.1 |
| def | 6 | 2.8 |
| comment | 6 | 2.8 |
| return | 5 | 2.3 |
| loop | 4 | 1.8 |
| try_block | 4 | 1.8 |
| raise | 1 | 0.5 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker — smoke_v26
    3 [docstring ] ====================================================================
    4 [docstring ] Проверяет пакет фиксов v26 (P0/P1) — качество финального аудио:
    5 [blank     ] 
    6 [docstring ]   1. v26.beat_stereo             — beat_constructor пишет СТЕРЕО (было моно
    7 [docstring ]                                    → весь мастер corr=1.0). Проверяем
    8 [docstring ]                                    shape=(N,2) и corr ∈ [0.3, 0.98].
    9 [docstring ]   2. v26.master_stereo_preserved — master_streaming.wav сохраняет стерео.
   10 [docstring ]   3. v26.master_loudness_target  — master в target -13.5 dBFS ±1.5.
   11 [docstring ]   4. v26.beat_drop_fade          — есть fade ≥100мс перед первым hook
   12 [docstring ]                                    (реальный drop, не плаво).
   13 [docstring ]   5. v26.hit_score_improved      — итоговый hit_score ≥55 (был 50.28 на v25).
   14 [docstring ]   6. v26.hook_repeat_fallback    — hook_repeatability даёт raw ≥ 1 на
   15 [docstring ]                                    коротком ритмичном сигнале.
   16 [docstring ] Запуск:  python3 tools/smoke_v26.py
   17 [docstring ] """
   18 [blank     ] 
   19 [import    ] from __future__ import annotations
   20 [blank     ] 
   21 [import    ] import shutil
   22 [import    ] import sys
   23 [import    ] from pathlib import Path
   24 [blank     ] 
   25 [import    ] import numpy as np
   26 [import    ] import soundfile as sf
   27 [blank     ] 
   28 [code      ] ROOT = Path(__file__).resolve().parents[1]
   29 [code      ] sys.path.insert(0, str(ROOT))
   30 [code      ] RESULTS = []
   31 [blank     ] 
   32 [blank     ] 
   33 [def       ] def check(name, ok, detail=""):
   34 [code      ]     RESULTS.append((name, bool(ok), detail))
   35 [code      ]     print(f"[{'PASS' if ok else 'FAIL'}] {name:38s} {detail}")
   36 [blank     ] 
   37 [blank     ] 
   38 [def       ] def _run(project_id, recipe):
   39 [import    ]     from app.core.orchestrator import run_full_pipeline
   40 [blank     ] 
   41 [code      ]     out_root = ROOT / "output" / "smoke_v26" / project_id
   42 [branch    ]     if out_root.exists():
   43 [code      ]         shutil.rmtree(out_root, ignore_errors=True)
   44 [return    ]     return run_full_pipeline(project_id, recipe, dry_run=False, out_root=out_root)
   45 [blank     ] 
   46 [blank     ] 
   47 [def       ] def _corr(p):
   48 [code      ]     y, _ = sf.read(p, always_2d=True)
   49 [branch    ]     if y.shape[1] < 2:
   50 [return    ]         return 1.0
   51 [return    ]     return float(np.corrcoef(y[:, 0], y[:, 1])[0, 1])
   52 [blank     ] 
   53 [blank     ] 
   54 [def       ] def _dbfs(p):
   55 [code      ]     y, _ = sf.read(p, always_2d=True)
   56 [code      ]     rms = float(np.sqrt(np.mean(y**2)))
   57 [return    ]     return 20.0 * np.log10(max(rms, 1e-12))
   58 [blank     ] 
   59 [blank     ] 
   60 [def       ] def main():
   61 [code      ]     print("=" * 64)
   62 [code      ]     print("ZS Music Maker v26 — smoke_v26 (stereo + loudness + drop)")
   63 [code      ]     print("=" * 64)
   64 [blank     ] 
   65 [code      ]     res = _run(
   66 [code      ]         "p_v26",
   67 [code      ]         {
   68 [code      ]             "references": [],
   69 [code      ]             "theme": "лето, тачки",
   70 [code      ]             "genre": "drift_phonk",
   71 [code      ]             "duration_sec": 35,
   72 [code      ]             "bpm_override": 130,
   73 [code      ]         },
   74 [code      ]     )
   75 [code      ]     root_out = ROOT / "output" / "smoke_v26" / "p_v26"
   76 [code      ]     beat = root_out / "beat.wav"
   77 [code      ]     master = root_out / "masters" / "master_streaming.wav"
   78 [blank     ] 
   79 [comment   ]     # 1
   80 [branch    ]     if beat.exists():
   81 [code      ]         y, sr = sf.read(str(beat), always_2d=True)
   82 [code      ]         stereo = y.shape[1] >= 2
   83 [code      ]         c = _corr(str(beat)) if stereo else 1.0
   84 [code      ]         check(
   85 [code      ]             "v26.beat_stereo",
   86 [code      ]             stereo and 0.3 <= c <= 0.98,
   87 [code      ]             f"shape={y.shape} corr={c:.3f}",
   88 [code      ]         )
   89 [branch    ]     else:
   90 [code      ]         check("v26.beat_stereo", False, "beat.wav missing")
   91 [blank     ] 
   92 [comment   ]     # 2
   93 [branch    ]     if master.exists():
   94 [code      ]         c = _corr(str(master))
   95 [code      ]         check("v26.master_stereo_preserved", 0.3 <= c <= 0.999, f"corr={c:.3f}")
   96 [branch    ]     else:
   97 [code      ]         check("v26.master_stereo_preserved", False, "master missing")
   98 [blank     ] 
   99 [comment   ]     # 3
  100 [branch    ]     if master.exists():
  101 [code      ]         db = _dbfs(str(master))
  102 [code      ]         check(
  103 [code      ]             "v26.master_loudness_target",
  104 [code      ]             -16.0 <= db <= -11.0,
  105 [code      ]             f"dBFS={db:.2f} target=-13.5±2.5",
  106 [code      ]         )
  107 [branch    ]     else:
  108 [code      ]         check("v26.master_loudness_target", False, "master missing")
  109 [blank     ] 
  110 [comment   ]     # 4
  111 [branch    ]     if beat.exists():
  112 [code      ]         y, sr = sf.read(str(beat), always_2d=False)
  113 [branch    ]         if y.ndim > 1:
  114 [code      ]             y = y.mean(axis=1)
  115 [code      ]         win = int(sr * 0.020)
  116 [code      ]         hop = int(sr * 0.010)
  117 [code      ]         rms = np.array(
  118 [code      ]             [
  119 [code      ]                 float(np.sqrt(np.mean(y[i : i + win] ** 2)) + 1e-12)
  120 [loop      ]                 for i in range(0, len(y) - win, hop)
  121 [code      ]             ]
  122 [code      ]         )
  123 [code      ]         med = float(np.median(rms))
  124 [code      ]         low = rms < (med * 0.15)
  125 [code      ]         max_run = cur = 0
  126 [loop      ]         for v in low:
  127 [branch    ]             if v:
  128 [code      ]                 cur += 1
  129 [code      ]                 max_run = max(max_run, cur)
  130 [branch    ]             else:
  131 [code      ]                 cur = 0
  132 [code      ]         check(
  133 [code      ]             "v26.beat_drop_fade",
  134 [code      ]             max_run >= 10,
  135 [code      ]             f"max_low_run={max_run} hops (need>=10, ~100ms)",
  136 [code      ]         )
  137 [branch    ]     else:
  138 [code      ]         check("v26.beat_drop_fade", False, "beat.wav missing")
  139 [blank     ] 
  140 [comment   ]     # 5
  141 [code      ]     hit = None
  142 [loop      ]     for s in res.get("stages", []):
  143 [branch    ]         if s.get("name") == "_stage_hit_score":
  144 [code      ]             hit = s.get("output") or {}
  145 [code      ]             break
  146 [branch    ]     if hit:
  147 [code      ]         sc = float(hit.get("hit_score", 0.0) or 0.0)
  148 [code      ]         check(
  149 [code      ]             "v26.hit_score_improved",
  150 [code      ]             sc >= 55.0,
  151 [code      ]             f"score={sc:.2f} (need>=55, prev v25=50.28)",
  152 [code      ]         )
  153 [branch    ]     else:
  154 [code      ]         check("v26.hit_score_improved", False, "no hit_score stage")
  155 [blank     ] 
  156 [comment   ]     # 6
  157 [try_block ]     try:
  158 [import    ]         from modules import hit_scorer as hs
  159 [blank     ] 
  160 [code      ]         sr = 22050
  161 [code      ]         t = np.arange(sr * 5) / sr
  162 [code      ]         env = np.zeros_like(t)
  163 [loop      ]         for i in range(5):
  164 [code      ]             st = int(i * sr * 1.0)
  165 [code      ]             en = min(st + int(sr * 0.4), len(env))
  166 [code      ]             env[st:en] = np.linspace(1.0, 0.0, en - st)
  167 [code      ]         y = env * np.sin(2 * np.pi * 220 * t) * 0.5
  168 [code      ]         score, raw = hs._hook_repeatability(y.astype(np.float32), sr)
  169 [code      ]         check(
  170 [code      ]             "v26.hook_repeat_fallback",
  171 [code      ]             raw >= 1,
  172 [code      ]             f"raw={raw} score={score:.1f} (need raw>=1)",
  173 [code      ]         )
  174 [try_block ]     except Exception as e:
  175 [code      ]         check("v26.hook_repeat_fallback", False, f"crash: {e}")
  176 [blank     ] 
  177 [code      ]     print("-" * 64)
  178 [code      ]     p = sum(1 for _, o, _ in RESULTS if o)
  179 [code      ]     f = len(RESULTS) - p
  180 [code      ]     print(f"RESULT: {p} PASS / {f} FAIL / {len(RESULTS)} total")
  181 [code      ]     _write_report("smoke_v26", p, f)
  182 [return    ]     return 0 if f == 0 else 1
  183 [blank     ] 
  184 [blank     ] 
  185 [def       ] def _write_report(name: str, passed: int, failed: int) -> None:
  186 [docstring ]     """v33: пишем JSON-отчёт в logs/ — его читают kpi_dashboard_v12 и
  187 [docstring ]     self_diag_v13 (раньше они искали несуществующий smoke_v12_report.json
  188 [docstring ]     и вечно показывали «smoke ещё не гонялся»)."""
  189 [import    ]     import json
  190 [import    ]     import time
  191 [import    ]     from pathlib import Path
  192 [blank     ] 
  193 [try_block ]     try:
  194 [code      ]         logs = Path(__file__).resolve().parents[1] / "logs"
  195 [code      ]         logs.mkdir(parents=True, exist_ok=True)
  196 [code      ]         cases = {n: bool(o) for n, o, _ in RESULTS}
  197 [code      ]         (logs / f"{name}_report.json").write_text(
  198 [code      ]             json.dumps(
  199 [code      ]                 {
  200 [code      ]                     "name": name,
  201 [code      ]                     "ts": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
  202 [code      ]                     "passed": passed,
  203 [code      ]                     "failed": failed,
  204 [code      ]                     "total": passed + failed,
  205 [code      ]                     "cases": cases,
  206 [code      ]                 },
  207 [code      ]                 ensure_ascii=False,
  208 [code      ]                 indent=1,
  209 [code      ]             ),
  210 [code      ]             encoding="utf-8",
  211 [code      ]         )
  212 [try_block ]     except Exception:
  213 [code      ]         pass  # отчёт — nice-to-have, не должен валить smoke
  214 [blank     ] 
  215 [blank     ] 
  216 [branch    ] if __name__ == "__main__":
  217 [raise     ]     raise SystemExit(main())
```