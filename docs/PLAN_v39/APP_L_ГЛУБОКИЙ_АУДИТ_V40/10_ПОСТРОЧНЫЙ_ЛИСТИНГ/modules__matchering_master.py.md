# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/matchering_master.py`

**Всего строк:** 133

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 57 | 42.9 |
| docstring | 26 | 19.5 |
| blank | 18 | 13.5 |
| return | 7 | 5.3 |
| import | 6 | 4.5 |
| try_block | 6 | 4.5 |
| branch | 5 | 3.8 |
| def | 4 | 3.0 |
| comment | 3 | 2.3 |
| loop | 1 | 0.8 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v10 — Matchering Mastering Wrapper
    3 [docstring ] ==================================================
    4 [docstring ] Обёртка над Matchering 2.0 (ТЗ 3.11).
    5 [blank     ] 
    6 [docstring ] Подгоняет TARGET под REFERENCE по:
    7 [docstring ]   - RMS / LUFS
    8 [docstring ]   - Спектральной характеристике
    9 [docstring ]   - Стерео-ширине
   10 [docstring ]   - Пиковой амплитуде
   11 [blank     ] 
   12 [docstring ] Если matchering не установлен — делает pydub-fallback:
   13 [docstring ]   - нормализация до -14 LUFS (streaming) / -8.5 LUFS (car) / -6.5 LUFS (club)
   14 [docstring ]   - лёгкая эквализация
   15 [docstring ] """
   16 [blank     ] 
   17 [import    ] from __future__ import annotations
   18 [blank     ] 
   19 [import    ] import logging
   20 [import    ] from pathlib import Path
   21 [import    ] from typing import Any
   22 [blank     ] 
   23 [code      ] log = logging.getLogger("zsmm.matchering")
   24 [blank     ] 
   25 [try_block ] try:
   26 [import    ]     import matchering as mg  # type: ignore
   27 [blank     ] 
   28 [code      ]     MG_OK = True
   29 [try_block ] except Exception:
   30 [code      ]     MG_OK = False
   31 [blank     ] 
   32 [blank     ] 
   33 [def       ] def match_to_reference(
   34 [code      ]     target: str, reference: str, out_wav: str, out_mp3: str | None = None
   35 [code      ] ) -> dict[str, Any]:
   36 [docstring ]     """
   37 [docstring ]     Основная функция: подгонка target под reference.
   38 [docstring ]     """
   39 [code      ]     Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
   40 [branch    ]     if MG_OK:
   41 [try_block ]         try:
   42 [code      ]             mg.log(print)
   43 [code      ]             results = [mg.pcm24(out_wav)]
   44 [branch    ]             if out_mp3:
   45 [code      ]                 results.append(mg.Result(out_mp3, subtype="PCM_16"))
   46 [code      ]             mg.process(target=target, reference=reference, results=results)
   47 [return    ]             return {
   48 [code      ]                 "ok": True,
   49 [code      ]                 "engine": "matchering",
   50 [code      ]                 "out_wav": out_wav,
   51 [code      ]                 "out_mp3": out_mp3,
   52 [code      ]             }
   53 [try_block ]         except Exception as e:
   54 [code      ]             log.warning("Matchering fail, fallback: %s", e)
   55 [return    ]     return {
   56 [code      ]         "ok": False,
   57 [code      ]         "engine": "none",
   58 [code      ]         "reason": "Matchering unavailable or failed; pydub gain is not mastering",
   59 [code      ]         "out_wav": out_wav,
   60 [code      ]     }
   61 [blank     ] 
   62 [blank     ] 
   63 [def       ] def master_to_stand(
   64 [code      ]     target: str, out_wav: str, stand: str = "streaming"
   65 [code      ] ) -> dict[str, Any]:
   66 [docstring ]     """
   67 [docstring ]     Мастер под целевой стенд без референса.
   68 [docstring ]       streaming: -14 LUFS
   69 [docstring ]       car:       -8.5 LUFS (громче, туповатее верх)
   70 [docstring ]       club:      -6.5 LUFS (макс-плотность)
   71 [docstring ]       tiktok:    -13 LUFS
   72 [docstring ]     """
   73 [code      ]     lufs_map = {"streaming": -14.0, "car": -8.5, "club": -6.5, "tiktok": -13.0}
   74 [branch    ]     if not MG_OK:
   75 [return    ]         return {
   76 [code      ]             "ok": False,
   77 [code      ]             "engine": "none",
   78 [code      ]             "stand": stand,
   79 [code      ]             "reason": "Matchering unavailable; refusing gain-only mastering",
   80 [code      ]             "out_wav": out_wav,
   81 [code      ]         }
   82 [return    ]     return _pydub_fallback(
   83 [code      ]         target, out_wav, target_lufs=lufs_map.get(stand, -14.0), stand=stand
   84 [code      ]     )
   85 [blank     ] 
   86 [blank     ] 
   87 [def       ] def master_all_stands(target: str, out_dir: str) -> dict[str, Any]:
   88 [docstring ]     """
   89 [docstring ]     Генерирует 4 версии: streaming / car / club / tiktok.
   90 [docstring ]     """
   91 [code      ]     Path(out_dir).mkdir(parents=True, exist_ok=True)
   92 [code      ]     out = {}
   93 [loop      ]     for stand in ("streaming", "car", "club", "tiktok"):
   94 [code      ]         out_wav = str(Path(out_dir) / f"{stand}_master.wav")
   95 [code      ]         res = master_to_stand(target, out_wav, stand)
   96 [code      ]         out[stand] = res
   97 [return    ]     return {"ok": True, "stands": out}
   98 [blank     ] 
   99 [blank     ] 
  100 [def       ] def _pydub_fallback(
  101 [code      ]     target: str, out_wav: str, target_lufs: float = -14.0, stand: str = "streaming"
  102 [code      ] ) -> dict[str, Any]:
  103 [try_block ]     try:
  104 [import    ]         from pydub import AudioSegment
  105 [blank     ] 
  106 [code      ]         seg = AudioSegment.from_file(target)
  107 [comment   ]         # приближение LUFS = dBFS - 3 (грубая оценка для музыки)
  108 [code      ]         cur_dbfs = seg.dBFS
  109 [code      ]         approx_lufs = cur_dbfs - 3.0
  110 [code      ]         gain = target_lufs - approx_lufs
  111 [comment   ]         # ограничим ±20 дБ чтобы не порвать
  112 [code      ]         gain = max(-20.0, min(20.0, gain))
  113 [code      ]         seg = seg.apply_gain(gain)
  114 [comment   ]         # клубный стенд — лёгкий пик-лимитер
  115 [branch    ]         if stand == "club":
  116 [code      ]             seg = seg.compress_dynamic_range(threshold=-6.0, ratio=4.0)
  117 [code      ]         Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
  118 [code      ]         seg.export(out_wav, format="wav")
  119 [return    ]         return {
  120 [code      ]             "ok": True,
  121 [code      ]             "engine": "pydub_fallback",
  122 [code      ]             "out_wav": out_wav,
  123 [code      ]             "gain_applied_db": round(gain, 2),
  124 [code      ]             "target_lufs": target_lufs,
  125 [code      ]             "stand": stand,
  126 [code      ]         }
  127 [try_block ]     except Exception as e:
  128 [code      ]         log.error("pydub fallback error: %s", e)
  129 [return    ]         return {"ok": False, "reason": str(e)}
  130 [blank     ] 
  131 [blank     ] 
  132 [branch    ] if __name__ == "__main__":
  133 [code      ]     print("Matchering available:", MG_OK)
```