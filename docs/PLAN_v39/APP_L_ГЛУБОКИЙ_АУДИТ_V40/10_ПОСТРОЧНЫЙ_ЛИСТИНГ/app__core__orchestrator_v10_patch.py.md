# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/core/orchestrator_v10_patch.py`

**Всего строк:** 226

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 99 | 43.8 |
| blank | 42 | 18.6 |
| try_block | 30 | 13.3 |
| import | 17 | 7.5 |
| comment | 16 | 7.1 |
| docstring | 15 | 6.6 |
| def | 2 | 0.9 |
| return | 2 | 0.9 |
| branch | 2 | 0.9 |
| class | 1 | 0.4 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v10 — Orchestrator Patch
    3 [docstring ] =========================================
    4 [docstring ] Подключает новые модули v10 к существующему оркестратору,
    5 [docstring ] не удаляя ничего из v7/v8/v9.
    6 [blank     ] 
    7 [docstring ] Порядок применения патчей: v7 base → v8 patch → v9 patch → v10 patch.
    8 [docstring ] """
    9 [blank     ] 
   10 [import    ] from __future__ import annotations
   11 [blank     ] 
   12 [import    ] import json
   13 [import    ] import logging
   14 [import    ] import time
   15 [import    ] from pathlib import Path
   16 [import    ] from typing import Any
   17 [blank     ] 
   18 [code      ] log = logging.getLogger("zsmm.orchestrator_v10")
   19 [blank     ] 
   20 [code      ] VERSION = "v10.0.0-chart-killer-pro"
   21 [blank     ] 
   22 [blank     ] 
   23 [def       ] def apply_v10_patch(orchestrator: Any) -> dict[str, Any]:
   24 [docstring ]     """
   25 [docstring ]     Регистрирует новые стадии v10 в оркестраторе.
   26 [docstring ]     """
   27 [code      ]     added = []
   28 [blank     ] 
   29 [comment   ]     # 1. Essentia advanced analyzer
   30 [try_block ]     try:
   31 [import    ]         from modules import essentia_analyzer
   32 [blank     ] 
   33 [code      ]         orchestrator.essentia = essentia_analyzer
   34 [code      ]         added.append("essentia_analyzer")
   35 [try_block ]     except Exception as e:
   36 [code      ]         log.warning("essentia_analyzer patch skipped: %s", e)
   37 [blank     ] 
   38 [comment   ]     # 2. Freesound client
   39 [try_block ]     try:
   40 [import    ]         from modules import freesound_client
   41 [blank     ] 
   42 [code      ]         orchestrator.freesound = freesound_client
   43 [code      ]         added.append("freesound_client")
   44 [try_block ]     except Exception as e:
   45 [code      ]         log.warning("freesound_client patch skipped: %s", e)
   46 [blank     ] 
   47 [comment   ]     # 3. Matchering wrapper
   48 [try_block ]     try:
   49 [import    ]         from modules import matchering_master
   50 [blank     ] 
   51 [code      ]         orchestrator.matchering = matchering_master
   52 [code      ]         added.append("matchering_master")
   53 [try_block ]     except Exception as e:
   54 [code      ]         log.warning("matchering_master patch skipped: %s", e)
   55 [blank     ] 
   56 [comment   ]     # 4. Cover art
   57 [try_block ]     try:
   58 [import    ]         from modules import cover_art_gen
   59 [blank     ] 
   60 [code      ]         orchestrator.cover_gen = cover_art_gen
   61 [code      ]         added.append("cover_art_gen")
   62 [try_block ]     except Exception as e:
   63 [code      ]         log.warning("cover_art_gen patch skipped: %s", e)
   64 [blank     ] 
   65 [comment   ]     # 5. Phoneme coverage
   66 [try_block ]     try:
   67 [import    ]         from modules import phoneme_coverage
   68 [blank     ] 
   69 [code      ]         orchestrator.phoneme_cov = phoneme_coverage
   70 [code      ]         added.append("phoneme_coverage")
   71 [try_block ]     except Exception as e:
   72 [code      ]         log.warning("phoneme_coverage patch skipped: %s", e)
   73 [blank     ] 
   74 [comment   ]     # 6. DirectML detector
   75 [try_block ]     try:
   76 [import    ]         from modules import hw_directml
   77 [blank     ] 
   78 [code      ]         orchestrator.hw_directml = hw_directml
   79 [code      ]         prof = hw_directml.save_profile()
   80 [code      ]         orchestrator.hw_v10 = prof
   81 [code      ]         added.append(f"hw_directml({prof.get('backend')})")
   82 [try_block ]     except Exception as e:
   83 [code      ]         log.warning("hw_directml patch skipped: %s", e)
   84 [blank     ] 
   85 [comment   ]     # 7. Anti-neuro polish v10
   86 [try_block ]     try:
   87 [import    ]         from modules import anti_neuro_v10
   88 [blank     ] 
   89 [code      ]         orchestrator.anti_neuro_v10 = anti_neuro_v10
   90 [code      ]         added.append("anti_neuro_v10")
   91 [try_block ]     except Exception as e:
   92 [code      ]         log.warning("anti_neuro_v10 patch skipped: %s", e)
   93 [blank     ] 
   94 [comment   ]     # 8. Lyric Vault v10
   95 [try_block ]     try:
   96 [import    ]         from modules import lyric_vault_v10
   97 [blank     ] 
   98 [code      ]         orchestrator.lyric_vault_v10 = lyric_vault_v10
   99 [code      ]         added.append("lyric_vault_v10")
  100 [try_block ]     except Exception as e:
  101 [code      ]         log.warning("lyric_vault_v10 patch skipped: %s", e)
  102 [blank     ] 
  103 [comment   ]     # 9. Karaoke engine
  104 [try_block ]     try:
  105 [import    ]         from modules import karaoke_engine
  106 [blank     ] 
  107 [code      ]         orchestrator.karaoke_v10 = karaoke_engine
  108 [code      ]         added.append("karaoke_engine")
  109 [try_block ]     except Exception as e:
  110 [code      ]         log.warning("karaoke_engine patch skipped: %s", e)
  111 [blank     ] 
  112 [comment   ]     # 10. Onboarding tour
  113 [try_block ]     try:
  114 [import    ]         from modules import onboarding_tour
  115 [blank     ] 
  116 [code      ]         orchestrator.tour = onboarding_tour
  117 [code      ]         added.append("onboarding_tour")
  118 [try_block ]     except Exception as e:
  119 [code      ]         log.warning("onboarding_tour patch skipped: %s", e)
  120 [blank     ] 
  121 [code      ]     log.info("v10 patch applied: %s", added)
  122 [return    ]     return {"ok": True, "version": VERSION, "added": added, "count": len(added)}
  123 [blank     ] 
  124 [blank     ] 
  125 [def       ] def full_v10_pipeline(
  126 [code      ]     orchestrator: Any,
  127 [code      ]     project_id: str,
  128 [code      ]     vocal_wav: str,
  129 [code      ]     beat_wav: str,
  130 [code      ]     reference_wav: str | None = None,
  131 [code      ]     polish_preset: str = "standard",
  132 [code      ]     track_title: str = "Untitled",
  133 [code      ]     artist: str = "ZS",
  134 [code      ] ) -> dict[str, Any]:
  135 [docstring ]     """
  136 [docstring ]     Оркестрирует полный v10 pipeline после v9-стадий.
  137 [docstring ]       → anti_neuro_v10 → matchering (car/club/streaming/tiktok) →
  138 [docstring ]         cover_art_gen → phoneme_cov update
  139 [docstring ]     """
  140 [code      ]     project_dir = Path("output/projects") / project_id / "release"
  141 [code      ]     project_dir.mkdir(parents=True, exist_ok=True)
  142 [code      ]     steps = {}
  143 [blank     ] 
  144 [comment   ]     # 1. Anti-neuro polish v10
  145 [code      ]     polished = str(project_dir / "vocal_polished_v10.wav")
  146 [try_block ]     try:
  147 [code      ]         r = orchestrator.anti_neuro_v10.polish_vocal(
  148 [code      ]             vocal_wav, polished, preset=polish_preset
  149 [code      ]         )
  150 [code      ]         steps["anti_neuro_v10"] = r
  151 [try_block ]     except Exception as e:
  152 [code      ]         steps["anti_neuro_v10"] = {"ok": False, "reason": str(e)}
  153 [blank     ] 
  154 [comment   ]     # 2. Mixdown (использует существующий mixdown.py)
  155 [try_block ]     try:
  156 [import    ]         from modules import mixdown
  157 [blank     ] 
  158 [code      ]         mix_out = str(project_dir / "master.wav")
  159 [code      ]         mixdown.mix(
  160 [code      ]             beat_wav, polished if Path(polished).exists() else vocal_wav, mix_out
  161 [code      ]         )
  162 [code      ]         steps["mixdown"] = {"ok": True, "out": mix_out}
  163 [try_block ]     except Exception as e:
  164 [code      ]         steps["mixdown"] = {"ok": False, "reason": str(e)}
  165 [code      ]         mix_out = beat_wav
  166 [blank     ] 
  167 [comment   ]     # 3. Matchering stands
  168 [code      ]     stands_dir = str(project_dir / "stands")
  169 [try_block ]     try:
  170 [branch    ]         if reference_wav and Path(reference_wav).exists():
  171 [code      ]             r_ref = orchestrator.matchering.match_to_reference(
  172 [code      ]                 mix_out, reference_wav, str(project_dir / "master_matched.wav")
  173 [code      ]             )
  174 [code      ]             steps["matchering_ref"] = r_ref
  175 [code      ]         r_stands = orchestrator.matchering.master_all_stands(mix_out, stands_dir)
  176 [code      ]         steps["stands"] = r_stands
  177 [try_block ]     except Exception as e:
  178 [code      ]         steps["stands"] = {"ok": False, "reason": str(e)}
  179 [blank     ] 
  180 [comment   ]     # 4. Cover art
  181 [try_block ]     try:
  182 [code      ]         cover_out = str(project_dir / "cover.png")
  183 [code      ]         r_cov = orchestrator.cover_gen.generate(
  184 [code      ]             track_title, artist, cover_out, style="neon"
  185 [code      ]         )
  186 [code      ]         steps["cover"] = r_cov
  187 [try_block ]     except Exception as e:
  188 [code      ]         steps["cover"] = {"ok": False, "reason": str(e)}
  189 [blank     ] 
  190 [comment   ]     # 5. Phoneme coverage refresh
  191 [try_block ]     try:
  192 [code      ]         steps["phoneme_coverage"] = orchestrator.phoneme_cov.compute_coverage()
  193 [try_block ]     except Exception as e:
  194 [code      ]         steps["phoneme_coverage"] = {"ok": False, "reason": str(e)}
  195 [blank     ] 
  196 [comment   ]     # 6. Release-manifest v10
  197 [code      ]     manifest = {
  198 [code      ]         "version": VERSION,
  199 [code      ]         "project_id": project_id,
  200 [code      ]         "artist": artist,
  201 [code      ]         "title": track_title,
  202 [code      ]         "generated_at": int(time.time()),
  203 [code      ]         "polish_preset": polish_preset,
  204 [code      ]         "steps": {k: v.get("ok", False) for k, v in steps.items()},
  205 [code      ]     }
  206 [code      ]     (project_dir / "manifest_v10.json").write_text(
  207 [code      ]         json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
  208 [code      ]     )
  209 [code      ]     steps["manifest"] = {"ok": True, "path": str(project_dir / "manifest_v10.json")}
  210 [blank     ] 
  211 [return    ]     return {
  212 [code      ]         "ok": True,
  213 [code      ]         "version": VERSION,
  214 [code      ]         "project_dir": str(project_dir),
  215 [code      ]         "steps": steps,
  216 [code      ]     }
  217 [blank     ] 
  218 [blank     ] 
  219 [branch    ] if __name__ == "__main__":
  220 [blank     ] 
  221 [class     ]     class Dummy:
  222 [code      ]         pass
  223 [blank     ] 
  224 [code      ]     d = Dummy()
  225 [code      ]     r = apply_v10_patch(d)
  226 [code      ]     print(json.dumps(r, ensure_ascii=False, indent=2))
```