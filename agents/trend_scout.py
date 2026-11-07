"""
agents/trend_scout.py — актуальный сленг, темы и хайп-слова на день создания трека.

Бывший `trend_scout.py` (v2: тренды в интернете) и `trend_scout_v3.py`
(словарь 2026 + Reddit + готовый отчёт под тему) слиты в один модуль.

Источники (все бесплатные, без ключей): DuckDuckGo HTML, Reddit (r/rap_ru,
r/hiphopheads), локальный `lyric_vault/slang.txt` и встроенный офлайн-словарь.
Любая сетевая ошибка превращается в диагностику + честный локальный fallback —
никаких «live»-заявлений без реального ответа. Кэш — 24 часа.
"""

from __future__ import annotations

import json
import random
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE_FILE = ROOT / "lyric_vault" / "trends_cache.json"
SLANG_FILE = ROOT / "lyric_vault" / "slang.txt"
USER_AGENT = "Mozilla/5.0 (Windows NT 11.0; Win64; x64) ZSMusicMaker/41.0"

# ---------------------------------------------------------------- офлайн-база
FALLBACK_2026: dict[str, list[str]] = {
    "hype_words": [
        "залетело", "имба", "база", "кринж", "флекс", "движ", "качает",
        "поднимает", "по кайфу", "на волне", "в теме", "разрыв", "убойный",
        "огонь", "краш", "хайп", "чек", "тэйк", "мув", "ноу-мув", "вайб",
        "стайл", "флоу", "дроп", "рил", "фит", "коллаб", "фитбэк", "релевант",
        "жирный", "тухлый", "жёсткий", "мощный",
    ],
    "punchlines_ru": [
        "деньги — фон, я — сюжет",
        "город спит, а мой мотор рычит",
        "я не в чарте, я — сам чарт",
        "фонк в тачке, лето в глазах",
        "молчание в кэше, крик в припеве",
        "рил про меня, ты — фильтр",
        "мы не эдит, мы — оригинал",
        "мой трек — твоя пятница",
        "супра шепчет ночь моя",
        "стамбул, чай, движ, вайб",
    ],
    "hooks_en_2026": [
        "night ride, city lights",
        "money talks, we don't stop",
        "supra vibe, drift on repeat",
        "summer heat, no defeat",
        "istanbul, we ride tonight",
        "living fast, we don't crash",
        "diamonds shine, we don't blind",
        "on the wave, misbehave",
    ],
    "brand_names": [
        "Supra", "AMG", "GT-R", "Skyline", "M5", "Camry", "Prado", "BMW",
        "Mercedes", "Toyota", "Nissan", "Balenciaga", "Off-White", "Rolex",
        "AP", "Rimowa", "Dior", "Nike TN",
    ],
    "city_names": [
        "Стамбул", "Дубай", "Москва", "Питер", "Казань", "Сочи", "Анталия",
        "Босфор", "Кемер", "Тбилиси", "Ереван", "Алматы",
    ],
    "themes_2026": [
        "летний драйв на юге",
        "ночная гонка в неоне",
        "трекера залетевший тикток",
        "верность района",
        "первый чек",
        "разлука на границе",
        "тачка как второе имя",
        "клуб / вечер / друзья",
    ],
}

HOT_TOPICS_BUILTIN = [
    "лето, море, тачки, движение",
    "ночной город, неон, флекс",
    "деньги, успех, подъём",
    "Турция, Стамбул, отдых",
    "район, пацаны, верность",
    "любовь, краш, чувства",
    "трэп, тёмный вайб, 808",
    "TikTok тренд, залетевший хук",
]


# --------------------------------------------------------------------------- #
#  Кэш
# --------------------------------------------------------------------------- #
def _load_cache() -> dict:
    if not CACHE_FILE.exists():
        return {}
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_cache(data: dict) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# --------------------------------------------------------------------------- #
#  Онлайн-источники
# --------------------------------------------------------------------------- #
def _http_text(url: str, timeout: float = 8.0) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="ignore")


def _duckduckgo_search(query: str, max_results: int = 5) -> list[str]:
    """DuckDuckGo HTML: чистые сниппеты 15–200 символов."""
    html = _http_text("https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query))
    snippets = re.findall(r'result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)
    out: list[str] = []
    for raw in snippets:
        text = re.sub(r"<[^>]+>", "", raw)
        text = re.sub(r"\s+", " ", text).strip()
        if 15 <= len(text) <= 200:
            out.append(text)
        if len(out) >= max_results:
            break
    return out


def _reddit_hot(subreddit: str, limit: int = 10) -> list[str]:
    """Горячие заголовки сабреддита (без авторизации)."""
    payload = json.loads(
        _http_text(f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}")
    )
    out: list[str] = []
    for post in payload.get("data", {}).get("children", []):
        title = post.get("data", {}).get("title", "").strip()
        if 10 <= len(title) <= 200:
            out.append(title)
    return out


def _load_local_slang(path=None) -> list[str]:
    """Прочитать пользовательский словарь сленга (`lyric_vault/slang.txt`).

    Строки-комментарии (`#`) и пустые строки игнорируются, дубликаты
    схлопываются с сохранением порядка. Файл не обязателен: отсутствие —
    нормальное состояние, о котором сообщает диагностика.
    """
    target = path or SLANG_FILE
    text = Path(target).read_text(encoding="utf-8")
    seen: list[str] = []
    for line in text.splitlines():
        entry = line.strip()
        if not entry or entry.startswith("#"):
            continue
        if entry not in seen:
            seen.append(entry)
    return seen


def _fallback_trends(query: str) -> list[str]:
    """Офлайн-словарь, если сеть недоступна."""
    return list(FALLBACK_2026["hype_words"]) + list(FALLBACK_2026["punchlines_ru"])


# --------------------------------------------------------------------------- #
#  Тренды под запрос
# --------------------------------------------------------------------------- #
def scout_trends_with_diagnostics(query: str, max_results: int = 10) -> dict:
    """Тренды + происхождение источника без ложных заявлений о live-данных."""
    cache = _load_cache()
    cache_key = (query or "").lower().strip()
    entry = cache.get(cache_key)
    if entry and time.time() - entry.get("ts", 0) < 86400:
        return {
            "trends": entry.get("trends", [])[:max_results],
            "source": "cache",
            "diagnostics": [],
        }

    trends: list[str] = []
    diagnostics: list[dict] = []

    try:
        trends.extend(_duckduckgo_search(f"{query} тренд сленг {time.strftime('%Y')}"))
    except Exception as exc:  # noqa: BLE001 - диагностика вместо падения
        diagnostics.append(
            {"source": "duckduckgo", "ok": False, "error": f"{type(exc).__name__}: {exc}"}
        )

    try:
        trends.extend(_load_local_slang()[:10])
    except Exception as exc:  # noqa: BLE001 - причина видна в диагностике
        diagnostics.append(
            {"source": "local_slang", "ok": False, "error": f"{type(exc).__name__}: {exc}"}
        )

    source = "live_or_local"
    if not trends:
        trends = _fallback_trends(query)
        source = "built_in_fallback"

    trends = list(dict.fromkeys(trends))[:max_results]
    cache[cache_key] = {"trends": trends, "ts": time.time()}
    _save_cache(cache)
    return {"trends": trends, "source": source, "diagnostics": diagnostics}


def scout_trends(query: str, max_results: int = 10) -> list[str]:
    """list-API для существующих вызовов."""
    return scout_trends_with_diagnostics(query, max_results)["trends"]


def get_hot_topics_with_diagnostics() -> dict:
    """Горячие темы: онлайн-сниппеты + встроенный список, с диагностикой."""
    cache = _load_cache()
    cached = cache.get("hot_topics")
    if cached and time.time() - cached.get("ts", 0) < 86400:
        return {"topics": cached.get("topics", []), "source": "cache", "diagnostics": []}

    topics = list(HOT_TOPICS_BUILTIN)
    diagnostics: list[dict] = []
    source = "built_in"
    try:
        online = _duckduckgo_search(f"trend music tiktok {time.strftime('%Y')}")
        if online:
            topics = online[:4] + topics
            source = "live_plus_built_in"
    except Exception as exc:  # noqa: BLE001
        diagnostics.append(
            {"source": "duckduckgo", "ok": False, "error": f"{type(exc).__name__}: {exc}"}
        )

    cache["hot_topics"] = {"topics": topics, "ts": time.time()}
    _save_cache(cache)
    return {"topics": topics, "source": source, "diagnostics": diagnostics}


def get_hot_topics() -> list[str]:
    return get_hot_topics_with_diagnostics()["topics"]


# --------------------------------------------------------------------------- #
#  Готовый отчёт под тему (для генератора текстов)
# --------------------------------------------------------------------------- #
def scout(theme: str, offline_only: bool = False) -> dict:
    """Полный набор материалов под тему: слова, панчлайны, хуки, бренды, города."""
    year = time.strftime("%Y")
    cache_key = f"{(theme or '').lower().strip()}|{year}"
    cache = _load_cache()
    cached = cache.get(cache_key)
    if cached and time.time() - cached.get("ts", 0) < 86400:
        return cached["data"]

    result: dict = {
        "hype_words": list(FALLBACK_2026["hype_words"]),
        "punchlines": list(FALLBACK_2026["punchlines_ru"]),
        "hooks_en": list(FALLBACK_2026["hooks_en_2026"]),
        "brands": list(FALLBACK_2026["brand_names"]),
        "cities": list(FALLBACK_2026["city_names"]),
        "themes": list(FALLBACK_2026["themes_2026"]),
        "external_snippets": [],
        "updated_ts": time.time(),
        "year": year,
    }

    if not offline_only:
        snippets: list[str] = []
        for query in (
            f"{theme} тренд {year} тикток",
            f"{theme} сленг {year}",
            f"tiktok music trend {year} phonk",
        ):
            try:
                snippets.extend(_duckduckgo_search(query, max_results=3))
            except Exception:
                continue
        for subreddit in ("rap_ru", "hiphopheads"):
            try:
                snippets.extend(_reddit_hot(subreddit, 5))
            except Exception:
                continue
        result["external_snippets"] = list(
            dict.fromkeys(item for item in snippets if item.strip())
        )[:20]

    cache[cache_key] = {"ts": time.time(), "data": result}
    _save_cache(cache)
    return result


def actual_slang_for_prompt(theme: str, n_words: int = 20) -> list[str]:
    """Пачка «модных сейчас» слов под тему для промпта генерации текста."""
    report = scout(theme)
    pool = (
        report["hype_words"]
        + [word for word in report["brands"] if len(word) <= 12]
        + report["cities"]
    )
    random.shuffle(pool)
    return pool[:n_words]


if __name__ == "__main__":
    import sys

    theme = sys.argv[1] if len(sys.argv) > 1 else "лето тачки"
    print(json.dumps(scout(theme, offline_only=True), ensure_ascii=False, indent=2))
