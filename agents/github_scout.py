# -*- coding: utf-8 -*-
"""
ZS Music Maker v15 — agents/github_scout.py
====================================================
TZ раздел 47: автоматический поиск новых GitHub-репозиториев
для внедрения. Работает через GitHub REST API (без токена — anon,
60 req/hour). Умеет кэшировать результаты в data/github_cache.json.

Ищет по темам:
  - RVC (voice conversion)
  - MusicGen / audiocraft
  - Demucs / stem separation
  - Sample packs CC0
  - Mastering (pedalboard / matchering)
  - Hit prediction
  - Text-to-Speech (XTTS / Bark)

Возвращает список репозиториев с полями:
  {name, full_name, url, description, stars, updated, topic,
   is_new_since_last_scan}
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

try:
    import requests
    HAS_REQ = True
except Exception:
    HAS_REQ = False

ROOT = Path(__file__).resolve().parents[1]
CACHE_FILE = ROOT / "data" / "github_cache.json"
CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)


TOPICS = [
    ("rvc voice conversion", "rvc"),
    ("musicgen audiocraft", "musicgen"),
    ("demucs stem separation", "demucs"),
    ("cc0 sample pack music", "samples"),
    ("pedalboard mastering audio", "mastering"),
    ("hit prediction popularity music", "hit_score"),
    ("xtts bark text-to-speech", "tts"),
    ("directml onnx audio", "accel"),
    ("faster-whisper", "stt"),
    ("free music dataset", "dataset"),
]


def search_github(query: str, per_page: int = 5,
                  timeout: float = 10.0) -> List[Dict[str, Any]]:
    if not HAS_REQ:
        return []
    try:
        r = requests.get("https://api.github.com/search/repositories",
                         params={"q": query, "sort": "stars",
                                 "order": "desc", "per_page": per_page},
                         headers={"Accept": "application/vnd.github+json"},
                         timeout=timeout)
        if r.status_code != 200:
            return [{"error": f"http_{r.status_code}", "query": query}]
        items = r.json().get("items", [])
        return [{
            "name": it["name"],
            "full_name": it["full_name"],
            "url": it["html_url"],
            "description": (it.get("description") or "")[:200],
            "stars": it["stargazers_count"],
            "updated": it["updated_at"],
            "language": it.get("language"),
        } for it in items]
    except Exception as e:
        return [{"error": type(e).__name__, "query": query}]


def load_cache() -> Dict[str, Any]:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_cache(cache: Dict[str, Any]):
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2),
                          encoding="utf-8")


def scan(offline_fallback: bool = True) -> Dict[str, Any]:
    """Основной entry-point. Возвращает {scanned_at, topics: {topic: [repos]},
    new_repos: [...], errors: [...]}"""
    cache = load_cache()
    seen: set = set()
    for repos in cache.get("topics", {}).values():
        for r in repos:
            if "full_name" in r:
                seen.add(r["full_name"])
    out: Dict[str, Any] = {"scanned_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                            "topics": {}, "new_repos": [], "errors": [],
                            "offline_fallback": False}
    for query, topic in TOPICS:
        results = search_github(query)
        if results and results[0].get("error"):
            out["errors"].append(results[0])
            # если API недоступен — offline mode
            if offline_fallback and results[0].get("error", "").startswith("Con"):
                out["offline_fallback"] = True
                out["topics"][topic] = cache.get("topics", {}).get(topic, [])
                continue
        # marks new
        for r in results:
            if r.get("full_name") and r["full_name"] not in seen:
                r["is_new_since_last_scan"] = True
                out["new_repos"].append({"topic": topic, **r})
            elif r.get("full_name"):
                r["is_new_since_last_scan"] = False
        out["topics"][topic] = results
    save_cache(out)
    return out


# ---------- предзаписанный список обязательных репо (TZ 48) ----------
MANDATORY_REPOS = [
    {"name": "Applio", "full_name": "IAHispano/Applio",
     "url": "https://github.com/IAHispano/Applio",
     "reason": "RVC форк с DirectML/AMD поддержкой",
     "topic": "rvc"},
    {"name": "audiocraft", "full_name": "facebookresearch/audiocraft",
     "url": "https://github.com/facebookresearch/audiocraft",
     "reason": "MusicGen (текстуры)", "topic": "musicgen"},
    {"name": "demucs", "full_name": "facebookresearch/demucs",
     "url": "https://github.com/facebookresearch/demucs",
     "reason": "Стемы (4-stem)", "topic": "demucs"},
    {"name": "matchering", "full_name": "sergree/matchering",
     "url": "https://github.com/sergree/matchering",
     "reason": "Matchering 2.0 — мастеринг под референс",
     "topic": "mastering"},
    {"name": "pedalboard", "full_name": "spotify/pedalboard",
     "url": "https://github.com/spotify/pedalboard",
     "reason": "Реальный sidechain-compressor и мастер-цепь",
     "topic": "mastering"},
    {"name": "faster-whisper",
     "full_name": "SYSTRAN/faster-whisper",
     "url": "https://github.com/SYSTRAN/faster-whisper",
     "reason": "Быстрый Whisper для караоке-wordmap", "topic": "stt"},
    {"name": "TTS", "full_name": "coqui-ai/TTS",
     "url": "https://github.com/coqui-ai/TTS",
     "reason": "XTTS-v2 (TTS + голосовое клонирование)", "topic": "tts"},
    {"name": "bark", "full_name": "suno-ai/bark",
     "url": "https://github.com/suno-ai/bark",
     "reason": "Bark TTS с эмоциями", "topic": "tts"},
    {"name": "silero-models", "full_name": "snakers4/silero-models",
     "url": "https://github.com/snakers4/silero-models",
     "reason": "Легковесный TTS для Lite-профиля", "topic": "tts"},
    {"name": "rnnoise", "full_name": "xiph/rnnoise",
     "url": "https://github.com/xiph/rnnoise",
     "reason": "Шумоподавление для микрофонных записей", "topic": "denoise"},
    {"name": "onnxruntime-directml",
     "full_name": "microsoft/onnxruntime",
     "url": "https://github.com/microsoft/onnxruntime",
     "reason": "DirectML для AMD/Windows", "topic": "accel"},
]


def get_mandatory_repos() -> List[Dict[str, Any]]:
    return MANDATORY_REPOS


if __name__ == "__main__":
    import sys
    if "--mandatory" in sys.argv:
        print(json.dumps(get_mandatory_repos(), ensure_ascii=False, indent=2))
    else:
        # Быстрый offline тест (без реального API)
        result = scan(offline_fallback=True)
        # Ограничить вывод, чтобы не флудить
        preview = {
            "scanned_at": result["scanned_at"],
            "topics_count": len(result["topics"]),
            "new_repos_count": len(result["new_repos"]),
            "errors_count": len(result["errors"]),
            "offline_fallback": result["offline_fallback"],
            "sample_new": result["new_repos"][:3],
            "cache_file": str(CACHE_FILE),
        }
        print(json.dumps(preview, ensure_ascii=False, indent=2))
