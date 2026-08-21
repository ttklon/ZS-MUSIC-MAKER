# ПОСТРОЧНЫЙ ЛИСТИНГ: `tools/real_e2e_v14.py`

**Всего строк:** 186

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 108 | 58.1 |
| blank | 30 | 16.1 |
| docstring | 10 | 5.4 |
| import | 10 | 5.4 |
| branch | 9 | 4.8 |
| loop | 5 | 2.7 |
| return | 5 | 2.7 |
| comment | 3 | 1.6 |
| def | 3 | 1.6 |
| try_block | 2 | 1.1 |
| raise | 1 | 0.5 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v14 — tools/real_e2e_v14.py
    3 [blank     ] 
    4 [docstring ] РЕАЛЬНЫЙ E2E-прогон:
    5 [docstring ]   1) генерирует синтетический WAV-референс;
    6 [docstring ]   2) вызывает run_full_pipeline(dry_run=False);
    7 [docstring ]   3) сохраняет артефакты в output/audit_v14/e2e_v14_<ts>/;
    8 [docstring ]   4) проверяет каждый выходной файл;
    9 [docstring ]   5) собирает fallback_audit + readiness;
   10 [docstring ]   6) финальный отчёт в JSON.
   11 [docstring ] """
   12 [blank     ] 
   13 [import    ] from __future__ import annotations
   14 [blank     ] 
   15 [import    ] import json
   16 [import    ] import sys
   17 [import    ] import time
   18 [import    ] from pathlib import Path
   19 [blank     ] 
   20 [code      ] ROOT = Path(__file__).resolve().parents[1]
   21 [comment   ] # v23 FIX: при прямом запуске «python3 tools/real_e2e_v14.py» каталог tools/
   22 [comment   ] # попадает в sys.path вместо корня проекта — из-за этого `import app`
   23 [comment   ] # падал с ModuleNotFoundError. Гарантируем ROOT в sys.path.
   24 [branch    ] if str(ROOT) not in sys.path:
   25 [code      ]     sys.path.insert(0, str(ROOT))
   26 [blank     ] 
   27 [blank     ] 
   28 [def       ] def _synthesize_reference(
   29 [code      ]     out_wav: Path, duration: float = 15.0, sr: int = 44100, bpm: int = 140
   30 [code      ] ) -> dict:
   31 [import    ]     import numpy as np
   32 [import    ]     import soundfile as sf
   33 [blank     ] 
   34 [code      ]     n = int(sr * duration)
   35 [code      ]     t = np.arange(n) / sr
   36 [code      ]     y = np.zeros(n, dtype="float32")
   37 [blank     ] 
   38 [code      ]     beat = 60.0 / bpm
   39 [loop      ]     for i in range(int(duration / beat)):
   40 [code      ]         s = int(i * beat * sr)
   41 [code      ]         e = min(s + int(sr * 0.15), n)
   42 [branch    ]         if i % 2 == 0:
   43 [code      ]             tt = np.arange(e - s) / sr
   44 [code      ]             freq = 55 * np.exp(-tt * 15)
   45 [code      ]             y[s:e] += np.sin(2 * np.pi * np.cumsum(freq) / sr) * np.exp(-tt * 8) * 0.9
   46 [branch    ]         else:
   47 [code      ]             tt = np.arange(e - s) / sr
   48 [code      ]             tone = np.sin(2 * np.pi * 220 * tt) * np.exp(-tt * 25)
   49 [code      ]             noise = np.random.randn(e - s).astype("float32") * np.exp(-tt * 10)
   50 [code      ]             y[s:e] += (tone * 0.4 + noise * 0.6) * 0.7
   51 [code      ]         y[s:e] += np.sin(2 * np.pi * 55 * t[s:e]) * 0.15
   52 [blank     ] 
   53 [loop      ]     for j in range(int(duration / (beat / 2))):
   54 [code      ]         s = int(j * beat / 2 * sr)
   55 [code      ]         e = min(s + int(sr * 0.05), n)
   56 [code      ]         tt = np.arange(e - s) / sr
   57 [code      ]         y[s:e] += np.random.randn(e - s).astype("float32") * np.exp(-tt * 60) * 0.35
   58 [blank     ] 
   59 [code      ]     y = y / (np.max(np.abs(y)) + 1e-9) * 0.9
   60 [code      ]     out_wav.parent.mkdir(parents=True, exist_ok=True)
   61 [code      ]     sf.write(str(out_wav), y, sr)
   62 [return    ]     return {"path": str(out_wav), "sr": sr, "duration": duration, "bpm": bpm}
   63 [blank     ] 
   64 [blank     ] 
   65 [def       ] def _check_wav(path: str) -> dict:
   66 [try_block ]     try:
   67 [import    ]         import soundfile as sf
   68 [blank     ] 
   69 [code      ]         info = sf.info(path)
   70 [return    ]         return {
   71 [code      ]             "exists": True,
   72 [code      ]             "path": path,
   73 [code      ]             "sr": info.samplerate,
   74 [code      ]             "channels": info.channels,
   75 [code      ]             "duration_sec": round(info.frames / info.samplerate, 2),
   76 [code      ]             "size_bytes": Path(path).stat().st_size,
   77 [code      ]         }
   78 [try_block ]     except Exception as e:
   79 [return    ]         return {"exists": False, "path": path, "error": str(e)}
   80 [blank     ] 
   81 [blank     ] 
   82 [def       ] def main() -> int:
   83 [code      ]     print("=" * 64)
   84 [code      ]     print("ZS Music Maker v14 — real_e2e_v14 (non-dry pipeline)")
   85 [code      ]     print("=" * 64)
   86 [blank     ] 
   87 [code      ]     ts = int(time.time())
   88 [code      ]     workdir = ROOT / "output" / "audit_v14" / f"e2e_v14_{ts}"
   89 [code      ]     workdir.mkdir(parents=True, exist_ok=True)
   90 [blank     ] 
   91 [code      ]     ref_path = workdir / "reference.wav"
   92 [code      ]     ref_meta = _synthesize_reference(ref_path, duration=15.0, bpm=140)
   93 [code      ]     print(
   94 [code      ]         f"[e2e] synthetic reference: {ref_path}  (sr={ref_meta['sr']}, dur={ref_meta['duration']}s)"
   95 [code      ]     )
   96 [blank     ] 
   97 [import    ]     from app.core.orchestrator import run_full_pipeline
   98 [blank     ] 
   99 [code      ]     result = run_full_pipeline(
  100 [code      ]         project_id=f"e2e_v14_{ts}",
  101 [code      ]         wizard_state={
  102 [code      ]             "references": [str(ref_path)],
  103 [code      ]             "theme": "лето, тачки, ночной драйв",
  104 [code      ]             "genre": "drift_phonk",
  105 [code      ]             "artist": "ZS Producer",
  106 [code      ]         },
  107 [code      ]         dry_run=False,
  108 [code      ]         out_root=workdir,
  109 [code      ]     )
  110 [blank     ] 
  111 [code      ]     (workdir / "pipeline_result.json").write_text(
  112 [code      ]         json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
  113 [code      ]     )
  114 [blank     ] 
  115 [code      ]     artifacts = {}
  116 [loop      ]     for cand in ("beat.wav", "voice_preview.wav", "mix_ducked.wav", "polished.wav"):
  117 [code      ]         p = workdir / cand
  118 [branch    ]         if p.exists():
  119 [code      ]             artifacts[cand] = _check_wav(str(p))
  120 [blank     ] 
  121 [code      ]     masters_dir = workdir / "masters"
  122 [code      ]     stands_check = {}
  123 [branch    ]     if masters_dir.exists():
  124 [loop      ]         for m in masters_dir.glob("master_*.wav"):
  125 [code      ]             stands_check[m.name] = _check_wav(str(m))
  126 [blank     ] 
  127 [code      ]     release_dir = workdir / "release"
  128 [code      ]     release_check = {}
  129 [branch    ]     if release_dir.exists():
  130 [loop      ]         for f in release_dir.iterdir():
  131 [branch    ]             if f.is_file():
  132 [code      ]                 release_check[f.name] = {"size": f.stat().st_size, "path": str(f)}
  133 [blank     ] 
  134 [import    ]     from tools import fallback_audit, readiness
  135 [blank     ] 
  136 [code      ]     fb = fallback_audit.scan_all()
  137 [code      ]     pct, blocks = readiness.compute()
  138 [blank     ] 
  139 [code      ]     summary = {
  140 [code      ]         "timestamp": ts,
  141 [code      ]         "workdir": str(workdir),
  142 [code      ]         "reference": ref_meta,
  143 [code      ]         "pipeline_verdict": result.get("verdict"),
  144 [code      ]         "pipeline_percent": result.get("percent"),
  145 [code      ]         "pipeline_stages": len(result.get("stages", [])),
  146 [code      ]         "stages_ok": sum(1 for s in result.get("stages", []) if s.get("ok")),
  147 [code      ]         "stages_fallback": sum(
  148 [code      ]             1 for s in result.get("stages", []) if s.get("fallback_used")
  149 [code      ]         ),
  150 [code      ]         "warnings": result.get("warnings", []),
  151 [code      ]         "artifacts_present": artifacts,
  152 [code      ]         "mastering_stands_present": stands_check,
  153 [code      ]         "release_pack_files": release_check,
  154 [code      ]         "fallback_audit_summary": fb.get("summary", {}),
  155 [code      ]         "fallback_red_flags_count": {
  156 [code      ]             k: len(v) for k, v in fb.get("red_flags", {}).items()
  157 [code      ]         },
  158 [code      ]         "readiness_percent": pct,
  159 [code      ]         "readiness_caps": blocks.get("caps_triggered", []),
  160 [code      ]     }
  161 [code      ]     (workdir / "e2e_summary.json").write_text(
  162 [code      ]         json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
  163 [code      ]     )
  164 [blank     ] 
  165 [code      ]     print()
  166 [code      ]     print("─" * 64)
  167 [code      ]     print(f"Verdict:            {summary['pipeline_verdict']}")
  168 [code      ]     print(f"Stages ok/total:    {summary['stages_ok']}/{summary['pipeline_stages']}")
  169 [code      ]     print(f"Fallback stages:    {summary['stages_fallback']}")
  170 [code      ]     print(f"Masters generated:  {len(stands_check)}/8")
  171 [code      ]     print(f"Release files:      {len(release_check)}")
  172 [code      ]     print(f"Readiness (formula):{summary['readiness_percent']}%")
  173 [code      ]     print(f"Red flags:          {summary['fallback_red_flags_count']}")
  174 [code      ]     print(f"Full JSON:          {workdir / 'e2e_summary.json'}")
  175 [code      ]     print()
  176 [blank     ] 
  177 [branch    ]     if (
  178 [code      ]         summary["pipeline_stages"]
  179 [code      ]         and summary["stages_ok"] / summary["pipeline_stages"] >= 0.6
  180 [code      ]     ):
  181 [return    ]         return 0
  182 [return    ]     return 1
  183 [blank     ] 
  184 [blank     ] 
  185 [branch    ] if __name__ == "__main__":
  186 [raise     ]     raise SystemExit(main())
```