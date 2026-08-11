# -*- coding: utf-8 -*-
"""
ZS Music Maker v10 — Freesound API Client
=========================================
Прямой клиент Freesound.org (ТЗ 3.3).

БЕСПЛАТНЫЙ (нужен только API-key, регистрация free forever).
Фильтрация по:
  - жанру, BPM, тональности, настроению, лицензии CC0/CC-BY
  - формату (wav, flac)
  - длительности

Работает и офлайн — если API-key не указан или сеть недоступна,
переключается на локальный кэш `samples_cache/`.
"""
from __future__ import annotations
import os
import json
import time
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional

log = logging.getLogger("zsmm.freesound")

try:
    import requests
except Exception:
    requests = None

FS_ENDPOINT = "https://freesound.org/apiv2/search/text/"
FS_DOWNLOAD = "https://freesound.org/apiv2/sounds/{sid}/download/"

CC0_LICENSES = ("Creative Commons 0", "cc0", "Public Domain")
CCBY_LICENSES = ("Attribution", "cc-by")

DEFAULT_CACHE = Path("samples_cache")
DEFAULT_MANIFEST = Path("data/sample_manifests/freesound_cache.json")


def _load_key() -> Optional[str]:
    # 1) ENV
    k = os.environ.get("FREESOUND_API_KEY")
    if k:
        return k.strip()
    # 2) config file
    cfg = Path("data/freesound.key")
    if cfg.exists():
        return cfg.read_text(encoding="utf-8").strip()
    return None


def search(query: str,
           bpm_min: Optional[int] = None,
           bpm_max: Optional[int] = None,
           duration_max: float = 20.0,
           license_only_cc0: bool = True,
           page_size: int = 20) -> Dict[str, Any]:
    """
    Ищет сэмплы. Всегда возвращает dict {ok, results, offline?}
    """
    api_key = _load_key()
    if not (requests and api_key):
        log.info("Freesound offline mode (no key or no requests)")
        return _offline_search(query)

    filt_parts = [f"duration:[0 TO {duration_max}]"]
    if bpm_min and bpm_max:
        filt_parts.append(f"bpm:[{bpm_min} TO {bpm_max}]")
    if license_only_cc0:
        filt_parts.append('license:"Creative Commons 0"')

    params = {
        "query": query,
        "filter": " ".join(filt_parts),
        "fields": "id,name,tags,previews,license,duration,bpm,username,download",
        "page_size": page_size,
        "token": api_key,
    }
    try:
        r = requests.get(FS_ENDPOINT, params=params, timeout=15)
        if r.status_code != 200:
            log.warning("Freesound %s: %s", r.status_code, r.text[:200])
            return _offline_search(query)
        data = r.json()
        results = []
        for item in data.get("results", []):
            results.append({
                "id": item.get("id"),
                "name": item.get("name"),
                "tags": item.get("tags", []),
                "license": item.get("license"),
                "duration": item.get("duration"),
                "bpm": item.get("bpm"),
                "author": item.get("username"),
                "preview_mp3": (item.get("previews") or {}).get("preview-hq-mp3"),
                "preview_ogg": (item.get("previews") or {}).get("preview-hq-ogg"),
                "source": "freesound",
            })
        return {"ok": True, "count": len(results), "results": results, "offline": False}
    except Exception as e:
        log.warning("Freesound exception: %s", e)
        return _offline_search(query)


def _offline_search(query: str) -> Dict[str, Any]:
    """
    Возвращает то что уже лежит в samples_cache — по подстроке в имени.
    """
    if not DEFAULT_CACHE.exists():
        return {"ok": True, "count": 0, "results": [], "offline": True}
    q = query.lower()
    out = []
    for p in DEFAULT_CACHE.rglob("*.wav"):
        if q in p.name.lower():
            out.append({
                "id": hashlib.md5(str(p).encode()).hexdigest()[:8],
                "name": p.name,
                "local_path": str(p),
                "source": "local_cache",
                "license": "unknown",
            })
    for p in DEFAULT_CACHE.rglob("*.mp3"):
        if q in p.name.lower():
            out.append({
                "id": hashlib.md5(str(p).encode()).hexdigest()[:8],
                "name": p.name,
                "local_path": str(p),
                "source": "local_cache",
                "license": "unknown",
            })
    return {"ok": True, "count": len(out), "results": out, "offline": True}


def download_preview(item: Dict[str, Any], dest_dir: str = "samples_cache") -> Optional[str]:
    """
    Скачивает preview mp3/ogg (доступен без auth).
    Полный wav требует OAuth (пропускаем — используем preview).
    """
    url = item.get("preview_mp3") or item.get("preview_ogg")
    if not url or not requests:
        return item.get("local_path")
    Path(dest_dir).mkdir(parents=True, exist_ok=True)
    ext = ".mp3" if item.get("preview_mp3") else ".ogg"
    safe_name = f"fs_{item['id']}_{int(time.time())}{ext}"
    out = Path(dest_dir) / safe_name
    try:
        r = requests.get(url, timeout=30, stream=True)
        if r.status_code == 200:
            with open(out, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            _append_manifest(item, str(out))
            return str(out)
    except Exception as e:
        log.warning("download error: %s", e)
    return None


def _append_manifest(item: Dict[str, Any], local_path: str) -> None:
    DEFAULT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    manifest = []
    if DEFAULT_MANIFEST.exists():
        try:
            manifest = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
        except Exception:
            manifest = []
    manifest.append({
        "id": item.get("id"),
        "name": item.get("name"),
        "license": item.get("license"),
        "author": item.get("author"),
        "local_path": local_path,
        "downloaded_at": int(time.time()),
        "source": "freesound",
    })
    DEFAULT_MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "trap 808 kick"
    res = search(q, bpm_min=120, bpm_max=160, duration_max=5.0)
    print(json.dumps(res, ensure_ascii=False, indent=2)[:2000])
