# -*- coding: utf-8 -*-
"""
agents/sample_hunter/web.py — бесплатные онлайн-источники сэмплов.

Freesound (публичная страница, CC0), Wikimedia Commons (CC-BY-SA/PD),
archive.org (CC/PD), Pixabay (при наличии бесплатного ключа). Любая ошибка
источника не роняет поиск: источник просто не даёт результатов.
"""

from __future__ import annotations

from urllib.parse import quote_plus

from agents.sample_hunter.config import HAS_REQ, requests


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
