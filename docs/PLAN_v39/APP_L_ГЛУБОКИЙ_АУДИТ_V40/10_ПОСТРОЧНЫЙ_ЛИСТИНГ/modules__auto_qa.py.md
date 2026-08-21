# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/auto_qa.py`

**Всего строк:** 204

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 101 | 49.5 |
| docstring | 25 | 12.3 |
| blank | 24 | 11.8 |
| branch | 17 | 8.3 |
| import | 10 | 4.9 |
| return | 9 | 4.4 |
| comment | 6 | 2.9 |
| try_block | 6 | 2.9 |
| def | 4 | 2.0 |
| loop | 2 | 1.0 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v8] auto_qa.py — Auto Quality Assurance loop.
    3 [blank     ] 
    4 [docstring ] ТЗ 20.2 п.34: «Программа должна сделать и прослушать трек так, как это сделал
    5 [docstring ] бы человек. Прям чтобы это 100% было слушабельно.»
    6 [blank     ] 
    7 [docstring ] Auto-QA берёт финальный master.wav и прогоняет его через 3 виртуальных «уха»:
    8 [docstring ]   1. AI Detector Pro (9 метрик) — оценка «нейроношности».
    9 [docstring ]   2. Loudness/LUFS/peak/DR — соответствие коммерческому уровню.
   10 [docstring ]   3. Structure & hook check — есть ли зацепляющий припев, не «плоско».
   11 [blank     ] 
   12 [docstring ] По сумме выдаёт verdict:
   13 [docstring ]   • ✅ РЕЛИЗ — можно выпускать;
   14 [docstring ]   • ⚠ ПЕРЕДЕЛАТЬ ЧАСТЬ — конкретно какой узел (beat/vocal/master);
   15 [docstring ]   • ❌ ПЕРЕСОБРАТЬ ВСЁ — критично много флагов, нужен полный ре-run.
   16 [blank     ] 
   17 [docstring ] Возвращает JSON с рекомендациями. Orchestrator сам решает — цикл повторить или
   18 [docstring ] завершить, если пользователь включил auto_qa_loop=True.
   19 [docstring ] """
   20 [blank     ] 
   21 [import    ] from __future__ import annotations
   22 [blank     ] 
   23 [import    ] import json
   24 [import    ] import math
   25 [import    ] import time
   26 [import    ] from pathlib import Path
   27 [blank     ] 
   28 [code      ] ROOT = Path(__file__).resolve().parents[1]
   29 [code      ] QA_DIR = ROOT / "output" / "auto_qa"
   30 [comment   ] # v22: ленивое создание (не при импорте)
   31 [blank     ] 
   32 [blank     ] 
   33 [def       ] def _loudness(y, sr) -> dict:
   34 [docstring ]     """Приблизительный интегрированный LUFS / peak / crest factor."""
   35 [import    ]     import numpy as np
   36 [blank     ] 
   37 [branch    ]     if y.ndim > 1:
   38 [code      ]         m = y.mean(axis=1)
   39 [branch    ]     else:
   40 [code      ]         m = y
   41 [code      ]     peak = float(np.max(np.abs(m))) if len(m) else 0.0
   42 [code      ]     rms = float(np.sqrt(np.mean(m * m))) if len(m) else 0.0
   43 [code      ]     peak_db = 20 * math.log10(peak + 1e-9)
   44 [code      ]     rms_db = 20 * math.log10(rms + 1e-9)
   45 [code      ]     lufs_approx = rms_db - 3.0  # very rough K-weighting
   46 [code      ]     crest = peak_db - rms_db
   47 [return    ]     return {
   48 [code      ]         "peak_db": round(peak_db, 2),
   49 [code      ]         "rms_db": round(rms_db, 2),
   50 [code      ]         "lufs_approx": round(lufs_approx, 2),
   51 [code      ]         "crest_factor_db": round(crest, 2),
   52 [code      ]     }
   53 [blank     ] 
   54 [blank     ] 
   55 [def       ] def _structure_check(y, sr) -> dict:
   56 [docstring ]     """Ищем хук: повторяющийся куск ~8 сек с высокой энергией."""
   57 [try_block ]     try:
   58 [import    ]         import librosa
   59 [import    ]         import numpy as np
   60 [blank     ] 
   61 [code      ]         rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=1024)[0]
   62 [comment   ]         # 8-сек окно ~ 44100*8/1024
   63 [code      ]         w = int(sr * 8 / 1024)
   64 [branch    ]         if len(rms) < 3 * w:
   65 [return    ]             return {"hook_score": 0.0, "sections_detected": 0}
   66 [code      ]         chunks = [rms[i : i + w] for i in range(0, len(rms) - w, w // 2)]
   67 [code      ]         best_corr = 0.0
   68 [loop      ]         for i in range(len(chunks)):
   69 [loop      ]             for j in range(i + 2, len(chunks)):
   70 [code      ]                 a = chunks[i]
   71 [code      ]                 b = chunks[j]
   72 [branch    ]                 if len(a) != len(b):
   73 [code      ]                     continue
   74 [code      ]                 da = a - a.mean()
   75 [code      ]                 db = b - b.mean()
   76 [code      ]                 den = np.linalg.norm(da) * np.linalg.norm(db) + 1e-9
   77 [code      ]                 c = float(np.dot(da, db) / den)
   78 [code      ]                 best_corr = max(best_corr, c)
   79 [return    ]         return {
   80 [code      ]             "hook_score": round(best_corr, 3),
   81 [code      ]             "sections_detected": len(chunks),
   82 [code      ]         }
   83 [try_block ]     except Exception as e:
   84 [return    ]         return {"hook_score": 0.0, "error": str(e)}
   85 [blank     ] 
   86 [blank     ] 
   87 [def       ] def audit_track(master_wav: str | Path, target_lufs: float = -9.0) -> dict:
   88 [docstring ]     """
   89 [docstring ]     Полный аудит финального трека. Возвращает dict с 3 блоками:
   90 [docstring ]     {ai_detector, loudness, structure, verdict, actions[]}
   91 [docstring ]     """
   92 [code      ]     master_wav = Path(master_wav)
   93 [code      ]     result = {
   94 [code      ]         "master": str(master_wav),
   95 [code      ]         "ts": time.time(),
   96 [code      ]         "ok": False,
   97 [code      ]         "actions": [],
   98 [code      ]     }
   99 [branch    ]     if not master_wav.exists():
  100 [code      ]         result["error"] = "master.wav не найден"
  101 [return    ]         return result
  102 [blank     ] 
  103 [comment   ]     # 1) AI Detector Pro
  104 [try_block ]     try:
  105 [import    ]         from modules.ai_detector_pro import analyze_track
  106 [blank     ] 
  107 [code      ]         ad = analyze_track(str(master_wav))
  108 [code      ]         result["ai_detector"] = ad
  109 [code      ]         neuro = ad.get("neuronoshnost_percent", ad.get("neuroness_percent", 0))
  110 [branch    ]         if neuro and neuro > 70:
  111 [code      ]             result["actions"].append(
  112 [code      ]                 {
  113 [code      ]                     "target": "voice",
  114 [code      ]                     "reason": f"AI detector: {neuro}% нейроношности",
  115 [code      ]                     "fix": "переделать голос через ProVoice Mode + добавить бэки",
  116 [code      ]                 }
  117 [code      ]             )
  118 [branch    ]         elif neuro and neuro > 40:
  119 [code      ]             result["actions"].append(
  120 [code      ]                 {
  121 [code      ]                     "target": "vocal_humanization",
  122 [code      ]                     "reason": f"AI detector: {neuro}% нейроношности",
  123 [code      ]                     "fix": "усилить humanization (тайминг, дыхания, adlibs)",
  124 [code      ]                 }
  125 [code      ]             )
  126 [try_block ]     except Exception as e:
  127 [code      ]         result["ai_detector"] = {"error": str(e)}
  128 [blank     ] 
  129 [comment   ]     # 2) Loudness / structure
  130 [try_block ]     try:
  131 [import    ]         import soundfile as sf
  132 [blank     ] 
  133 [code      ]         y, sr = sf.read(str(master_wav))
  134 [branch    ]         if y.ndim > 1:
  135 [code      ]             y_mono = y.mean(axis=1)
  136 [branch    ]         else:
  137 [code      ]             y_mono = y
  138 [code      ]         result["loudness"] = _loudness(y, sr)
  139 [code      ]         result["structure"] = _structure_check(y_mono, sr)
  140 [blank     ] 
  141 [code      ]         lu = result["loudness"]["lufs_approx"]
  142 [branch    ]         if lu < target_lufs - 3:
  143 [code      ]             result["actions"].append(
  144 [code      ]                 {
  145 [code      ]                     "target": "mastering",
  146 [code      ]                     "reason": f"Слишком тихо (LUFS≈{lu}, target={target_lufs})",
  147 [code      ]                     "fix": "усилить лимитер, повторить Matchering",
  148 [code      ]                 }
  149 [code      ]             )
  150 [branch    ]         if result["loudness"]["peak_db"] > -0.2:
  151 [code      ]             result["actions"].append(
  152 [code      ]                 {
  153 [code      ]                     "target": "mastering",
  154 [code      ]                     "reason": "Клиппинг на пиках",
  155 [code      ]                     "fix": "мягкий true-peak limiter −1 dBTP",
  156 [code      ]                 }
  157 [code      ]             )
  158 [branch    ]         if result["structure"]["hook_score"] < 0.35:
  159 [code      ]             result["actions"].append(
  160 [code      ]                 {
  161 [code      ]                     "target": "beat",
  162 [code      ]                     "reason": "Не найден яркий хук",
  163 [code      ]                     "fix": "усилить контраст припева, повторить Beat Constructor",
  164 [code      ]                 }
  165 [code      ]             )
  166 [try_block ]     except Exception as e:
  167 [code      ]         result["loudness_error"] = str(e)
  168 [blank     ] 
  169 [comment   ]     # 3) Verdict
  170 [code      ]     n_actions = len(result["actions"])
  171 [branch    ]     if n_actions == 0:
  172 [code      ]         result["verdict"] = "release"
  173 [code      ]         result["verdict_text"] = "✅ Готов к релизу"
  174 [branch    ]     elif n_actions <= 2:
  175 [code      ]         result["verdict"] = "patch"
  176 [code      ]         result["verdict_text"] = "⚠ Переделать: " + ", ".join(
  177 [code      ]             a["target"] for a in result["actions"]
  178 [code      ]         )
  179 [branch    ]     else:
  180 [code      ]         result["verdict"] = "rebuild"
  181 [code      ]         result["verdict_text"] = "❌ Пересобрать всё"
  182 [blank     ] 
  183 [comment   ]     # Save
  184 [code      ]     out = QA_DIR / f"qa_{int(time.time())}.json"
  185 [code      ]     out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
  186 [code      ]     result["report_path"] = str(out)
  187 [code      ]     result["ok"] = True
  188 [return    ]     return result
  189 [blank     ] 
  190 [blank     ] 
  191 [def       ] def should_retry(
  192 [code      ]     qa_report: dict, max_iterations: int = 3, current_iter: int = 0
  193 [code      ] ) -> tuple[bool, list[str]]:
  194 [docstring ]     """
  195 [docstring ]     Решаем — гонять ли pipeline снова.
  196 [docstring ]     Возвращает (retry: bool, targets: list[str]).
  197 [docstring ]     """
  198 [branch    ]     if current_iter >= max_iterations:
  199 [return    ]         return False, []
  200 [code      ]     verdict = qa_report.get("verdict")
  201 [branch    ]     if verdict == "release":
  202 [return    ]         return False, []
  203 [code      ]     targets = list(set(a["target"] for a in qa_report.get("actions", [])))
  204 [return    ]     return True, targets
```