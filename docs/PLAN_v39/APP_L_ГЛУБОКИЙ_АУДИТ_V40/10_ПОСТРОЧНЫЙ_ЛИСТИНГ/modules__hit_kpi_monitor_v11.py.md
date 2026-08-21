# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/hit_kpi_monitor_v11.py`

**Всего строк:** 349

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 217 | 62.2 |
| blank | 31 | 8.9 |
| branch | 20 | 5.7 |
| return | 16 | 4.6 |
| loop | 13 | 3.7 |
| def | 12 | 3.4 |
| docstring | 9 | 2.6 |
| import | 8 | 2.3 |
| try_block | 8 | 2.3 |
| comment | 6 | 1.7 |
| decorator | 4 | 1.1 |
| stmt | 3 | 0.9 |
| class | 2 | 0.6 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v11 — hit_kpi_monitor_v11.py
    3 [blank     ] 
    4 [docstring ] Реализует ТЗ 20.5 «НУЛЕВАЯ ТЕРПИМОСТЬ К ОТКАТУ ЦЕЛИ» — KPI-мониторинг:
    5 [docstring ] 1. Один трек ≤60 мин full / ≤180 мин fallback
    6 [docstring ] 2. RVC обучает модель ≤30 / ≤180 мин
    7 [docstring ] 3. AI Detector Pro verdict ≤30% / 40%
    8 [docstring ] 4. Release-пакет: все обязательные форматы
    9 [docstring ] 5. ≥5 треков через render_queue за вечер (сохранено от v9)
   10 [docstring ] """
   11 [blank     ] 
   12 [import    ] from __future__ import annotations
   13 [blank     ] 
   14 [import    ] import fnmatch
   15 [import    ] import json
   16 [import    ] import os
   17 [import    ] import sys
   18 [import    ] import time
   19 [import    ] from dataclasses import asdict, dataclass, field
   20 [blank     ] 
   21 [blank     ] 
   22 [def       ] def _safe_print(msg):
   23 [try_block ]     try:
   24 [code      ]         print(msg)
   25 [try_block ]     except UnicodeEncodeError:
   26 [code      ]         sys.stdout.buffer.write((msg + "\n").encode("cp866", errors="replace"))
   27 [blank     ] 
   28 [blank     ] 
   29 [code      ] KPI_TARGETS = {
   30 [code      ]     "full_hw": {
   31 [code      ]         "pipeline_max_min": 60,
   32 [code      ]         "rvc_train_max_min": 30,
   33 [code      ]         "ai_detector_max_percent": 30,
   34 [code      ]         "release_required": [
   35 [code      ]             "master_wav",
   36 [code      ]             "mp3_320",
   37 [code      ]             "flac",
   38 [code      ]             "instrumental",
   39 [code      ]             "acapella",
   40 [code      ]             "stems",
   41 [code      ]             "tiktok_mp4",
   42 [code      ]             "reels_mp4",
   43 [code      ]             "lyrics_txt",
   44 [code      ]             "lyrics_lrc",
   45 [code      ]             "recipe_json",
   46 [code      ]             "manifest_json",
   47 [code      ]             "cover_png",
   48 [code      ]         ],
   49 [code      ]     },
   50 [code      ]     "fallback_hw": {
   51 [code      ]         "pipeline_max_min": 180,
   52 [code      ]         "rvc_train_max_min": 180,
   53 [code      ]         "ai_detector_max_percent": 40,
   54 [code      ]         "release_required": [
   55 [code      ]             "master_wav",
   56 [code      ]             "mp3_320",
   57 [code      ]             "lyrics_txt",
   58 [code      ]             "recipe_json",
   59 [code      ]             "manifest_json",
   60 [code      ]             "cover_png",
   61 [code      ]         ],
   62 [code      ]     },
   63 [code      ] }
   64 [blank     ] 
   65 [blank     ] 
   66 [decorator ] @dataclass
   67 [class     ] class KpiStage:
   68 [code      ]     name: str
   69 [code      ]     started_at: float = 0.0
   70 [code      ]     ended_at: float = 0.0
   71 [code      ]     ok: bool = False
   72 [code      ]     note: str = ""
   73 [blank     ] 
   74 [decorator ]     @property
   75 [def       ]     def duration_min(self) -> float:
   76 [return    ]         return max(0.0, (self.ended_at - self.started_at) / 60.0)
   77 [blank     ] 
   78 [blank     ] 
   79 [decorator ] @dataclass
   80 [class     ] class KpiSession:
   81 [code      ]     project_id: str
   82 [code      ]     hw_mode: str = "full_hw"
   83 [code      ]     started_at: float = field(default_factory=time.time)
   84 [code      ]     ended_at: float = 0.0
   85 [code      ]     stages: list[KpiStage] = field(default_factory=list)
   86 [code      ]     ai_detector_percent: float = -1.0
   87 [code      ]     release_files_present: list[str] = field(default_factory=list)
   88 [code      ]     release_files_missing: list[str] = field(default_factory=list)
   89 [code      ]     verdict: str = "PENDING"
   90 [code      ]     recommendations: list[str] = field(default_factory=list)
   91 [blank     ] 
   92 [decorator ]     @property
   93 [def       ]     def pipeline_min(self) -> float:
   94 [code      ]         end = self.ended_at or time.time()
   95 [return    ]         return max(0.0, (end - self.started_at) / 60.0)
   96 [blank     ] 
   97 [def       ]     def start_stage(self, name):
   98 [code      ]         stg = KpiStage(name=name, started_at=time.time())
   99 [code      ]         self.stages.append(stg)
  100 [return    ]         return stg
  101 [blank     ] 
  102 [def       ]     def end_stage(self, stg, ok=True, note=""):
  103 [code      ]         stg.ended_at = time.time()
  104 [code      ]         stg.ok = ok
  105 [code      ]         stg.note = note
  106 [blank     ] 
  107 [def       ]     def to_dict(self):
  108 [code      ]         d = asdict(self)
  109 [code      ]         d["pipeline_min"] = self.pipeline_min
  110 [code      ]         d["stages_min"] = {s.name: s.duration_min for s in self.stages}
  111 [return    ]         return d
  112 [blank     ] 
  113 [blank     ] 
  114 [def       ] def check_release_completeness(release_dir, hw_mode="full_hw"):
  115 [code      ]     required = KPI_TARGETS.get(hw_mode, KPI_TARGETS["full_hw"])["release_required"]
  116 [code      ]     patterns = {
  117 [code      ]         "master_wav": ["master.wav", "final.wav", "*_master.wav"],
  118 [code      ]         "mp3_320": ["master.mp3", "final.mp3", "*_320.mp3", "*.mp3"],
  119 [code      ]         "flac": ["master.flac", "*.flac"],
  120 [code      ]         "instrumental": ["instrumental.wav", "instrumental.mp3", "instr.*"],
  121 [code      ]         "acapella": ["acapella.wav", "acapella.mp3", "vocal.*"],
  122 [code      ]         "stems": ["stems/", "stems"],
  123 [code      ]         "tiktok_mp4": ["tiktok_edit.mp4", "tiktok.mp4", "*tiktok*.mp4"],
  124 [code      ]         "reels_mp4": ["reels_edit.mp4", "reels.mp4", "*reels*.mp4"],
  125 [code      ]         "lyrics_txt": ["lyrics.txt"],
  126 [code      ]         "lyrics_lrc": ["lyrics.lrc"],
  127 [code      ]         "recipe_json": ["recipe.json", "*_recipe.json"],
  128 [code      ]         "manifest_json": ["manifest.json", "*_manifest.json"],
  129 [code      ]         "cover_png": ["cover.png", "cover.jpg", "artwork.*"],
  130 [code      ]     }
  131 [code      ]     present, missing = [], []
  132 [branch    ]     if not os.path.isdir(release_dir):
  133 [return    ]         return {"present": [], "missing": required, "release_dir": release_dir}
  134 [code      ]     all_files = []
  135 [loop      ]     for root, dirs, files in os.walk(release_dir):
  136 [code      ]         rel_root = os.path.relpath(root, release_dir)
  137 [loop      ]         for d in dirs:
  138 [code      ]             all_files.append(os.path.join(rel_root, d).replace("\\", "/") + "/")
  139 [loop      ]         for f in files:
  140 [code      ]             all_files.append(os.path.join(rel_root, f).replace("\\", "/"))
  141 [loop      ]     for key in required:
  142 [code      ]         pats = patterns.get(key, [key])
  143 [code      ]         found = False
  144 [loop      ]         for pat in pats:
  145 [loop      ]             for f in all_files:
  146 [code      ]                 base = os.path.basename(f.rstrip("/"))
  147 [branch    ]                 if (
  148 [code      ]                     fnmatch.fnmatch(base, pat)
  149 [code      ]                     or fnmatch.fnmatch(f, pat)
  150 [comment   ]                     # v34 FIX (P2.14): f уже нормализован в POSIX-вид
  151 [comment   ]                     # (os.path.relpath + replace("\\","/") выше), поэтому
  152 [comment   ]                     # sep-хак "*/"+pat больше не нужен для basename-паттернов,
  153 [comment   ]                     # но оставляем его для вложенных glob-паттернов (напр.
  154 [comment   ]                     # "stems/*.wav") — они матчатся против полного относительного
  155 [comment   ]                     # пути, где каталоги разделены именно "/".
  156 [code      ]                     or fnmatch.fnmatch(f, "*/" + pat)
  157 [code      ]                 ):
  158 [code      ]                     found = True
  159 [code      ]                     break
  160 [branch    ]             if found:
  161 [code      ]                 break
  162 [code      ]         (present if found else missing).append(key)
  163 [return    ]     return {"present": present, "missing": missing, "release_dir": release_dir}
  164 [blank     ] 
  165 [blank     ] 
  166 [def       ] def check_ai_detector(report):
  167 [branch    ]     if not report:
  168 [return    ]         return -1.0
  169 [loop      ]     for key in (
  170 [code      ]         "neuronoshnost_percent",
  171 [code      ]         "ai_percent",
  172 [code      ]         "verdict_percent",
  173 [code      ]         "percent",
  174 [code      ]         "score",
  175 [code      ]     ):
  176 [branch    ]         if key in report:
  177 [try_block ]             try:
  178 [code      ]                 v = float(report[key])
  179 [branch    ]                 if v > 1.0 and v <= 100.0:
  180 [return    ]                     return v
  181 [branch    ]                 if v <= 1.0:
  182 [return    ]                     return v * 100.0
  183 [try_block ]             except Exception:
  184 [code      ]                 pass
  185 [loop      ]     for k in ("summary", "verdict", "final"):
  186 [branch    ]         if isinstance(report.get(k), dict):
  187 [code      ]             v = check_ai_detector(report[k])
  188 [branch    ]             if v >= 0:
  189 [return    ]                 return v
  190 [return    ]     return -1.0
  191 [blank     ] 
  192 [blank     ] 
  193 [def       ] def finalize_session(
  194 [code      ]     session, release_dir=None, ai_detector_report=None, save_dir="data"
  195 [code      ] ):
  196 [code      ]     session.ended_at = time.time()
  197 [code      ]     targets = KPI_TARGETS.get(session.hw_mode, KPI_TARGETS["full_hw"])
  198 [code      ]     problems = []
  199 [branch    ]     if session.pipeline_min > targets["pipeline_max_min"]:
  200 [code      ]         problems.append(
  201 [code      ]             f"pipeline_slow: {session.pipeline_min:.1f} мин > "
  202 [code      ]             f"{targets['pipeline_max_min']} мин"
  203 [code      ]         )
  204 [code      ]         session.recommendations.append(
  205 [code      ]             "Ускорь пайплайн: включи Быстрый режим, проверь MusicGen-variant "
  206 [code      ]             "в hw_directml.py, убедись что кеш референсов не пересчитывается."
  207 [code      ]         )
  208 [loop      ]     for stg in session.stages:
  209 [branch    ]         if "rvc" in stg.name.lower() and "train" in stg.name.lower():
  210 [branch    ]             if stg.duration_min > targets["rvc_train_max_min"]:
  211 [code      ]                 problems.append(
  212 [code      ]                     f"rvc_train_slow: {stg.duration_min:.1f} > "
  213 [code      ]                     f"{targets['rvc_train_max_min']} мин"
  214 [code      ]                 )
  215 [code      ]                 session.recommendations.append(
  216 [code      ]                     "RVC обучается слишком долго. Проверь hw_directml.py, "
  217 [code      ]                     "уменьши эпохи для fallback, запусти ночной режим."
  218 [code      ]                 )
  219 [code      ]     ai_percent = check_ai_detector(ai_detector_report)
  220 [code      ]     session.ai_detector_percent = ai_percent
  221 [branch    ]     if 0 <= ai_percent and ai_percent > targets["ai_detector_max_percent"]:
  222 [code      ]         problems.append(
  223 [code      ]             f"neuronoshnost_high: {ai_percent:.1f}% > "
  224 [code      ]             f"{targets['ai_detector_max_percent']}%"
  225 [code      ]         )
  226 [code      ]         session.recommendations.append(
  227 [code      ]             "AI detector говорит слишком «нейроношно». Прогони "
  228 [code      ]             "anti_neuro_v10 aggressive, запиши больше живого голоса в Voice Vault."
  229 [code      ]         )
  230 [branch    ]     if release_dir:
  231 [code      ]         r = check_release_completeness(release_dir, session.hw_mode)
  232 [code      ]         session.release_files_present = r["present"]
  233 [code      ]         session.release_files_missing = r["missing"]
  234 [branch    ]         if r["missing"]:
  235 [code      ]             problems.append(
  236 [code      ]                 f"release_incomplete: missing " f"{len(r['missing'])} files"
  237 [code      ]             )
  238 [code      ]             session.recommendations.append(
  239 [code      ]                 f"В релизе не хватает: {', '.join(r['missing'])}. "
  240 [code      ]                 "Проверь release_pack_v9 + video_edit_v11 + cover_art_gen."
  241 [code      ]             )
  242 [code      ]     hard_fail_keys = ("release_incomplete", "pipeline_slow")
  243 [branch    ]     if any(p.startswith(k) for p in problems for k in hard_fail_keys):
  244 [code      ]         session.verdict = "HARD_FAIL"
  245 [branch    ]     elif problems:
  246 [code      ]         session.verdict = "SOFT_FAIL"
  247 [branch    ]     else:
  248 [code      ]         session.verdict = "PASS"
  249 [code      ]         session.recommendations.append("Все KPI выполнены. Трек соответствует ТЗ 20.5.")
  250 [try_block ]     try:
  251 [code      ]         os.makedirs(save_dir, exist_ok=True)
  252 [stmt      ]         with open(
  253 [code      ]             os.path.join(save_dir, "kpi_history.jsonl"), "a", encoding="utf-8"
  254 [code      ]         ) as f:
  255 [code      ]             f.write(json.dumps(session.to_dict(), ensure_ascii=False) + "\n")
  256 [try_block ]     except Exception as e:
  257 [code      ]         _safe_print(f"[kpi_v11] cannot persist: {e}")
  258 [code      ]     _safe_print(
  259 [code      ]         f"[kpi_v11] verdict={session.verdict} "
  260 [code      ]         f"pipeline={session.pipeline_min:.1f}min "
  261 [code      ]         f"ai={ai_percent:.1f}% "
  262 [code      ]         f"missing={len(session.release_files_missing)}"
  263 [code      ]     )
  264 [return    ]     return session
  265 [blank     ] 
  266 [blank     ] 
  267 [def       ] def render_kpi_report_md(session):
  268 [code      ]     lines = [
  269 [code      ]         "# KPI-отчёт по проекту `" + session.project_id + "`",
  270 [code      ]         "",
  271 [code      ]         f"- Verdict: **{session.verdict}**",
  272 [code      ]         f"- HW-режим: `{session.hw_mode}`",
  273 [code      ]         f"- Полный pipeline: **{session.pipeline_min:.1f} мин**",
  274 [code      ]         f"- AI Detector: **{session.ai_detector_percent:.1f}%** нейроношности",
  275 [code      ]         "",
  276 [code      ]         "## Этапы",
  277 [code      ]         "",
  278 [code      ]     ]
  279 [loop      ]     for s in session.stages:
  280 [code      ]         mark = "✅" if s.ok else "❌"
  281 [code      ]         lines.append(
  282 [code      ]             f"- {mark} `{s.name}` — {s.duration_min:.1f} мин "
  283 [code      ]             f"{('· ' + s.note) if s.note else ''}"
  284 [code      ]         )
  285 [code      ]     lines += [
  286 [code      ]         "",
  287 [code      ]         "## Файлы релиза",
  288 [code      ]         f"- Присутствуют: {', '.join(session.release_files_present) or '—'}",
  289 [code      ]         f"- Отсутствуют:  {', '.join(session.release_files_missing) or '—'}",
  290 [code      ]         "",
  291 [code      ]         "## Рекомендации",
  292 [code      ]         "",
  293 [code      ]     ]
  294 [loop      ]     for r in session.recommendations:
  295 [code      ]         lines.append(f"- {r}")
  296 [code      ]     lines.append("")
  297 [code      ]     lines.append("_ZS Music Maker v11 hit_kpi_monitor_v11._")
  298 [return    ]     return "\n".join(lines)
  299 [blank     ] 
  300 [blank     ] 
  301 [def       ] def latest_sessions(save_dir="data", limit=20):
  302 [code      ]     p = os.path.join(save_dir, "kpi_history.jsonl")
  303 [branch    ]     if not os.path.exists(p):
  304 [return    ]         return []
  305 [stmt      ]     with open(p, encoding="utf-8") as f:
  306 [code      ]         lines = [ln.strip() for ln in f if ln.strip()]
  307 [code      ]     out = []
  308 [loop      ]     for ln in lines[-limit:]:
  309 [try_block ]         try:
  310 [code      ]             out.append(json.loads(ln))
  311 [try_block ]         except Exception:
  312 [code      ]             continue
  313 [return    ]     return out
  314 [blank     ] 
  315 [blank     ] 
  316 [def       ] def _self_test():
  317 [import    ]     import tempfile
  318 [blank     ] 
  319 [stmt      ]     with tempfile.TemporaryDirectory() as tmp:
  320 [code      ]         s = KpiSession(project_id="test01", hw_mode="fallback_hw")
  321 [code      ]         st = s.start_stage("mix")
  322 [code      ]         time.sleep(0.02)
  323 [code      ]         s.end_stage(st, True)
  324 [code      ]         st2 = s.start_stage("rvc_train")
  325 [code      ]         time.sleep(0.02)
  326 [code      ]         s.end_stage(st2, True)
  327 [code      ]         rd = os.path.join(tmp, "rel")
  328 [code      ]         os.makedirs(rd)
  329 [loop      ]         for n in [
  330 [code      ]             "master.wav",
  331 [code      ]             "master.mp3",
  332 [code      ]             "lyrics.txt",
  333 [code      ]             "recipe.json",
  334 [code      ]             "manifest.json",
  335 [code      ]             "cover.png",
  336 [code      ]         ]:
  337 [code      ]             open(os.path.join(rd, n), "wb").close()
  338 [code      ]         s = finalize_session(
  339 [code      ]             s, release_dir=rd, ai_detector_report={"percent": 22.5}, save_dir=tmp
  340 [code      ]         )
  341 [code      ]         ok = s.verdict == "PASS"
  342 [code      ]         md = render_kpi_report_md(s)
  343 [code      ]         ok &= "KPI-отчёт" in md
  344 [code      ]         ok &= len(latest_sessions(save_dir=tmp)) == 1
  345 [return    ]         return ok
  346 [blank     ] 
  347 [blank     ] 
  348 [branch    ] if __name__ == "__main__":
  349 [code      ]     print("hit_kpi_monitor_v11 self-test:", "OK" if _self_test() else "FAIL")
```