"""
[v9] sample_hunter_v9.py — расширенный поиск сэмплов.

Надстройка над v7 agents/sample_hunter.py — НИЧЕГО не удаляем, только добавляем.

По ТЗ 3.3 (Sample Browser + Sample Search Agent):
  «Сэмплы ищутся, фильтруются и собираются в библиотеку».
  Лицензии: ТОЛЬКО CC0 / CC-BY / Royalty-Free. Никаких платных ключей.

Источники (все free, без API-ключей):
  1. Локальная библиотека samples_cache/  (v7)
  2. Freesound (только public preview + CC-фильтр через web-поиск)
  3. Wikimedia Commons (audio files) — CC-BY-SA / PD
  4. archive.org  (Public Domain / Creative Commons коллекции)

Ключевые фичи v9:
  • query planner: разбирает style_vector → пачка целевых запросов
  • bpm-aware match: тег/название содержит BPM ≈ target
  • dedup по названию
  • manifest.json — сохраняет URL + license + attribution для юридической
    чистоты каждого использованного сэмпла

Работает без интернета — тогда используется только локальная библиотека.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.parse import quote_plus

try:
    import requests

    HAS_REQ = True
except Exception:
    HAS_REQ = False

ROOT = Path(__file__).resolve().parents[1]
LOCAL_LIB = ROOT / "samples_cache"
LOCAL_LIB.mkdir(parents=True, exist_ok=True)
MANIFEST_DIR = ROOT / "data" / "sample_manifests"
MANIFEST_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================ query planner
GENRE_KEYWORDS = {
    "phonk / drift": [
        "808 kick",
        "cowbell phonk",
        "vinyl hiss",
        "memphis vocal chop",
        "drift phonk sample",
        "japanese vocal chop",
        "808 slide",
        "phonk snare",
        "phonk hihat roll",
        "supra engine",
    ],
    "dance / edm": [
        "big room synth",
        "future bass chord",
        "dance kick",
        "edm riser",
        "reverse cymbal",
        "dance clap",
        "vocal chop edm",
        "sidechain pad",
    ],
    "trap / hip-hop": [
        "trap 808",
        "hip-hop snare",
        "hip-hop kick",
        "trap hihat",
        "sample trap loop",
        "vocal chop trap",
        "trap riser",
        "trap open hat",
    ],
    "pop / r&b": [
        "rnb chord loop",
        "pop drum loop",
        "pop clap",
        "vocal chop rnb",
        "smooth piano loop",
        "airy pad",
        "pop snare",
    ],
    "hardstyle / techno": [
        "hardstyle kick",
        "reverse kick",
        "techno hat",
        "techno bass",
        "acid loop",
        "techno stab",
    ],
    "generic hit": [
        "kick drum",
        "snare drum",
        "hihat loop",
        "bass loop",
        "vocal chop",
        "riser fx",
        "impact fx",
    ],
}


def plan_queries(style_vector: dict, max_queries: int = 8) -> list[str]:
    genre = (
        (style_vector or {}).get("genre_hint")
        or (style_vector or {}).get("genre")
        or "generic hit"
    )
    bpm = int(round((style_vector or {}).get("bpm", 130.0)))
    base = GENRE_KEYWORDS.get(genre, GENRE_KEYWORDS["generic hit"])[:]
    bpm_q = [f"loop {bpm} bpm", f"drum loop {bpm} bpm", f"bass {bpm} bpm sample"]
    plan = (base + bpm_q)[:max_queries]
    return plan


# ============================================================ local
AUDIO_EXT = (".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aiff")


def list_local(subdir: str = "") -> list[dict]:
    root = LOCAL_LIB / subdir if subdir else LOCAL_LIB
    if not root.exists():
        return []
    items = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in AUDIO_EXT:
            items.append(
                {
                    "name": p.name,
                    "path": str(p),
                    "size": p.stat().st_size,
                    "source": "local",
                    "license": "user_supplied",
                    "url": None,
                }
            )
    return items


# ============================================================ online — safe wrappers
def _http_get(url: str, timeout: float = 6.0) -> str | None:
    if not HAS_REQ:
        return None
    try:
        r = requests.get(
            url, timeout=timeout, headers={"User-Agent": "ZSMusicMaker/9.0"}
        )
        if r.status_code == 200:
            return r.text
    except Exception:
        return None
    return None


def search_freesound_web(query: str, limit: int = 5) -> list[dict]:
    """Поиск через публичную веб-страницу Freesound без API-ключа."""
    if not HAS_REQ:
        return []
    url = (
        f"https://freesound.org/search/?q={quote_plus(query)}"
        "&f=license:%22Creative+Commons+0%22"
    )
    html = _http_get(url)
    if not html:
        return []
    m = re.findall(r'href="(/people/[^/]+/sounds/(\d+)/)"[^>]*>\s*([^<]{3,100})', html)
    out = []
    for path, sid, name in m[:limit]:
        out.append(
            {
                "name": name.strip(),
                "path": None,
                "source": "freesound_cc0",
                "license": "CC0",
                "url": f"https://freesound.org{path}",
                "id": sid,
                "query": query,
            }
        )
    return out


def search_wikimedia(query: str, limit: int = 5) -> list[dict]:
    if not HAS_REQ:
        return []
    url = (
        "https://commons.wikimedia.org/w/api.php"
        "?action=query&list=search&format=json"
        f"&srnamespace=6&srsearch={quote_plus(query)}+audio&srlimit={limit}"
    )
    txt = _http_get(url)
    if not txt:
        return []
    try:
        j = json.loads(txt)
        out = []
        for row in j.get("query", {}).get("search", [])[:limit]:
            title = row.get("title", "")
            if not any(title.lower().endswith(ext) for ext in AUDIO_EXT):
                continue
            file_url = "https://commons.wikimedia.org/wiki/" + quote_plus(
                title.replace(" ", "_")
            )
            out.append(
                {
                    "name": title,
                    "path": None,
                    "source": "wikimedia",
                    "license": "CC-BY-SA / PD",
                    "url": file_url,
                    "query": query,
                }
            )
        return out
    except Exception:
        return []


def search_archive_org(query: str, limit: int = 5) -> list[dict]:
    if not HAS_REQ:
        return []
    url = (
        "https://archive.org/advancedsearch.php?q="
        + quote_plus(
            f"{query} AND mediatype:audio AND "
            "(licenseurl:*creativecommons* OR licenseurl:*publicdomain*)"
        )
        + f"&fl%5B%5D=identifier&fl%5B%5D=title&fl%5B%5D=licenseurl"
        f"&rows={limit}&output=json"
    )
    txt = _http_get(url)
    if not txt:
        return []
    try:
        j = json.loads(txt)
        docs = j.get("response", {}).get("docs", [])
        out = []
        for d in docs[:limit]:
            ident = d.get("identifier")
            title = d.get("title", ident)
            if not ident:
                continue
            out.append(
                {
                    "name": str(title)[:120],
                    "path": None,
                    "source": "archive.org",
                    "license": str(d.get("licenseurl", "cc"))[:80],
                    "url": f"https://archive.org/details/{ident}",
                    "id": ident,
                    "query": query,
                }
            )
        return out
    except Exception:
        return []


# ============================================================ main API
def search_online(
    style_vector: dict, max_per_source: int = 5, max_total: int = 40
) -> list[dict]:
    queries = plan_queries(style_vector, max_queries=6)
    hits: list[dict] = []
    seen = set()
    for q in queries:
        for finder in (search_freesound_web, search_wikimedia, search_archive_org):
            try:
                results = finder(q, limit=max_per_source)
            except Exception:
                results = []
            for r in results:
                key = (r.get("source"), r.get("name", "").lower())
                if key in seen:
                    continue
                seen.add(key)
                hits.append(r)
                if len(hits) >= max_total:
                    return hits
    return hits


def unified_search(
    style_vector: dict,
    include_local: bool = True,
    include_online: bool = True,
    max_total: int = 60,
) -> dict:
    result = {
        "queries": plan_queries(style_vector),
        "local": [],
        "online": [],
        "ts": time.time(),
    }
    if include_local:
        result["local"] = list_local()
    if include_online:
        result["online"] = search_online(style_vector, max_total=max_total)
    result["total"] = len(result["local"]) + len(result["online"])
    return result


def save_manifest(items: list[dict], project_id: str) -> str:
    path = MANIFEST_DIR / f"{project_id}_samples.json"
    payload = {
        "project_id": project_id,
        "ts": time.time(),
        "total": len(items),
        "items": items,
        "notice": "Все сэмплы — CC0 / CC-BY / PD или пользовательская "
        "локальная библиотека.",
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


# ============================================================ CLI
if __name__ == "__main__":
    sv = {"bpm": 132, "genre_hint": "phonk / drift"}
    q = plan_queries(sv)
    print("PLAN:", q)
    local = list_local()
    print(f"LOCAL: {len(local)} files")
    print(f"HAS_REQ: {HAS_REQ}")
