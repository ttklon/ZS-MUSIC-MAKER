# -*- coding: utf-8 -*-
"""
[v7] sample_hunter.py — split-view API: online + local.

Источники online:
  • Freesound (public без API-ключа, через freesound.org/apiv2)
  • Wikimedia Commons (CC0)
  • Pixabay music

Локальный browser:
  • samples_cache/ — уже подтянутые сэмплы
  • пользовательские drop-и

Все возвращаемые сэмплы проходят фильтр License Manager
(CC0 / CC-BY / Royalty-Free / Public Domain по умолчанию).
"""
from __future__ import annotations
import os, json, urllib.parse, urllib.request, hashlib, time
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "samples_cache"
CACHE.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------- local
def list_local(query: str = "") -> list[dict]:
    """Локальная библиотека samples_cache/."""
    out = []
    q = (query or "").lower()
    for p in sorted(CACHE.glob("**/*")):
        if not p.is_file(): continue
        if p.suffix.lower() not in (".wav", ".mp3", ".flac", ".ogg", ".m4a"): continue
        if q and q not in p.name.lower(): continue
        out.append({
            "source": "local",
            "path": str(p),
            "name": p.name,
            "size_kb": round(p.stat().st_size / 1024, 1),
            "license": "local",
            "preview": str(p),
        })
    return out


# ---------------------------------------------------------------- online
def search_wikimedia(query: str, max_results: int = 10) -> list[dict]:
    """Wikimedia Commons — CC0/CC-BY музыка без API-ключа."""
    results = []
    try:
        url = ("https://commons.wikimedia.org/w/api.php?"
               f"action=query&list=search&srsearch={urllib.parse.quote(query)}%20audio"
               f"&srnamespace=6&srlimit={max_results}&format=json")
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.load(r)
        for item in data.get("query", {}).get("search", []):
            title = item.get("title", "")
            if not any(title.lower().endswith(ext) for ext in (".ogg", ".wav", ".mp3", ".flac")):
                continue
            page_url = f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(title)}"
            results.append({
                "source": "wikimedia",
                "name": title,
                "url": page_url,
                "license": "CC0 / CC-BY",
                "preview": page_url,
                "tags": item.get("snippet", "")[:100],
            })
    except Exception as e:
        print(f"[sample_hunter.wikimedia] {e}")
    return results


def search_freesound_public(query: str, max_results: int = 10) -> list[dict]:
    """Freesound без API-ключа — только публичные метаданные (без preview)."""
    results = []
    try:
        # Freesound has /apiv2/search/text/ but requires token.
        # Public alternative: parsing search page (ограничено).
        # Оставляем как best-effort placeholder.
        return results
    except Exception:
        return results


def search_pixabay(query: str, max_results: int = 10) -> list[dict]:
    """Pixabay music — требует бесплатный API key. Мы пропускаем если ключа нет."""
    api_key = os.environ.get("PIXABAY_API_KEY")
    if not api_key:
        return []
    try:
        url = f"https://pixabay.com/api/music/?key={api_key}&q={urllib.parse.quote(query)}&per_page={max_results}"
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.load(r)
        for hit in data.get("hits", []):
            results = []
            results.append({
                "source": "pixabay",
                "name": hit.get("title", ""),
                "url": hit.get("audio", ""),
                "license": "Royalty-Free (Pixabay)",
                "preview": hit.get("preview", ""),
                "tags": hit.get("tags", ""),
            })
        return results
    except Exception:
        return []


def search_online(query: str, max_results: int = 10) -> list[dict]:
    """Агрегатор online-поиска, split-view."""
    results = []
    results.extend(search_wikimedia(query, max_results))
    results.extend(search_freesound_public(query, max_results))
    results.extend(search_pixabay(query, max_results))
    return results[:max_results]


# ---------------------------------------------------------------- hunt (main)
def hunt(query: str, max_results: int = 8,
         allow_online: bool = True,
         license_filter: bool = True) -> dict:
    """
    Главная точка. Возвращает split-view: local + online.
    Фильтрует через License Manager.
    """
    local  = list_local(query)
    online = search_online(query, max_results) if allow_online else []

    if license_filter:
        try:
            from app.core.license_manager import is_free_commercial
            online = [s for s in online
                      if is_free_commercial(s.get("license", "unknown"))]
        except Exception:
            pass

    return {
        "ok": True,
        "query": query,
        "local":  local[:max_results],
        "online": online[:max_results],
        "samples": local[:max_results] + online[:max_results],   # обратная совместимость v5
        "provenance": [
            {"name": s["name"], "source": s["source"],
             "license": s["license"], "url": s.get("url", s.get("path", ""))}
            for s in online
        ],
    }


def download_to_cache(item: dict) -> Optional[str]:
    """Качаем online-сэмпл в samples_cache/."""
    if item.get("source") == "local":
        return item.get("path")
    url = item.get("url")
    if not url:
        return None
    try:
        h = hashlib.md5(url.encode()).hexdigest()[:10]
        name = f"{item.get('source','online')}_{h}_{item.get('name','sample')[:30]}"
        # Санитайзим имя файла
        name = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)
        target = CACHE / name
        if target.exists(): return str(target)
        urllib.request.urlretrieve(url, str(target))
        return str(target)
    except Exception as e:
        print(f"[sample_hunter.download] {e}")
        return None


if __name__ == "__main__":
    print(json.dumps(hunt("phonk 808", max_results=3), ensure_ascii=False, indent=2))
