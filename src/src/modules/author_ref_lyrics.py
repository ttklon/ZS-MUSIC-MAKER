"""
[v8] author_ref_lyrics.py — Author-Referenced Lyrics Engine.

Реализация ТЗ 20.3, пункт «Темы: тренды + пользователь»:

  «Возможность, чтобы все треки, которые я загрузил (в библиотеку) использовались
   для написания новых текстов. Берётся 500 треков или все → на основе них + ИИ
   + словарь + поисковик трендов составляются реально крутые тексты.
   Я могу задать тему, слова, ВЫБРАТЬ АВТОРА ИЗ РЕФЕРЕНСОВ, чтобы именно в его
   стиле всё писалось, или написать автора в поиске — программа сама найдёт
   все треки автора для референса.»

Модуль:
  • Индексирует всю библиотеку lyric_vault + references/*.mp3 (через whisper).
  • Строит стилевой профиль автора: n-граммы, любимые слова, ритм слогов, темы.
  • При запросе автора в интернете — ищет тексты через DuckDuckGo/Genius/Lyrics.fandom.
  • Отдаёт «стилевой промт» для lyrics_gen (Ollama/fallback).
  • Полностью офлайн-совместим: если интернета нет — работает по локальному корпусу.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = ROOT / "lyric_vault" / "author_corpus"
STYLE_DIR = ROOT / "lyric_vault" / "author_styles"
CACHE_FILE = ROOT / "lyric_vault" / "author_index.json"
for p in (CORPUS_DIR, STYLE_DIR):
    p.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------- utils
_WORD_RE = re.compile(r"[а-яА-Яёa-zA-Z0-9']+")
_STOPWORDS = {
    "и",
    "а",
    "но",
    "или",
    "что",
    "как",
    "это",
    "то",
    "же",
    "бы",
    "не",
    "в",
    "на",
    "с",
    "по",
    "за",
    "из",
    "от",
    "до",
    "у",
    "к",
    "о",
    "об",
    "the",
    "a",
    "an",
    "of",
    "to",
    "and",
    "in",
    "is",
    "it",
    "on",
    "for",
    "my",
    "your",
    "we",
    "you",
    "i",
}


def _tokenize(text: str) -> list[str]:
    return [w.lower() for w in _WORD_RE.findall(text or "")]


def _syllables_ru(word: str) -> int:
    return max(1, sum(1 for ch in word.lower() if ch in "аеёиоуыэюяaeiouy"))


def _load_index() -> dict:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_index(idx: dict) -> None:
    CACHE_FILE.write_text(
        json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ------------------------------------------------------------- ingest
def ingest_lyrics_file(path: str | Path, author: str, title: str = "") -> dict:
    """Кладём один текст в корпус автора. Возвращаем сводку."""
    path = Path(path)
    if not path.exists():
        return {"ok": False, "error": f"file not found: {path}"}
    text = path.read_text(encoding="utf-8", errors="ignore")
    return ingest_lyrics_text(text, author=author, title=title or path.stem)


def ingest_lyrics_text(text: str, author: str, title: str = "") -> dict:
    """Индексируем сырой текст."""
    author_slug = re.sub(r"[^a-zA-Zа-яА-Я0-9]+", "_", (author or "unknown")).lower()
    fname = hashlib.md5(
        (author_slug + "|" + title + "|" + text[:60]).encode()
    ).hexdigest()[:12]
    dst = CORPUS_DIR / author_slug
    dst.mkdir(parents=True, exist_ok=True)
    (dst / f"{fname}.txt").write_text(text, encoding="utf-8")

    idx = _load_index()
    idx.setdefault(author_slug, {"display_name": author, "files": []})
    idx[author_slug]["files"].append(
        {
            "id": fname,
            "title": title,
            "chars": len(text),
            "ts": time.time(),
        }
    )
    _save_index(idx)
    return {"ok": True, "author": author_slug, "id": fname}


def ingest_reference_audio(
    audio_path: str | Path, author: str = "unknown", title: str = ""
) -> dict:
    """Через Whisper вытаскиваем текст из аудио-референса и кладём в корпус."""
    audio_path = Path(audio_path)
    if not audio_path.exists():
        return {"ok": False, "error": "no audio"}
    try:
        import whisper

        model = whisper.load_model("base")
        res = model.transcribe(str(audio_path), fp16=False)
        text = (res.get("text") or "").strip()
        if not text:
            return {"ok": False, "error": "empty transcription"}
        return ingest_lyrics_text(text, author=author, title=title or audio_path.stem)
    except Exception as e:
        return {"ok": False, "error": f"whisper failed: {e}"}


# ------------------------------------------------------------- style profile
def build_style_profile(author: str) -> dict:
    """
    Строим стилевой профиль автора: словарь, ритм слогов, любимые темы, характерные
    n-граммы. Сохраняем в STYLE_DIR/<author>.json.
    """
    author_slug = re.sub(r"[^a-zA-Zа-яА-Я0-9]+", "_", author).lower()
    author_dir = CORPUS_DIR / author_slug
    if not author_dir.exists():
        return {"ok": False, "error": f"нет корпуса для {author}"}

    all_text = ""
    for f in author_dir.glob("*.txt"):
        all_text += "\n" + f.read_text(encoding="utf-8", errors="ignore")

    tokens = _tokenize(all_text)
    if len(tokens) < 5:
        return {"ok": False, "error": "слишком мало данных"}

    counter = Counter(w for w in tokens if w not in _STOPWORDS and len(w) > 2)
    top_words = counter.most_common(80)

    # Биграммы (характерные обороты)
    bigrams = Counter()
    for i in range(len(tokens) - 1):
        a, b = tokens[i], tokens[i + 1]
        if a not in _STOPWORDS and b not in _STOPWORDS:
            bigrams[f"{a} {b}"] += 1
    top_bigrams = [bg for bg, c in bigrams.most_common(30) if c >= 2]

    # Средняя длина строки в слогах
    lines = [l for l in all_text.split("\n") if l.strip()]
    syll_per_line = []
    for line in lines[:400]:
        ws = _tokenize(line)
        if ws:
            syll_per_line.append(sum(_syllables_ru(w) for w in ws))
    avg_syll = round(sum(syll_per_line) / max(1, len(syll_per_line)), 1)

    # Rhyme skeleton: последние слоги последних слов строк
    rhymes = []
    for line in lines[:200]:
        ws = _tokenize(line)
        if ws:
            rhymes.append(ws[-1][-3:])
    rhyme_counter = Counter(rhymes)

    profile = {
        "author": author,
        "author_slug": author_slug,
        "top_words": [{"w": w, "n": n} for w, n in top_words],
        "top_bigrams": top_bigrams,
        "avg_syll_per_line": avg_syll,
        "rhyme_endings": [r for r, _ in rhyme_counter.most_common(20)],
        "sample_lines": [l.strip() for l in lines if 6 <= len(_tokenize(l)) <= 14][:12],
        "corpus_size_chars": len(all_text),
        "built_at": time.time(),
    }
    (STYLE_DIR / f"{author_slug}.json").write_text(
        json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {"ok": True, "profile": profile}


def get_style_profile(author: str) -> dict | None:
    author_slug = re.sub(r"[^a-zA-Zа-яА-Я0-9]+", "_", author).lower()
    f = STYLE_DIR / f"{author_slug}.json"
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            return None
    # Автосборка при первом обращении
    r = build_style_profile(author)
    return r.get("profile") if r.get("ok") else None


# ------------------------------------------------------------- online search
def search_author_online(author: str, max_tracks: int = 20) -> list[dict]:
    """
    Пытаемся найти в интернете тексты треков автора.
    Использует DuckDuckGo html endpoint (без API-ключа).
    Возвращает список {title, url, snippet}.
    """
    import urllib.parse
    import urllib.request

    q = urllib.parse.quote(f"{author} lyrics текст песни")
    url = f"https://html.duckduckgo.com/html/?q={q}"
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            html = r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return [{"error": str(e)}]

    results = []
    for m in re.finditer(
        r'result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?'
        r'result__snippet"[^>]*>(.*?)</a>',
        html,
        re.DOTALL,
    ):
        u, t, s = m.groups()
        title = re.sub(r"<[^>]+>", "", t).strip()
        snip = re.sub(r"<[^>]+>", "", s).strip()
        if title and snip:
            results.append({"title": title, "url": u, "snippet": snip})
        if len(results) >= max_tracks:
            break
    return results


def fetch_and_ingest_author(author: str, max_tracks: int = 5) -> dict:
    """
    Ищет автора онлайн, тянет пары {title, snippet}, сохраняет как лирические
    заготовки. Полноценные тексты нельзя тянуть без API — используем snippets
    как стилевой намёк.
    """
    hits = search_author_online(author, max_tracks=max_tracks * 3)
    kept = 0
    for h in hits:
        if "error" in h:
            continue
        text = h.get("snippet") or ""
        if len(text) < 40:
            continue
        ingest_lyrics_text(text, author=author, title=h.get("title", ""))
        kept += 1
        if kept >= max_tracks:
            break
    if kept:
        build_style_profile(author)
    return {"ok": kept > 0, "ingested": kept, "author": author}


# ------------------------------------------------------------- prompt builder
def build_style_prompt(
    author: str, theme: str, user_words: list[str], bpm: int, target_lines: int = 16
) -> str:
    """
    Строим промт для Ollama/лирического движка с учётом стилевого профиля автора.
    """
    profile = get_style_profile(author) or {}
    words = ", ".join(w["w"] for w in profile.get("top_words", [])[:20])
    bigs = ", ".join(profile.get("top_bigrams", [])[:10])
    samples = "\n".join(f"  • {s}" for s in profile.get("sample_lines", [])[:6])
    avg = profile.get("avg_syll_per_line", 9.0)
    user_line = ", ".join(user_words or []) or "(нет)"
    parts = [
        f"Пиши текст в стиле «{profile.get('author', author) or author}».",
        f"Тема: {theme}. Обязательно впиши слова пользователя: {user_line}.",
        f"BPM трека: {bpm}. Средняя длина строки — около {avg} слогов.",
        "Куплеты на русском, припев/хук может быть на английском.",
        f"Целевая длина: {target_lines} строк, без нейроношных повторов, "
        "с рифмой AABB или ABAB.",
        f"Характерные слова автора: {words}." if words else "",
        f"Характерные обороты: {bigs}." if bigs else "",
        f"Примеры строк автора:\n{samples}" if samples else "",
        "Выдай текст блоками [Куплет 1] / [Припев] / [Куплет 2] / [Аутро].",
    ]
    return "\n".join(p for p in parts if p)


# ------------------------------------------------------------- library sweep
def scan_library(
    references_dir: str | Path = None, vault_dir: str | Path = None
) -> dict:
    """
    Проход по всей библиотеке пользователя: references/*.mp3 → whisper →
    ingest; lyric_vault/*.txt → ingest как unknown если автор неизвестен.
    """
    references_dir = Path(references_dir or ROOT / "references")
    vault_dir = Path(vault_dir or ROOT / "lyric_vault")
    added_audio = added_text = 0
    for ext in ("*.mp3", "*.wav", "*.flac", "*.m4a"):
        for f in references_dir.rglob(ext):
            author = f.parent.name if f.parent != references_dir else "unknown"
            r = ingest_reference_audio(f, author=author, title=f.stem)
            if r.get("ok"):
                added_audio += 1
    for f in vault_dir.rglob("*.txt"):
        if "author_corpus" in str(f) or "slang" in f.name:
            continue
        r = ingest_lyrics_file(f, author=f.parent.name or "unknown", title=f.stem)
        if r.get("ok"):
            added_text += 1
    return {"ok": True, "audio_ingested": added_audio, "text_ingested": added_text}


def list_authors() -> list[dict]:
    idx = _load_index()
    return [
        {"slug": s, "name": d.get("display_name", s), "files": len(d.get("files", []))}
        for s, d in idx.items()
    ]


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "scan":
        print(json.dumps(scan_library(), ensure_ascii=False, indent=2))
    elif len(sys.argv) > 2 and sys.argv[1] == "profile":
        print(
            json.dumps(build_style_profile(sys.argv[2]), ensure_ascii=False, indent=2)
        )
    else:
        print(json.dumps(list_authors(), ensure_ascii=False, indent=2))
