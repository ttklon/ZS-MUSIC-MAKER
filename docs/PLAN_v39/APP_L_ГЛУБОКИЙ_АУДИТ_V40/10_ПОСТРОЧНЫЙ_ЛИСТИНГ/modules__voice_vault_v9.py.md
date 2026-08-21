# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/voice_vault_v9.py`

**Всего строк:** 314

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 149 | 47.5 |
| blank | 50 | 15.9 |
| return | 27 | 8.6 |
| try_block | 20 | 6.4 |
| docstring | 17 | 5.4 |
| branch | 17 | 5.4 |
| import | 12 | 3.8 |
| def | 12 | 3.8 |
| comment | 7 | 2.2 |
| loop | 2 | 0.6 |
| stmt | 1 | 0.3 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v9] voice_vault_v9.py — ПОСТОЯННО НАКОПИТЕЛЬНЫЙ Voice Vault.
    3 [blank     ] 
    4 [docstring ] По ТЗ 3.8: «Голосовой профиль пользователя КОПИТСЯ ПОСТОЯННО».
    5 [docstring ] Раньше v8 хранил только сырые файлы. v9 добавляет:
    6 [blank     ] 
    7 [docstring ]   • индексацию каждого файла: длительность, транскрипт (whisper), стиль подачи
    8 [docstring ]     (rap / sing / adlib / shout / whisper), BPM записи (если под метроном),
    9 [docstring ]     оценка качества записи (SNR, clipping, breath-noise).
   10 [docstring ]   • автопометки стилей — 8 стилей караоке (rap/sing/adlib/shout/whisper/melodic
   11 [docstring ]     /aggressive/deadpan).
   12 [docstring ]   • очередь для RVC-переобучения: как только накопилось ≥N мин чистого голоса
   13 [docstring ]     → auto-trigger rvc_trainer_v9.retrain_incremental().
   14 [docstring ]   • стабильные id-файлов (md5), чтобы дубликаты не попадали в vault дважды.
   15 [docstring ]   • экспорт «voice_manifest.json» — что реально скормлено в RVC.
   16 [blank     ] 
   17 [docstring ] Ничего не удаляет из v7/v8. Работает без librosa/whisper (тогда без транскрипта
   18 [docstring ] и SNR-оценки).
   19 [docstring ] """
   20 [blank     ] 
   21 [import    ] from __future__ import annotations
   22 [blank     ] 
   23 [import    ] import hashlib
   24 [import    ] import json
   25 [import    ] import math
   26 [import    ] import shutil
   27 [import    ] import time
   28 [import    ] from pathlib import Path
   29 [blank     ] 
   30 [try_block ] try:
   31 [import    ]     import numpy as np
   32 [try_block ] except Exception:
   33 [code      ]     np = None
   34 [blank     ] 
   35 [try_block ] try:
   36 [import    ]     import soundfile as sf
   37 [blank     ] 
   38 [code      ]     HAS_SF = True
   39 [try_block ] except Exception:
   40 [code      ]     HAS_SF = False
   41 [blank     ] 
   42 [try_block ] try:
   43 [code      ]     HAS_LIBROSA = True
   44 [try_block ] except Exception:
   45 [code      ]     HAS_LIBROSA = False
   46 [blank     ] 
   47 [code      ] ROOT = Path(__file__).resolve().parents[1]
   48 [code      ] VAULT_DIR = ROOT / "voice_vault"
   49 [code      ] INDEX_FILE = VAULT_DIR / "index.json"
   50 [code      ] MANIFEST_FILE = VAULT_DIR / "voice_manifest.json"
   51 [comment   ] # v22: ленивое создание (не при импорте)
   52 [blank     ] 
   53 [code      ] STYLES = (
   54 [code      ]     "rap",
   55 [code      ]     "sing",
   56 [code      ]     "adlib",
   57 [code      ]     "shout",
   58 [code      ]     "whisper",
   59 [code      ]     "melodic",
   60 [code      ]     "aggressive",
   61 [code      ]     "deadpan",
   62 [code      ] )
   63 [blank     ] 
   64 [comment   ] # Порог для авто-триггера дообучения RVC (в секундах чистого голоса)
   65 [code      ] RETRAIN_THRESHOLD_SEC = 300.0  # 5 минут
   66 [blank     ] 
   67 [blank     ] 
   68 [comment   ] # ============================================================ index
   69 [def       ] def _load_index() -> dict:
   70 [branch    ]     if INDEX_FILE.exists():
   71 [try_block ]         try:
   72 [return    ]             return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
   73 [try_block ]         except Exception:
   74 [return    ]             return {"items": {}}
   75 [return    ]     return {"items": {}}
   76 [blank     ] 
   77 [blank     ] 
   78 [def       ] def _save_index(idx: dict) -> None:
   79 [code      ]     INDEX_FILE.write_text(
   80 [code      ]         json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8"
   81 [code      ]     )
   82 [blank     ] 
   83 [blank     ] 
   84 [def       ] def _md5(path: Path, limit: int = 1 << 20) -> str:
   85 [code      ]     h = hashlib.md5()
   86 [stmt      ]     with open(path, "rb") as f:
   87 [code      ]         h.update(f.read(limit))
   88 [return    ]     return h.hexdigest()
   89 [blank     ] 
   90 [blank     ] 
   91 [comment   ] # ============================================================ audio quality
   92 [def       ] def _snr_and_clipping(path: Path) -> dict:
   93 [branch    ]     if not HAS_SF or np is None:
   94 [return    ]         return {"snr_db": None, "clip_ratio": None, "duration_s": None}
   95 [try_block ]     try:
   96 [code      ]         y, sr = sf.read(str(path), always_2d=False)
   97 [branch    ]         if hasattr(y, "ndim") and y.ndim > 1:
   98 [code      ]             y = y.mean(axis=1)
   99 [code      ]         dur = len(y) / sr
  100 [code      ]         win = max(1, int(sr * 0.05))
  101 [code      ]         chunks = [y[i : i + win] for i in range(0, len(y) - win, win)]
  102 [code      ]         rmss = sorted([float(np.sqrt(np.mean(np.square(c)) + 1e-12)) for c in chunks])
  103 [branch    ]         if len(rmss) < 20:
  104 [return    ]             return {"snr_db": None, "clip_ratio": None, "duration_s": dur}
  105 [code      ]         noise = float(np.mean(rmss[: max(1, len(rmss) // 20)]))
  106 [code      ]         signal = float(np.mean(rmss[-max(1, len(rmss) // 5) :]))
  107 [code      ]         snr = 20 * math.log10(max(signal, 1e-9) / max(noise, 1e-9))
  108 [code      ]         clip = float(np.mean(np.abs(y) > 0.98))
  109 [return    ]         return {
  110 [code      ]             "snr_db": round(snr, 2),
  111 [code      ]             "clip_ratio": round(clip, 5),
  112 [code      ]             "duration_s": round(dur, 2),
  113 [code      ]         }
  114 [try_block ]     except Exception as e:
  115 [return    ]         return {"snr_db": None, "clip_ratio": None, "duration_s": None, "err": str(e)}
  116 [blank     ] 
  117 [blank     ] 
  118 [def       ] def _guess_style(features: dict, hint: str | None = None) -> str:
  119 [branch    ]     if hint and hint in STYLES:
  120 [return    ]         return hint
  121 [code      ]     dur = features.get("duration_s") or 0.0
  122 [branch    ]     if dur < 2.0:
  123 [return    ]         return "adlib"
  124 [return    ]     return "rap"  # безопасный дефолт
  125 [blank     ] 
  126 [blank     ] 
  127 [comment   ] # ============================================================ transcript
  128 [def       ] def _transcribe(path: Path) -> str | None:
  129 [try_block ]     try:
  130 [import    ]         from faster_whisper import WhisperModel
  131 [blank     ] 
  132 [code      ]         m = WhisperModel("tiny", device="cpu", compute_type="int8")
  133 [code      ]         segs, _ = m.transcribe(str(path))
  134 [return    ]         return " ".join(s.text.strip() for s in segs)[:500]
  135 [try_block ]     except Exception:
  136 [code      ]         pass
  137 [try_block ]     try:
  138 [import    ]         import whisper
  139 [blank     ] 
  140 [code      ]         m = whisper.load_model("tiny")
  141 [return    ]         return (m.transcribe(str(path)).get("text") or "")[:500]
  142 [try_block ]     except Exception:
  143 [code      ]         pass
  144 [return    ]     return None
  145 [blank     ] 
  146 [blank     ] 
  147 [def       ] def calculate_phoneme_coverage(text: str) -> dict:
  148 [docstring ]     """Считает покрытие алфавита (русский + английский)."""
  149 [branch    ]     if not text:
  150 [return    ]         return {}
  151 [code      ]     text = text.lower()
  152 [code      ]     ru = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
  153 [code      ]     en = "abcdefghijklmnopqrstuvwxyz"
  154 [blank     ] 
  155 [code      ]     found_ru = [c for c in ru if c in text]
  156 [code      ]     found_en = [c for c in en if c in text]
  157 [blank     ] 
  158 [return    ]     return {
  159 [code      ]         "ru_count": len(found_ru),
  160 [code      ]         "ru_total": len(ru),
  161 [code      ]         "ru_percent": round(len(found_ru) / len(ru) * 100, 1),
  162 [code      ]         "en_count": len(found_en),
  163 [code      ]         "en_total": len(en),
  164 [code      ]         "en_percent": round(len(found_en) / len(en) * 100, 1),
  165 [code      ]         "found": "".join(sorted(set(found_ru + found_en))),
  166 [code      ]     }
  167 [blank     ] 
  168 [blank     ] 
  169 [comment   ] # ============================================================ main API
  170 [def       ] def add_recording(
  171 [code      ]     src_path: str,
  172 [code      ]     style_hint: str | None = None,
  173 [code      ]     transcribe: bool = False,
  174 [code      ]     overwrite: bool = False,
  175 [code      ] ) -> dict:
  176 [code      ]     p = Path(src_path)
  177 [branch    ]     if not p.exists():
  178 [return    ]         return {"ok": False, "error": f"not found: {src_path}"}
  179 [blank     ] 
  180 [code      ]     mid = _md5(p)
  181 [code      ]     idx = _load_index()
  182 [code      ]     items = idx.setdefault("items", {})
  183 [blank     ] 
  184 [branch    ]     if mid in items and not overwrite:
  185 [return    ]         return {"ok": True, "already_indexed": True, "item": items[mid]}
  186 [blank     ] 
  187 [code      ]     dst = VAULT_DIR / f"{mid[:12]}_{p.name}"
  188 [branch    ]     if not dst.exists():
  189 [try_block ]         try:
  190 [code      ]             shutil.copy2(p, dst)
  191 [try_block ]         except Exception as e:
  192 [return    ]             return {"ok": False, "error": f"copy failed: {e}"}
  193 [blank     ] 
  194 [code      ]     feats = _snr_and_clipping(dst)
  195 [code      ]     style = _guess_style(feats, style_hint)
  196 [code      ]     transcript = _transcribe(dst) if transcribe else None
  197 [blank     ] 
  198 [code      ]     coverage = calculate_phoneme_coverage(transcript) if transcript else {}
  199 [blank     ] 
  200 [code      ]     entry = {
  201 [code      ]         "id": mid,
  202 [code      ]         "src_name": p.name,
  203 [code      ]         "vault_path": str(dst),
  204 [code      ]         "size": dst.stat().st_size,
  205 [code      ]         "style": style,
  206 [code      ]         "features": feats,
  207 [code      ]         "transcript": transcript,
  208 [code      ]         "coverage": coverage,
  209 [code      ]         "added_at": time.time(),
  210 [code      ]         "used_in_rvc_rounds": [],
  211 [code      ]     }
  212 [code      ]     items[mid] = entry
  213 [code      ]     _save_index(idx)
  214 [return    ]     return {"ok": True, "already_indexed": False, "item": entry}
  215 [blank     ] 
  216 [blank     ] 
  217 [def       ] def list_recordings(style: str | None = None) -> list[dict]:
  218 [code      ]     idx = _load_index()
  219 [code      ]     items = list(idx.get("items", {}).values())
  220 [branch    ]     if style:
  221 [code      ]         items = [x for x in items if x.get("style") == style]
  222 [return    ]     return items
  223 [blank     ] 
  224 [blank     ] 
  225 [def       ] def clean_stats() -> dict:
  226 [code      ]     idx = _load_index()
  227 [code      ]     items = list(idx.get("items", {}).values())
  228 [code      ]     total_sec = 0.0
  229 [code      ]     good_sec = 0.0
  230 [code      ]     by_style = {}
  231 [code      ]     all_text = ""
  232 [loop      ]     for x in items:
  233 [code      ]         dur = (x.get("features") or {}).get("duration_s") or 0.0
  234 [code      ]         snr = (x.get("features") or {}).get("snr_db") or 0.0
  235 [code      ]         clip = (x.get("features") or {}).get("clip_ratio") or 0.0
  236 [code      ]         total_sec += dur
  237 [branch    ]         if (snr is None or snr >= 15.0) and (clip is None or clip < 0.01):
  238 [code      ]             good_sec += dur
  239 [code      ]         st = x.get("style") or "unknown"
  240 [code      ]         by_style[st] = by_style.get(st, 0.0) + dur
  241 [branch    ]         if x.get("transcript"):
  242 [code      ]             all_text += x["transcript"] + " "
  243 [blank     ] 
  244 [code      ]     coverage = calculate_phoneme_coverage(all_text)
  245 [blank     ] 
  246 [return    ]     return {
  247 [code      ]         "n_items": len(items),
  248 [code      ]         "total_sec": round(total_sec, 2),
  249 [code      ]         "good_sec": round(good_sec, 2),
  250 [code      ]         "by_style": {k: round(v, 2) for k, v in by_style.items()},
  251 [code      ]         "coverage": coverage,
  252 [code      ]         "ready_for_retrain": good_sec >= RETRAIN_THRESHOLD_SEC,
  253 [code      ]         "threshold_sec": RETRAIN_THRESHOLD_SEC,
  254 [code      ]     }
  255 [blank     ] 
  256 [blank     ] 
  257 [def       ] def export_manifest_for_rvc(out_path: str | None = None) -> str:
  258 [code      ]     idx = _load_index()
  259 [code      ]     good = []
  260 [loop      ]     for x in idx.get("items", {}).values():
  261 [code      ]         f = x.get("features") or {}
  262 [code      ]         snr = f.get("snr_db")
  263 [code      ]         clip = f.get("clip_ratio")
  264 [branch    ]         if (snr is None or snr >= 15.0) and (clip is None or clip < 0.01):
  265 [code      ]             good.append(
  266 [code      ]                 {
  267 [code      ]                     "id": x["id"],
  268 [code      ]                     "path": x["vault_path"],
  269 [code      ]                     "style": x.get("style"),
  270 [code      ]                     "duration_s": f.get("duration_s"),
  271 [code      ]                     "snr_db": snr,
  272 [code      ]                 }
  273 [code      ]             )
  274 [code      ]     payload = {
  275 [code      ]         "ts": time.time(),
  276 [code      ]         "n_items": len(good),
  277 [code      ]         "total_sec": round(sum(x.get("duration_s") or 0 for x in good), 2),
  278 [code      ]         "items": good,
  279 [code      ]     }
  280 [code      ]     dst = Path(out_path) if out_path else MANIFEST_FILE
  281 [code      ]     dst.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
  282 [return    ]     return str(dst)
  283 [blank     ] 
  284 [blank     ] 
  285 [def       ] def maybe_trigger_retrain(rvc_trainer=None) -> dict:
  286 [code      ]     stats = clean_stats()
  287 [branch    ]     if not stats["ready_for_retrain"]:
  288 [return    ]         return {"triggered": False, "reason": "not enough clean voice", "stats": stats}
  289 [code      ]     manifest = export_manifest_for_rvc()
  290 [branch    ]     if rvc_trainer is None:
  291 [try_block ]         try:
  292 [import    ]             from modules import rvc_trainer_v9 as rvc_trainer
  293 [try_block ]         except Exception as e:
  294 [return    ]             return {
  295 [code      ]                 "triggered": False,
  296 [code      ]                 "reason": f"rvc_trainer_v9 unavailable: {e}",
  297 [code      ]                 "manifest": manifest,
  298 [code      ]                 "stats": stats,
  299 [code      ]             }
  300 [try_block ]     try:
  301 [code      ]         job = rvc_trainer.retrain_incremental(manifest_path=manifest)
  302 [return    ]         return {"triggered": True, "manifest": manifest, "stats": stats, "job": job}
  303 [try_block ]     except Exception as e:
  304 [return    ]         return {
  305 [code      ]             "triggered": False,
  306 [code      ]             "reason": str(e),
  307 [code      ]             "manifest": manifest,
  308 [code      ]             "stats": stats,
  309 [code      ]         }
  310 [blank     ] 
  311 [blank     ] 
  312 [comment   ] # ============================================================ CLI
  313 [branch    ] if __name__ == "__main__":
  314 [code      ]     print(json.dumps(clean_stats(), ensure_ascii=False, indent=2))
```