"""
Agent: TrendScout v2 (НОВЫЙ)
Ищет в интернете тренды, сленг, мемы, популярные выражения.
Источники: DuckDuckGo, Google Trends (опционально), Reddit.
Работает опционально — если интернета нет, возвращает локальный кэш.
"""

import json
import os
import re
import time

import requests

CACHE_FILE = os.path.join(
    os.path.dirname(__file__), "..", "lyric_vault", "trends_cache.json"
)
os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)


def scout_trends_with_diagnostics(query: str, max_results: int = 10) -> dict:
    """Ищет тренды и раскрывает источник либо причину fallback без live-claims."""
    cache = _load_cache()
    cache_key = query.lower().strip()

    # Проверяем кэш (не старше 24 часов)
    if cache_key in cache:
        entry = cache[cache_key]
        if time.time() - entry.get("ts", 0) < 86400:
            return {
                "trends": entry.get("trends", [])[:max_results],
                "source": "cache",
                "diagnostics": [],
            }

    trends = []
    diagnostics = []

    # 1. DuckDuckGo (простой HTML-парсинг)
    try:
        trends.extend(_duckduckgo_search(f"{query} тренд сленг 2026"))
    except Exception as exc:
        diagnostics.append({"source": "duckduckgo", "ok": False, "error": f"{type(exc).__name__}: {exc}"})

    # 2. Дополняем локальным словарём
    try:
        from modules.lyrics_gen import load_slang_dictionary

        trends.extend(load_slang_dictionary()[:10])
    except Exception as exc:
        diagnostics.append({"source": "local_slang", "ok": False, "error": f"{type(exc).__name__}: {exc}"})

    # 3. Стандартные хайповые фразы (fallback)
    source = "live_or_local"
    if not trends:
        trends = _fallback_trends(query)
        source = "built_in_fallback"

    # Дедупликация
    trends = list(dict.fromkeys(trends))[:max_results]

    # Кэшируем
    cache[cache_key] = {"trends": trends, "ts": time.time()}
    _save_cache(cache)
    return {"trends": trends, "source": source, "diagnostics": diagnostics}


def scout_trends(query: str, max_results: int = 10) -> list:
    """Совместимый list API для трендов без изменения существующих callers."""
    return scout_trends_with_diagnostics(query, max_results)["trends"]


def _duckduckgo_search(query: str) -> list:
    """Простой парсинг DuckDuckGo HTML."""
    url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    r = requests.get(url, headers=headers, timeout=10)
    # Извлекаем текст из результатов
    snippets = re.findall(r'class="result__snippet">(.*?)</a>', r.text, re.DOTALL)
    # Очищаем от HTML
    clean = []
    for s in snippets:
        text = re.sub(r"<[^>]+>", "", s).strip()
        if text and len(text) > 10:
            clean.append(text)
    return clean[:5]


def _fallback_trends(query: str) -> list:
    """Локальный fallback если интернет недоступен."""
    return [
        "движ",
        "качает",
        "поднимает",
        "тачка",
        "бабки",
        "лям",
        "движуха",
        "залетело",
        "чек",
        "стайл",
        "флоу",
        "вайб",
        "огонь",
        "краш",
        "флекс",
        "хайп",
        "имба",
        "база",
        "на волне",
        "в теме",
        "по кайфу",
        "разрыв",
        "убойный",
    ]


def _load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        try:
            return json.load(open(CACHE_FILE, encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_cache(data: dict):
    json.dump(
        data, open(CACHE_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2
    )


def get_hot_topics_with_diagnostics() -> dict:
    """Возвращает темы с provenance online-подмешивания без false live-claims."""
    cache = _load_cache()
    if "hot_topics" in cache and time.time() - cache["hot_topics"].get("ts", 0) < 86400:
        return {"topics": cache["hot_topics"].get("topics", []), "source": "cache", "diagnostics": []}

    topics = [
        "лето, море, тачки, движение",
        "ночной город, неон, флекс",
        "деньги, успех, подъём",
        "Турция, Стамбул, отдых",
        "район, пацаны, верность",
        "любовь, краш, чувства",
        "трэп, тёмный вайб, 808",
        "TikTok тренд, залетевший хук",
    ]
    diagnostics = []
    source = "built_in"

    # Пробуем найти актуальные тренды в интернете
    try:
        online = _duckduckgo_search("trend music tiktok 2026")
        if online:
            topics = online[:4] + topics
            source = "live_plus_built_in"
    except Exception as exc:
        diagnostics.append({"source": "duckduckgo", "ok": False, "error": f"{type(exc).__name__}: {exc}"})

    cache["hot_topics"] = {"topics": topics, "ts": time.time()}
    _save_cache(cache)
    return {"topics": topics, "source": source, "diagnostics": diagnostics}


def get_hot_topics() -> list:
    """Совместимый list API для горячих тем."""
    return get_hot_topics_with_diagnostics()["topics"]


if __name__ == "__main__":
    print(json.dumps(scout_trends("phonk drift"), ensure_ascii=False, indent=2))
