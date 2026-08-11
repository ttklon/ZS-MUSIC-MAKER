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


def scout_trends(query: str, max_results: int = 10) -> list:
    """
    Ищет актуальные тренды и сленг по теме.
    Возвращает список выражений/фраз.
    """
    cache = _load_cache()
    cache_key = query.lower().strip()

    # Проверяем кэш (не старше 24 часов)
    if cache_key in cache:
        entry = cache[cache_key]
        if time.time() - entry.get("ts", 0) < 86400:
            return entry.get("trends", [])

    trends = []

    # 1. DuckDuckGo (простой HTML-парсинг)
    try:
        trends.extend(_duckduckgo_search(f"{query} тренд сленг 2026"))
    except Exception:
        pass

    # 2. Дополняем локальным словарём
    try:
        from modules.lyrics_gen import load_slang_dictionary

        trends.extend(load_slang_dictionary()[:10])
    except Exception:
        pass

    # 3. Стандартные хайповые фразы (fallback)
    if not trends:
        trends = _fallback_trends(query)

    # Дедупликация
    trends = list(dict.fromkeys(trends))[:max_results]

    # Кэшируем
    cache[cache_key] = {"trends": trends, "ts": time.time()}
    _save_cache(cache)

    return trends


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


def get_hot_topics() -> list:
    """Возвращает актуальные горячие темы для треков."""
    cache = _load_cache()
    if "hot_topics" in cache and time.time() - cache["hot_topics"].get("ts", 0) < 86400:
        return cache["hot_topics"].get("topics", [])

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

    # Пробуем найти актуальные тренды в интернете
    try:
        online = _duckduckgo_search("тrend music tiktok 2026")
        if online:
            topics = online[:4] + topics
    except Exception:
        pass

    cache["hot_topics"] = {"topics": topics, "ts": time.time()}
    _save_cache(cache)
    return topics


if __name__ == "__main__":
    print(json.dumps(scout_trends("phonk drift"), ensure_ascii=False, indent=2))
