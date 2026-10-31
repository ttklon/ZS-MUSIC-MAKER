"""
agents/sample_hunter.py — единый поиск сэмплов (локальная библиотека + online).

Бывший `sample_hunter.py` (v7) и `sample_hunter_v9.py` слиты в один модуль:
онлайн-источники, query planner, лицензионный gate и manifest жили в v9,
а публичный split-view API (`hunt`, `download_to_cache`) — в v7.

Источники (все бесплатные, без платных ключей):
  1. локальная библиотека `samples_cache/`;
  2. Freesound (публичная страница, только CC0);
  3. Wikimedia Commons (CC-BY-SA / PD);
  4. archive.org (Creative Commons / Public Domain);
  5. Pixabay music (только при наличии бесплатного `PIXABAY_API_KEY`).

Лицензии: в результаты и manifest попадают только CC0 / PD / CC-BY / Royalty-Free.
Все онлайн-хиты проходят `app.core.license_manager.is_free_commercial`; если
валидатор недоступен — поиск **fail closed** (онлайн-результаты отбрасываются).
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from urllib.parse import quote_plus

try:  # сеть опциональна: без requests работает только локальная библиотека
    import requests

    HAS_REQ = True
except Exception:  # pragma: no cover - окружение без requests
    HAS_REQ = False

ROOT = Path(__file__).resolve().parents[1]
LOCAL_LIB = ROOT / "samples_cache"
CACHE = LOCAL_LIB
MANIFEST_DIR = ROOT / "data" / "sample_manifests"

AUDIO_EXT = (".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aiff")

GENRE_KEYWORDS: dict[str, list[str]] = {
    "phonk / drift": [
        "808 kick", "cowbell phonk", "vinyl hiss", "memphis vocal chop",
        "drift phonk sample", "japanese vocal chop", "808 slide", "phonk snare",
        "phonk hihat roll", "supra engine",
    ],
    "dance / edm": [
        "big room synth", "future bass chord", "dance kick", "edm riser",
        "reverse cymbal", "dance clap", "vocal chop edm", "sidechain pad",
    ],
    "trap / hip-hop": [
        "trap 808", "hip-hop snare", "hip-hop kick", "trap hihat",
        "sample trap loop", "vocal chop trap", "trap riser", "trap open hat",
    ],
    "pop / r&b": [
        "rnb chord loop", "pop drum loop", "pop clap", "vocal chop rnb",
        "smooth piano loop", "airy pad", "pop snare",
    ],
    "hardstyle / techno": [
        "hardstyle kick", "reverse kick", "techno hat", "techno bass",
        "acid loop", "techno stab",
    ],
    "generic hit": [
        "kick drum", "snare drum", "hihat loop", "bass loop", "vocal chop",
        "riser fx", "impact fx",
    ],
}


# --------------------------------------------------------------------------- #
#  Query planner
# --------------------------------------------------------------------------- #
def plan_queries(style_vector: dict, max_queries: int = 8) -> list[str]:
    """Разложить style_vector на пачку целевых поисковых запросов."""
    style = style_vector or {}
    genre = style.get("genre_hint") or style.get("genre") or "generic hit"
    bpm = int(round(float(style.get("bpm", 130.0) or 130.0)))
    base = GENRE_KEYWORDS.get(genre, GENRE_KEYWORDS["generic hit"])[:]
    bpm_queries = [f"loop {bpm} bpm", f"drum loop {bpm} bpm", f"bass {bpm} bpm sample"]
    return (base + bpm_queries)[:max_queries]


# --------------------------------------------------------------------------- #
#  Локальная библиотека
# --------------------------------------------------------------------------- #
def list_local(query: str = "") -> list[dict]:
    """Сэмплы пользователя из `samples_cache/` (фильтр по подстроке имени)."""
    if not LOCAL_LIB.exists():
        return []
    needle = (query or "").lower()
    items: list[dict] = []
    for path in sorted(LOCAL_LIB.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in AUDIO_EXT:
            continue
        if needle and needle not in path.name.lower():
            continue
        size_bytes = path.stat().st_size
        items.append(
            {
                "name": path.name,
                "path": str(path),
                "size": size_bytes,
                "size_kb": round(size_bytes / 1024, 1),
                "source": "local",
                "license": "user_supplied",
                "url": None,
            }
        )
    return items


# --------------------------------------------------------------------------- #
#  Онлайн-источники
# --------------------------------------------------------------------------- #
def _http_get(url: str, timeout: float = 6.0) -> str | None:
    if not HAS_REQ:
        return None
    try:
        response = requests.get(
            url, timeout=timeout, headers={"User-Agent": "ZSMusicMaker/41.0"}
        )
        if response.status_code == 200:
            return response.text
    except Exception:
        return None
    return None


def search_freesound_web(query: str, limit: int = 5) -> list[dict]:
    """Freesound без API-ключа: публичная выдача с фильтром CC0."""
    if not HAS_REQ:
        return []
    url = (
        f"https://freesound.org/search/?q={quote_plus(query)}"
        "&f=license:%22Creative+Commons+0%22"
    )
    html = _http_get(url)
    if not html:
        return []
    found = re.findall(r'href="(/people/[^/]+/sounds/(\d+)/)"[^>]*>\s*([^<]{3,100})', html)
    return [
        {
            "name": name.strip(),
            "path": None,
            "source": "freesound_cc0",
            "license": "CC0",
            "url": f"https://freesound.org{path}",
            "id": sound_id,
            "query": query,
        }
        for path, sound_id, name in found[:limit]
    ]


def search_wikimedia(query: str, limit: int = 5) -> list[dict]:
    if not HAS_REQ:
        return []
    url = (
        "https://commons.wikimedia.org/w/api.php"
        "?action=query&list=search&format=json"
        f"&srnamespace=6&srsearch={quote_plus(query)}+audio&srlimit={limit}"
    )
    raw = _http_get(url)
    if not raw:
        return []
    try:
        payload = json.loads(raw)
    except ValueError:
        return []
    out = []
    for row in payload.get("query", {}).get("search", [])[:limit]:
        title = row.get("title", "")
        if not any(title.lower().endswith(ext) for ext in AUDIO_EXT):
            continue
        out.append(
            {
                "name": title,
                "path": None,
                "source": "wikimedia",
                "license": "CC-BY-SA / PD",
                "url": "https://commons.wikimedia.org/wiki/"
                + quote_plus(title.replace(" ", "_")),
                "query": query,
            }
        )
    return out


def search_archive_org(query: str, limit: int = 5) -> list[dict]:
    if not HAS_REQ:
        return []
    url = (
        "https://archive.org/advancedsearch.php?q="
        + quote_plus(
            f"{query} AND mediatype:audio AND "
            "(licenseurl:*creativecommons* OR licenseurl:*publicdomain*)"
        )
        + "&fl%5B%5D=identifier&fl%5B%5D=title&fl%5B%5D=licenseurl"
        f"&rows={limit}&output=json"
    )
    raw = _http_get(url)
    if not raw:
        return []
    try:
        payload = json.loads(raw)
    except ValueError:
        return []
    out = []
    for doc in payload.get("response", {}).get("docs", [])[:limit]:
        identifier = doc.get("identifier")
        if not identifier:
            continue
        out.append(
            {
                "name": str(doc.get("title", identifier))[:120],
                "path": None,
                "source": "archive.org",
                "license": str(doc.get("licenseurl", "cc"))[:80],
                "url": f"https://archive.org/details/{identifier}",
                "id": identifier,
                "query": query,
            }
        )
    return out


def search_pixabay(query: str, limit: int = 5) -> list[dict]:
    """Pixabay music: только при наличии бесплатного ключа."""
    api_key = os.environ.get("PIXABAY_API_KEY")
    if not api_key or not HAS_REQ:
        return []
    url = (
        f"https://pixabay.com/api/music/?key={api_key}"
        f"&q={quote_plus(query)}&per_page={limit}"
    )
    raw = _http_get(url)
    if not raw:
        return []
    try:
        payload = json.loads(raw)
    except ValueError:
        return []
    return [
        {
            "name": hit.get("title", ""),
            "path": None,
            "source": "pixabay",
            "license": "Royalty-Free (Pixabay)",
            "url": hit.get("audio", ""),
            "tags": hit.get("tags", ""),
            "query": query,
        }
        for hit in payload.get("hits", [])[:limit]
    ]


# --------------------------------------------------------------------------- #
#  Лицензионный gate
# --------------------------------------------------------------------------- #
def _license_gate(items: list[dict], allow_user_override: bool = False) -> list[dict]:
    """Пропустить только CC0 / PD / CC-BY / RF. NC/SA/unknown — блокируются."""
    try:
        from app.core.license_manager import is_free_commercial
    except Exception:  # менеджер недоступен — не выдаём непроверенное
        return [item for item in items if item.get("source") == "local"]

    passed: list[dict] = []
    for item in items:
        if item.get("source") == "local":
            passed.append(item)
            continue
        license_name = str(item.get("license", "unknown"))
        if is_free_commercial(license_name, allow_user_override=allow_user_override):
            passed.append(item)
        else:
            item["license_blocked"] = True
            item["license_reason"] = f"blocked by license gate: {license_name}"
    return passed


# --------------------------------------------------------------------------- #
#  Публичный API
# --------------------------------------------------------------------------- #
def search_online(query, limit: int = 10) -> list[dict]:
    """Онлайн-поиск. Принимает строку или style_vector (тогда работает planner)."""
    if isinstance(query, dict):
        queries = plan_queries(query, max_queries=4)
    else:
        queries = [str(query)]
    hits: list[dict] = []
    for text in queries:
        for finder in (search_freesound_web, search_wikimedia, search_archive_org, search_pixabay):
            try:
                hits.extend(finder(text, limit=limit))
            except Exception:
                continue
    return _license_gate(hits)


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
        result["online"] = search_online(style_vector, limit=max_total)
    result["total"] = len(result["local"]) + len(result["online"])
    return result


def hunt(
    query: str,
    max_results: int = 8,
    allow_online: bool = True,
    license_filter: bool = True,
) -> dict:
    """Главная точка: split-view local + online с лицензионным фильтром."""
    local = list_local(query)
    online = search_online(query, limit=max_results) if allow_online else []

    license_status: dict = {"ok": False, "status": "not_requested"}
    if license_filter:
        try:
            from app.core.license_manager import is_free_commercial

            online = [
                sample
                for sample in online
                if is_free_commercial(sample.get("license", "unknown"))
            ]
            license_status = {"ok": True, "status": "applied"}
        except Exception as exc:  # noqa: BLE001 - fail closed by design
            online = []
            license_status = {
                "ok": False,
                "status": "failed_closed",
                "error": f"{type(exc).__name__}: {exc}",
            }

    return {
        "ok": True,
        "query": query,
        "license_filter": license_status,
        "local": local[:max_results],
        "online": online[:max_results],
        "samples": local[:max_results] + online[:max_results],
        "provenance": [
            {
                "name": sample.get("name"),
                "source": sample.get("source"),
                "license": sample.get("license"),
                "url": sample.get("url") or sample.get("path", ""),
            }
            for sample in online
        ],
    }


def download_to_cache(item: dict) -> str | None:
    """Скачать онлайн-сэмпл в `samples_cache/` и вернуть локальный путь."""
    if item.get("source") == "local":
        return item.get("path")
    url = item.get("url")
    if not url:
        return None
    from app.core.security_utils import download_file, safe_hash

    CACHE.mkdir(parents=True, exist_ok=True)
    digest = safe_hash(url)[:10]
    raw_name = f"{item.get('source', 'online')}_{digest}_{item.get('name', 'sample')[:30]}"
    safe_name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in raw_name)
    target = CACHE / safe_name
    if target.exists():
        return str(target)
    if download_file(url, str(target)):
        return str(target)
    return None


def save_manifest(items: list[dict], project_id: str) -> str:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    path = MANIFEST_DIR / f"{project_id}_samples.json"
    payload = {
        "project_id": project_id,
        "ts": time.time(),
        "total": len(items),
        "items": items,
        "notice": "Все сэмплы — CC0 / CC-BY / PD или локальная библиотека пользователя.",
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


if __name__ == "__main__":
    print(json.dumps(hunt("phonk 808", max_results=3), ensure_ascii=False, indent=2))
