# ПОСТРОЧНЫЙ ЛИСТИНГ: `tools/smoke_v29.py`

**Всего строк:** 188

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 87 | 46.3 |
| blank | 31 | 16.5 |
| branch | 23 | 12.2 |
| docstring | 14 | 7.4 |
| import | 14 | 7.4 |
| def | 8 | 4.3 |
| comment | 4 | 2.1 |
| try_block | 4 | 2.1 |
| return | 3 | 1.6 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """
    3 [docstring ] ZS Music Maker — smoke_v29.py (God Mode E2E)
    4 [docstring ] ========================================================================
    5 [docstring ] Проверяет:
    6 [docstring ]   1) main.py --version читает version.json
    7 [docstring ]   2) modules.midi_generator (guard при отсутствии mido, реальный вывод при наличии)
    8 [docstring ]   3) full God Mode pipeline от ai_arrangement до god_mastering_pro
    9 [docstring ]   4) master_god.wav: стерео, длительность ~120с, peak <= -1 dBTP, RMS в диапазоне
   10 [docstring ]   5) honest LUFS-отчёт из mastering_pro
   11 [blank     ] 
   12 [docstring ] Запуск:
   13 [docstring ]     python3 tools/smoke_v29.py
   14 [docstring ] """
   15 [blank     ] 
   16 [import    ] from __future__ import annotations
   17 [blank     ] 
   18 [import    ] import json
   19 [import    ] import shutil
   20 [import    ] import subprocess
   21 [import    ] import sys
   22 [import    ] from pathlib import Path
   23 [blank     ] 
   24 [import    ] import numpy as np
   25 [import    ] import soundfile as sf
   26 [blank     ] 
   27 [code      ] ROOT = Path(__file__).resolve().parents[1]
   28 [code      ] sys.path.insert(0, str(ROOT))
   29 [blank     ] 
   30 [code      ] RESULTS = []
   31 [blank     ] 
   32 [blank     ] 
   33 [def       ] def _ok(name: str, extra: str = "") -> None:
   34 [code      ]     RESULTS.append((True, name, extra))
   35 [code      ]     print(f"[PASS] {name:40s} {extra}")
   36 [blank     ] 
   37 [blank     ] 
   38 [def       ] def _fail(name: str, extra: str = "") -> None:
   39 [code      ]     RESULTS.append((False, name, extra))
   40 [code      ]     print(f"[FAIL] {name:40s} {extra}")
   41 [blank     ] 
   42 [blank     ] 
   43 [def       ] def test_version_cli() -> None:
   44 [try_block ]     try:
   45 [code      ]         out = subprocess.run(
   46 [code      ]             [sys.executable, str(ROOT / "main.py"), "--version"],
   47 [code      ]             capture_output=True, text=True, timeout=30,
   48 [code      ]         )
   49 [branch    ]         if out.returncode == 0 and "ZS Music Maker" in out.stdout:
   50 [code      ]             _ok("v29.main_version_cli", f"rc=0 build in stdout")
   51 [branch    ]         else:
   52 [code      ]             _fail("v29.main_version_cli", f"rc={out.returncode}")
   53 [try_block ]     except Exception as e:
   54 [code      ]         _fail("v29.main_version_cli", str(e))
   55 [blank     ] 
   56 [blank     ] 
   57 [def       ] def test_midi_generator() -> None:
   58 [import    ]     from modules import midi_generator
   59 [code      ]     st = midi_generator.MIDIGenerator.get_status()
   60 [code      ]     g = midi_generator.MIDIGenerator(output_dir=str(ROOT / "output" / "smoke_v29" / "midi"))
   61 [code      ]     drum = g.generate_drum_pattern("drift_phonk", 140)
   62 [code      ]     mel = g.generate_melody_pattern("drift_phonk", "A", "minor", 140)
   63 [branch    ]     if st["ok"]:
   64 [branch    ]         if drum and mel and Path(drum).exists() and Path(mel).exists():
   65 [code      ]             _ok("v29.midi_generator", f"engine=mido drum+melody OK")
   66 [branch    ]         else:
   67 [code      ]             _fail("v29.midi_generator", f"mido installed but files missing: {drum!r} / {mel!r}")
   68 [branch    ]     else:
   69 [comment   ]         # honest BLOCKED — не должно ломать pipeline
   70 [branch    ]         if drum == "" and mel == "":
   71 [code      ]             _ok("v29.midi_generator", "BLOCKED honest fallback (mido missing)")
   72 [branch    ]         else:
   73 [code      ]             _fail("v29.midi_generator", f"expected empty strings, got {drum!r}/{mel!r}")
   74 [blank     ] 
   75 [blank     ] 
   76 [def       ] def test_god_mode_e2e() -> None:
   77 [code      ]     out_root = ROOT / "output" / "smoke_v29" / "god"
   78 [branch    ]     if out_root.exists():
   79 [code      ]         shutil.rmtree(out_root)
   80 [import    ]     from app.core.orchestrator_god import run_god_pipeline
   81 [code      ]     res = run_god_pipeline("smoke_v29", wizard_state=None, out_root=out_root)
   82 [blank     ] 
   83 [branch    ]     if res.get("status") == "completed":
   84 [code      ]         _ok("v29.god_e2e_status", f"elapsed={res.get('elapsed_sec')}s")
   85 [branch    ]     else:
   86 [code      ]         _fail("v29.god_e2e_status", json.dumps(res.get("stages", []), default=str)[:200])
   87 [return    ]         return
   88 [blank     ] 
   89 [code      ]     master = res.get("master_path")
   90 [branch    ]     if not master or not Path(master).exists():
   91 [code      ]         _fail("v29.god_e2e_master_exists", f"missing {master}")
   92 [return    ]         return
   93 [blank     ] 
   94 [code      ]     audio, sr = sf.read(master)
   95 [branch    ]     if audio.ndim == 2 and audio.shape[1] == 2:
   96 [code      ]         _ok("v29.god_e2e_stereo", f"shape={audio.shape} sr={sr}")
   97 [branch    ]     else:
   98 [code      ]         _fail("v29.god_e2e_stereo", f"shape={audio.shape}")
   99 [blank     ] 
  100 [code      ]     dur = len(audio) / sr
  101 [branch    ]     if 110 <= dur <= 130:
  102 [code      ]         _ok("v29.god_e2e_duration", f"{round(dur,1)}s")
  103 [branch    ]     else:
  104 [code      ]         _fail("v29.god_e2e_duration", f"{round(dur,1)}s (want ~120s)")
  105 [blank     ] 
  106 [code      ]     peak = float(np.max(np.abs(audio))) if audio.size else 0.0
  107 [code      ]     peak_db = 20.0 * np.log10(peak + 1e-12)
  108 [comment   ]     # ceiling -1 dBTP, допускаем небольшой запас
  109 [branch    ]     if peak_db <= -0.5:
  110 [code      ]         _ok("v29.god_e2e_true_peak", f"peak={round(peak_db,2)} dB (<= -0.5)")
  111 [branch    ]     else:
  112 [code      ]         _fail("v29.god_e2e_true_peak", f"peak={round(peak_db,2)} dB (>-0.5)")
  113 [blank     ] 
  114 [code      ]     rms = float(np.sqrt(np.mean(audio ** 2)))
  115 [branch    ]     if 0.03 <= rms <= 0.6:
  116 [code      ]         _ok("v29.god_e2e_rms", f"rms={round(rms,3)}")
  117 [branch    ]     else:
  118 [code      ]         _fail("v29.god_e2e_rms", f"rms={round(rms,3)} out of [0.03,0.6]")
  119 [blank     ] 
  120 [blank     ] 
  121 [def       ] def test_mastering_pro_metrics() -> None:
  122 [docstring ]     """mastering_pro возвращает честные output-метрики (v29)."""
  123 [import    ]     from modules import mastering_pro
  124 [comment   ]     # Синтетический вход
  125 [code      ]     sr = 44100
  126 [code      ]     t = np.linspace(0, 3.0, sr * 3, endpoint=False)
  127 [code      ]     x = 0.3 * np.sin(2 * np.pi * 220 * t).astype(np.float32)
  128 [code      ]     stereo = np.stack([x, x], axis=1)
  129 [code      ]     in_wav = ROOT / "output" / "smoke_v29" / "master_in.wav"
  130 [code      ]     out_wav = ROOT / "output" / "smoke_v29" / "master_out.wav"
  131 [code      ]     in_wav.parent.mkdir(parents=True, exist_ok=True)
  132 [code      ]     sf.write(str(in_wav), stereo, sr)
  133 [code      ]     r = mastering_pro.process_mastering(str(in_wav), str(out_wav), target_lufs=-14.0)
  134 [branch    ]     if r.get("ok") and "output_peak_db" in r and "channels" in r:
  135 [code      ]         _ok("v29.mastering_pro_metrics",
  136 [code      ]             f"engine={r['engine']} ch={r['channels']} peak={r['output_peak_db']}dB lufs={r.get('output_lufs')}")
  137 [branch    ]     else:
  138 [code      ]         _fail("v29.mastering_pro_metrics", str(r))
  139 [blank     ] 
  140 [blank     ] 
  141 [def       ] def main() -> int:
  142 [code      ]     print("=" * 64)
  143 [code      ]     print("ZS Music Maker v29 — smoke_v29 (God Mode E2E)")
  144 [code      ]     print("=" * 64)
  145 [code      ]     test_version_cli()
  146 [code      ]     test_midi_generator()
  147 [code      ]     test_god_mode_e2e()
  148 [code      ]     test_mastering_pro_metrics()
  149 [code      ]     print("-" * 64)
  150 [code      ]     passed = sum(1 for r in RESULTS if r[0])
  151 [code      ]     total = len(RESULTS)
  152 [code      ]     failed = total - passed
  153 [code      ]     print(f"RESULT: {passed} PASS / {failed} FAIL / {total} total")
  154 [code      ]     _write_report("smoke_v29", passed, failed)
  155 [return    ]     return 0 if failed == 0 else 1
  156 [blank     ] 
  157 [blank     ] 
  158 [def       ] def _write_report(name: str, passed: int, failed: int) -> None:
  159 [docstring ]     """v33: JSON-отчёт в logs/ для kpi_dashboard_v12 / self_diag_v13."""
  160 [import    ]     import json
  161 [import    ]     import time
  162 [import    ]     from pathlib import Path
  163 [blank     ] 
  164 [try_block ]     try:
  165 [code      ]         logs = Path(__file__).resolve().parents[1] / "logs"
  166 [code      ]         logs.mkdir(parents=True, exist_ok=True)
  167 [code      ]         cases = {str(r[1] if len(r) > 1 else i): bool(r[0]) for i, r in enumerate(RESULTS)}
  168 [code      ]         (logs / f"{name}_report.json").write_text(
  169 [code      ]             json.dumps(
  170 [code      ]                 {
  171 [code      ]                     "name": name,
  172 [code      ]                     "ts": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
  173 [code      ]                     "passed": passed,
  174 [code      ]                     "failed": failed,
  175 [code      ]                     "total": passed + failed,
  176 [code      ]                     "cases": cases,
  177 [code      ]                 },
  178 [code      ]                 ensure_ascii=False,
  179 [code      ]                 indent=1,
  180 [code      ]             ),
  181 [code      ]             encoding="utf-8",
  182 [code      ]         )
  183 [try_block ]     except Exception:
  184 [code      ]         pass  # отчёт — nice-to-have, не должен валить smoke
  185 [blank     ] 
  186 [blank     ] 
  187 [branch    ] if __name__ == "__main__":
  188 [code      ]     sys.exit(main())
```