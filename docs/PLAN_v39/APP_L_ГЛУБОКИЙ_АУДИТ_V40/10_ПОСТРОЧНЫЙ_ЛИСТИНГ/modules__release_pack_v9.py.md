# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/release_pack_v9.py`

**Всего строк:** 180

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 95 | 52.8 |
| docstring | 23 | 12.8 |
| blank | 23 | 12.8 |
| branch | 15 | 8.3 |
| import | 6 | 3.3 |
| comment | 5 | 2.8 |
| def | 4 | 2.2 |
| return | 4 | 2.2 |
| loop | 3 | 1.7 |
| try_block | 2 | 1.1 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v9] release_pack_v9.py — расширенная сборка релиз-пакета.
    3 [blank     ] 
    4 [docstring ] По ТЗ 3.12 (Export & Release Package):
    5 [docstring ]   Полный релиз содержит master.wav/mp3/flac + инструментал + акапелла + стемы +
    6 [docstring ]   lyrics.txt/lrc + cover.png + tiktok.mp4/reels.mp4 + car/club/streaming +
    7 [docstring ]   manifest.json + metadata.json + recipe.json.
    8 [blank     ] 
    9 [docstring ] v9 добавляет к v6 release_pack_v6 / v7 release_export:
   10 [docstring ]   • hit_score.json                    — отчёт hit_scorer
   11 [docstring ]   • arrangement_plan.json             — план из arrangement_engine
   12 [docstring ]   • style_fingerprint.json            — style_vector из reference_ingest
   13 [docstring ]   • sample_manifest.json              — юр. чистота сэмплов (v9 sample_hunter)
   14 [docstring ]   • voice_manifest.json               — какие записи скормлены в RVC
   15 [docstring ]   • tiktok/hook_loop.wav              — фрагменты для эдитов
   16 [docstring ]   • README_RELEASE.txt                — читабельная сводка релиза
   17 [blank     ] 
   18 [docstring ] НИЧЕГО не удаляет из v6/v7. Работает как append-режим: даёт файлы поверх
   19 [docstring ] существующей папки релиза.
   20 [docstring ] """
   21 [blank     ] 
   22 [import    ] from __future__ import annotations
   23 [blank     ] 
   24 [import    ] import json
   25 [import    ] import shutil
   26 [import    ] import time
   27 [import    ] from pathlib import Path
   28 [blank     ] 
   29 [code      ] ROOT = Path(__file__).resolve().parents[1]
   30 [blank     ] 
   31 [blank     ] 
   32 [def       ] def _safe_copy(src: str, dst: str) -> bool:
   33 [try_block ]     try:
   34 [code      ]         Path(dst).parent.mkdir(parents=True, exist_ok=True)
   35 [code      ]         shutil.copy2(src, dst)
   36 [return    ]         return True
   37 [try_block ]     except Exception:
   38 [return    ]         return False
   39 [blank     ] 
   40 [blank     ] 
   41 [def       ] def _write_json(path: str, data: dict) -> None:
   42 [code      ]     Path(path).parent.mkdir(parents=True, exist_ok=True)
   43 [code      ]     Path(path).write_text(
   44 [code      ]         json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
   45 [code      ]     )
   46 [blank     ] 
   47 [blank     ] 
   48 [def       ] def _readme_text(payload: dict) -> str:
   49 [code      ]     lines = [
   50 [code      ]         f"# {payload.get('title', 'Untitled')} — {payload.get('artist', '')}",
   51 [code      ]         "",
   52 [code      ]         f"BPM: {payload.get('bpm')} · Key: {payload.get('key')} "
   53 [code      ]         f"{payload.get('mode')}",
   54 [code      ]         f"Genre: {payload.get('genre')} · Mood: {payload.get('mood')}",
   55 [code      ]         f"Duration: {payload.get('duration_s')} sec",
   56 [code      ]         f"Hit Score: {payload.get('hit_score')} — {payload.get('hit_verdict')}",
   57 [code      ]         "",
   58 [code      ]         "## Files",
   59 [code      ]     ]
   60 [loop      ]     for f in payload.get("files", []):
   61 [code      ]         lines.append(f"  · {f}")
   62 [code      ]     lines += [
   63 [code      ]         "",
   64 [code      ]         "## Legal",
   65 [code      ]         "Все использованные сэмплы имеют лицензии CC0 / CC-BY / Public Domain",
   66 [code      ]         "или предоставлены пользователем локально. Тексты — оригинал.",
   67 [code      ]         "Голос синтезирован Silero/Bark/XTTS и переконвертирован RVC в",
   68 [code      ]         "тембр пользователя (голосовой профиль обучен на его же записях).",
   69 [code      ]         "",
   70 [code      ]         f"Собрано: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}",
   71 [code      ]     ]
   72 [return    ]     return "\n".join(lines)
   73 [blank     ] 
   74 [blank     ] 
   75 [def       ] def build_release_v9(
   76 [code      ]     release_dir: str,
   77 [code      ]     project_meta: dict,
   78 [code      ]     master_wav: str,
   79 [code      ]     hit_report: dict | None = None,
   80 [code      ]     arrangement_plan: dict | None = None,
   81 [code      ]     style_fingerprint: dict | None = None,
   82 [code      ]     sample_manifest: dict | None = None,
   83 [code      ]     voice_manifest: dict | None = None,
   84 [code      ]     stand_wavs: dict | None = None,
   85 [code      ]     tiktok_wavs: dict | None = None,
   86 [code      ] ) -> dict:
   87 [docstring ]     """
   88 [docstring ]     Дописывает v9-артефакты в существующую (или новую) папку релиза.
   89 [docstring ]     project_meta: {artist, title, bpm, key, mode, genre, mood, duration_s, ...}
   90 [docstring ]     stand_wavs:   {"car": "/path/car_master.wav", "club": ..., "streaming": ...}
   91 [docstring ]     tiktok_wavs:  {"tiktok_15s": "...", "tiktok_30s": "...", "hook_loop": "..."}
   92 [docstring ]     """
   93 [code      ]     outd = Path(release_dir)
   94 [code      ]     outd.mkdir(parents=True, exist_ok=True)
   95 [code      ]     files: list[str] = []
   96 [code      ]     warnings: list[str] = []
   97 [blank     ] 
   98 [comment   ]     # master.wav — копируем если ещё не там
   99 [code      ]     master_dst = outd / "master.wav"
  100 [branch    ]     if Path(master_wav).exists() and not master_dst.exists():
  101 [branch    ]         if _safe_copy(master_wav, str(master_dst)):
  102 [code      ]             files.append("master.wav")
  103 [blank     ] 
  104 [comment   ]     # v9 JSON-артефакты
  105 [branch    ]     if hit_report:
  106 [code      ]         _write_json(str(outd / "hit_score.json"), hit_report)
  107 [code      ]         files.append("hit_score.json")
  108 [branch    ]     if arrangement_plan:
  109 [code      ]         _write_json(str(outd / "arrangement_plan.json"), arrangement_plan)
  110 [code      ]         files.append("arrangement_plan.json")
  111 [branch    ]     if style_fingerprint:
  112 [code      ]         _write_json(str(outd / "style_fingerprint.json"), style_fingerprint)
  113 [code      ]         files.append("style_fingerprint.json")
  114 [branch    ]     if sample_manifest:
  115 [code      ]         _write_json(str(outd / "sample_manifest.json"), sample_manifest)
  116 [code      ]         files.append("sample_manifest.json")
  117 [branch    ]     if voice_manifest:
  118 [code      ]         _write_json(str(outd / "voice_manifest.json"), voice_manifest)
  119 [code      ]         files.append("voice_manifest.json")
  120 [blank     ] 
  121 [comment   ]     # стенды
  122 [branch    ]     if stand_wavs:
  123 [loop      ]         for name, path in stand_wavs.items():
  124 [code      ]             dst = outd / f"{name}_master.wav"
  125 [branch    ]             if Path(path).exists() and _safe_copy(path, str(dst)):
  126 [code      ]                 files.append(dst.name)
  127 [branch    ]             else:
  128 [code      ]                 warnings.append(f"stand {name}: not found {path}")
  129 [blank     ] 
  130 [comment   ]     # tiktok cuts
  131 [branch    ]     if tiktok_wavs:
  132 [code      ]         tt_dir = outd / "tiktok"
  133 [code      ]         tt_dir.mkdir(parents=True, exist_ok=True)
  134 [loop      ]         for name, path in tiktok_wavs.items():
  135 [code      ]             dst = tt_dir / f"{name}.wav"
  136 [branch    ]             if Path(path).exists() and _safe_copy(path, str(dst)):
  137 [code      ]                 files.append(f"tiktok/{dst.name}")
  138 [branch    ]             else:
  139 [code      ]                 warnings.append(f"tiktok {name}: not found {path}")
  140 [blank     ] 
  141 [comment   ]     # README
  142 [code      ]     payload = {
  143 [code      ]         **project_meta,
  144 [code      ]         "hit_score": (hit_report or {}).get("hit_score"),
  145 [code      ]         "hit_verdict": (hit_report or {}).get("verdict"),
  146 [code      ]         "files": files,
  147 [code      ]     }
  148 [code      ]     (outd / "README_RELEASE.txt").write_text(_readme_text(payload), encoding="utf-8")
  149 [code      ]     files.append("README_RELEASE.txt")
  150 [blank     ] 
  151 [return    ]     return {
  152 [code      ]         "ok": True,
  153 [code      ]         "release_dir": str(outd),
  154 [code      ]         "n_files_added": len(files),
  155 [code      ]         "files": files,
  156 [code      ]         "warnings": warnings,
  157 [code      ]     }
  158 [blank     ] 
  159 [blank     ] 
  160 [branch    ] if __name__ == "__main__":
  161 [import    ]     import sys
  162 [blank     ] 
  163 [branch    ]     if len(sys.argv) < 2:
  164 [code      ]         print("usage: python release_pack_v9.py <release_dir>")
  165 [code      ]         sys.exit(1)
  166 [code      ]     r = build_release_v9(
  167 [code      ]         sys.argv[1],
  168 [code      ]         project_meta={
  169 [code      ]             "artist": "test",
  170 [code      ]             "title": "demo",
  171 [code      ]             "bpm": 132,
  172 [code      ]             "key": "F",
  173 [code      ]             "mode": "minor",
  174 [code      ]             "genre": "phonk",
  175 [code      ]             "mood": "moody",
  176 [code      ]             "duration_s": 150,
  177 [code      ]         },
  178 [code      ]         master_wav="/tmp/none.wav",
  179 [code      ]     )
  180 [code      ]     print(json.dumps(r, indent=2))
```