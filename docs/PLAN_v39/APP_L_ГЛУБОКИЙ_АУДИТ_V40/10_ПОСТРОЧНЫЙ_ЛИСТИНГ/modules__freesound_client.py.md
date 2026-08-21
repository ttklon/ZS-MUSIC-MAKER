# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/freesound_client.py`

**Всего строк:** 200

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 100 | 50.0 |
| blank | 24 | 12.0 |
| docstring | 22 | 11.0 |
| branch | 13 | 6.5 |
| return | 12 | 6.0 |
| import | 10 | 5.0 |
| try_block | 8 | 4.0 |
| def | 5 | 2.5 |
| loop | 3 | 1.5 |
| comment | 2 | 1.0 |
| stmt | 1 | 0.5 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v10 — Freesound API Client
    3 [docstring ] =========================================
    4 [docstring ] Прямой клиент Freesound.org (ТЗ 3.3).
    5 [blank     ] 
    6 [docstring ] БЕСПЛАТНЫЙ (нужен только API-key, регистрация free forever).
    7 [docstring ] Фильтрация по:
    8 [docstring ]   - жанру, BPM, тональности, настроению, лицензии CC0/CC-BY
    9 [docstring ]   - формату (wav, flac)
   10 [docstring ]   - длительности
   11 [blank     ] 
   12 [docstring ] Работает и офлайн — если API-key не указан или сеть недоступна,
   13 [docstring ] переключается на локальный кэш `samples_cache/`.
   14 [docstring ] """
   15 [blank     ] 
   16 [import    ] from __future__ import annotations
   17 [blank     ] 
   18 [import    ] import hashlib
   19 [import    ] import json
   20 [import    ] import logging
   21 [import    ] import os
   22 [import    ] import time
   23 [import    ] from pathlib import Path
   24 [import    ] from typing import Any
   25 [blank     ] 
   26 [code      ] log = logging.getLogger("zsmm.freesound")
   27 [blank     ] 
   28 [try_block ] try:
   29 [import    ]     import requests
   30 [try_block ] except Exception:
   31 [code      ]     requests = None
   32 [blank     ] 
   33 [code      ] FS_ENDPOINT = "https://freesound.org/apiv2/search/text/"
   34 [code      ] FS_DOWNLOAD = "https://freesound.org/apiv2/sounds/{sid}/download/"
   35 [blank     ] 
   36 [code      ] CC0_LICENSES = ("Creative Commons 0", "cc0", "Public Domain")
   37 [code      ] CCBY_LICENSES = ("Attribution", "cc-by")
   38 [blank     ] 
   39 [code      ] DEFAULT_CACHE = Path("samples_cache")
   40 [code      ] DEFAULT_MANIFEST = Path("data/sample_manifests/freesound_cache.json")
   41 [blank     ] 
   42 [blank     ] 
   43 [def       ] def _load_key() -> str | None:
   44 [comment   ]     # 1) ENV
   45 [code      ]     k = os.environ.get("FREESOUND_API_KEY")
   46 [branch    ]     if k:
   47 [return    ]         return k.strip()
   48 [comment   ]     # 2) config file
   49 [code      ]     cfg = Path("data/freesound.key")
   50 [branch    ]     if cfg.exists():
   51 [return    ]         return cfg.read_text(encoding="utf-8").strip()
   52 [return    ]     return None
   53 [blank     ] 
   54 [blank     ] 
   55 [def       ] def search(
   56 [code      ]     query: str,
   57 [code      ]     bpm_min: int | None = None,
   58 [code      ]     bpm_max: int | None = None,
   59 [code      ]     duration_max: float = 20.0,
   60 [code      ]     license_only_cc0: bool = True,
   61 [code      ]     page_size: int = 20,
   62 [code      ] ) -> dict[str, Any]:
   63 [docstring ]     """
   64 [docstring ]     Ищет сэмплы. Всегда возвращает dict {ok, results, offline?}
   65 [docstring ]     """
   66 [code      ]     api_key = _load_key()
   67 [branch    ]     if not (requests and api_key):
   68 [code      ]         log.info("Freesound offline mode (no key or no requests)")
   69 [return    ]         return _offline_search(query)
   70 [blank     ] 
   71 [code      ]     filt_parts = [f"duration:[0 TO {duration_max}]"]
   72 [branch    ]     if bpm_min and bpm_max:
   73 [code      ]         filt_parts.append(f"bpm:[{bpm_min} TO {bpm_max}]")
   74 [branch    ]     if license_only_cc0:
   75 [code      ]         filt_parts.append('license:"Creative Commons 0"')
   76 [blank     ] 
   77 [code      ]     params = {
   78 [code      ]         "query": query,
   79 [code      ]         "filter": " ".join(filt_parts),
   80 [code      ]         "fields": "id,name,tags,previews,license,duration,bpm,username,download",
   81 [code      ]         "page_size": page_size,
   82 [code      ]         "token": api_key,
   83 [code      ]     }
   84 [try_block ]     try:
   85 [code      ]         r = requests.get(FS_ENDPOINT, params=params, timeout=15)
   86 [branch    ]         if r.status_code != 200:
   87 [code      ]             log.warning("Freesound %s: %s", r.status_code, r.text[:200])
   88 [return    ]             return _offline_search(query)
   89 [code      ]         data = r.json()
   90 [code      ]         results = []
   91 [loop      ]         for item in data.get("results", []):
   92 [code      ]             results.append(
   93 [code      ]                 {
   94 [code      ]                     "id": item.get("id"),
   95 [code      ]                     "name": item.get("name"),
   96 [code      ]                     "tags": item.get("tags", []),
   97 [code      ]                     "license": item.get("license"),
   98 [code      ]                     "duration": item.get("duration"),
   99 [code      ]                     "bpm": item.get("bpm"),
  100 [code      ]                     "author": item.get("username"),
  101 [code      ]                     "preview_mp3": (item.get("previews") or {}).get("preview-hq-mp3"),
  102 [code      ]                     "preview_ogg": (item.get("previews") or {}).get("preview-hq-ogg"),
  103 [code      ]                     "source": "freesound",
  104 [code      ]                 }
  105 [code      ]             )
  106 [return    ]         return {"ok": True, "count": len(results), "results": results, "offline": False}
  107 [try_block ]     except Exception as e:
  108 [code      ]         log.warning("Freesound exception: %s", e)
  109 [return    ]         return _offline_search(query)
  110 [blank     ] 
  111 [blank     ] 
  112 [def       ] def _offline_search(query: str) -> dict[str, Any]:
  113 [docstring ]     """
  114 [docstring ]     Возвращает то что уже лежит в samples_cache — по подстроке в имени.
  115 [docstring ]     """
  116 [branch    ]     if not DEFAULT_CACHE.exists():
  117 [return    ]         return {"ok": True, "count": 0, "results": [], "offline": True}
  118 [code      ]     q = query.lower()
  119 [code      ]     out = []
  120 [loop      ]     for p in DEFAULT_CACHE.rglob("*.wav"):
  121 [branch    ]         if q in p.name.lower():
  122 [code      ]             out.append(
  123 [code      ]                 {
  124 [code      ]                     "id": hashlib.md5(str(p).encode()).hexdigest()[:8],
  125 [code      ]                     "name": p.name,
  126 [code      ]                     "local_path": str(p),
  127 [code      ]                     "source": "local_cache",
  128 [code      ]                     "license": "unknown",
  129 [code      ]                 }
  130 [code      ]             )
  131 [loop      ]     for p in DEFAULT_CACHE.rglob("*.mp3"):
  132 [branch    ]         if q in p.name.lower():
  133 [code      ]             out.append(
  134 [code      ]                 {
  135 [code      ]                     "id": hashlib.md5(str(p).encode()).hexdigest()[:8],
  136 [code      ]                     "name": p.name,
  137 [code      ]                     "local_path": str(p),
  138 [code      ]                     "source": "local_cache",
  139 [code      ]                     "license": "unknown",
  140 [code      ]                 }
  141 [code      ]             )
  142 [return    ]     return {"ok": True, "count": len(out), "results": out, "offline": True}
  143 [blank     ] 
  144 [blank     ] 
  145 [def       ] def download_preview(
  146 [code      ]     item: dict[str, Any], dest_dir: str = "samples_cache"
  147 [code      ] ) -> str | None:
  148 [docstring ]     """
  149 [docstring ]     Скачивает preview mp3/ogg (доступен без auth).
  150 [docstring ]     Полный wav требует OAuth (пропускаем — используем preview).
  151 [docstring ]     """
  152 [code      ]     url = item.get("preview_mp3") or item.get("preview_ogg")
  153 [branch    ]     if not url or not requests:
  154 [return    ]         return item.get("local_path")
  155 [code      ]     Path(dest_dir).mkdir(parents=True, exist_ok=True)
  156 [code      ]     ext = ".mp3" if item.get("preview_mp3") else ".ogg"
  157 [code      ]     safe_name = f"fs_{item['id']}_{int(time.time())}{ext}"
  158 [code      ]     out = Path(dest_dir) / safe_name
  159 [try_block ]     try:
  160 [code      ]         r = requests.get(url, timeout=30, stream=True)
  161 [branch    ]         if r.status_code == 200:
  162 [stmt      ]             with open(out, "wb") as f:
  163 [code      ]                 f.writelines(r.iter_content(8192))
  164 [code      ]             _append_manifest(item, str(out))
  165 [return    ]             return str(out)
  166 [try_block ]     except Exception as e:
  167 [code      ]         log.warning("download error: %s", e)
  168 [return    ]     return None
  169 [blank     ] 
  170 [blank     ] 
  171 [def       ] def _append_manifest(item: dict[str, Any], local_path: str) -> None:
  172 [code      ]     DEFAULT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
  173 [code      ]     manifest = []
  174 [branch    ]     if DEFAULT_MANIFEST.exists():
  175 [try_block ]         try:
  176 [code      ]             manifest = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
  177 [try_block ]         except Exception:
  178 [code      ]             manifest = []
  179 [code      ]     manifest.append(
  180 [code      ]         {
  181 [code      ]             "id": item.get("id"),
  182 [code      ]             "name": item.get("name"),
  183 [code      ]             "license": item.get("license"),
  184 [code      ]             "author": item.get("author"),
  185 [code      ]             "local_path": local_path,
  186 [code      ]             "downloaded_at": int(time.time()),
  187 [code      ]             "source": "freesound",
  188 [code      ]         }
  189 [code      ]     )
  190 [code      ]     DEFAULT_MANIFEST.write_text(
  191 [code      ]         json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
  192 [code      ]     )
  193 [blank     ] 
  194 [blank     ] 
  195 [branch    ] if __name__ == "__main__":
  196 [import    ]     import sys
  197 [blank     ] 
  198 [code      ]     q = sys.argv[1] if len(sys.argv) > 1 else "trap 808 kick"
  199 [code      ]     res = search(q, bpm_min=120, bpm_max=160, duration_max=5.0)
  200 [code      ]     print(json.dumps(res, ensure_ascii=False, indent=2)[:2000])
```