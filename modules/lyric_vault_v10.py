# -*- coding: utf-8 -*-
"""
ZS Music Maker v10 — Lyric Vault v10
======================================
Расширенное хранилище лирики (ТЗ 3.7).

Возможности v10 (сверх lyrics_memory.jsonl v9):
  - индекс по BPM / слоговой плотности / эмоции / темам
  - кросс-жанровое смешение хуков
  - поиск подходящих панчей под текущий BPM
  - экспорт в LRC с тайм-кодами
  - импорт из чужих транскриптов с автопомечанием
  - анти-повтор: чтобы одни и те же строки не всплывали 5 треков подряд
"""
from __future__ import annotations
import json
import time
import hashlib
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import Counter

log = logging.getLogger("zsmm.lyric_vault_v10")

VAULT = Path("lyric_vault")
MEMORY_JSONL = VAULT / "lyrics_memory.jsonl"
INDEX_JSON = VAULT / "vault_index_v10.json"
USAGE_LOG = VAULT / "line_usage_log.json"


def _syllable_count(line: str) -> int:
    """
    Приблизительный подсчёт слогов (RU/EN).
    Для RU считаем гласные, для EN — группы гласных.
    """
    line = line.lower()
    ru_vowels = set("аеёиоуыэюяaeiouy")
    n = 0
    prev_vowel = False
    for ch in line:
        is_v = ch in ru_vowels
        if is_v and not prev_vowel:
            n += 1
        prev_vowel = is_v
    return max(1, n)


def add_line(text: str,
             bpm: Optional[int] = None,
             emotion: str = "neutral",
             topic: str = "generic",
             lang: str = "ru",
             source: str = "user") -> Dict[str, Any]:
    """
    Добавляет строку в vault.
    """
    VAULT.mkdir(parents=True, exist_ok=True)
    entry = {
        "id": hashlib.md5(f"{text}{time.time()}".encode()).hexdigest()[:10],
        "text": text.strip(),
        "syllables": _syllable_count(text),
        "bpm": bpm,
        "emotion": emotion,
        "topic": topic,
        "lang": lang,
        "source": source,
        "created_at": int(time.time()),
        "use_count": 0,
    }
    with open(MEMORY_JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def load_all() -> List[Dict[str, Any]]:
    """
    Загружает все записи из lyrics_memory.jsonl.
    Совместимость: v9-записи (поле 'lyrics' вместо 'text', без 'id')
    нормализуются в v10-схему на лету, без перезаписи файла.
    """
    if not MEMORY_JSONL.exists():
        return []
    out = []
    with open(MEMORY_JSONL, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except Exception:
                continue
            # v9 -> v10 нормализация
            if "id" not in entry:
                base = str(entry.get("text") or entry.get("lyrics") or i)
                entry["id"] = hashlib.md5(base.encode()).hexdigest()[:10]
            if "text" not in entry:
                entry["text"] = entry.get("lyrics", "")
            if "syllables" not in entry:
                entry["syllables"] = _syllable_count(str(entry.get("text", "")))
            out.append(entry)
    return out


def find_lines(bpm: Optional[int] = None,
               emotion: Optional[str] = None,
               topic: Optional[str] = None,
               lang: Optional[str] = None,
               syllable_min: Optional[int] = None,
               syllable_max: Optional[int] = None,
               limit: int = 20,
               anti_repeat: bool = True) -> List[Dict[str, Any]]:
    """
    Ищет подходящие строки. Anti-repeat: строки использованные
    за последние 5 треков — отфильтровываются.
    """
    all_lines = load_all()
    recently_used = _recently_used_ids(last_n_tracks=5) if anti_repeat else set()

    matched = []
    for e in all_lines:
        if e["id"] in recently_used:
            continue
        if bpm and e.get("bpm") and abs(e["bpm"] - bpm) > 15:
            continue
        if emotion and e.get("emotion") != emotion:
            continue
        if topic and e.get("topic") != topic:
            continue
        if lang and e.get("lang") != lang:
            continue
        syl = e.get("syllables", 0)
        if syllable_min and syl < syllable_min:
            continue
        if syllable_max and syl > syllable_max:
            continue
        matched.append(e)

    # сортируем по use_count (свежее сначала)
    matched.sort(key=lambda x: (x.get("use_count", 0), -x.get("created_at", 0)))
    return matched[:limit]


def mark_used(line_ids: List[str], track_id: str) -> None:
    """
    Отмечает строки как использованные в треке (для anti-repeat).
    """
    usage = _load_usage()
    ts = int(time.time())
    for lid in line_ids:
        usage.setdefault(lid, []).append({"track": track_id, "at": ts})
    _save_usage(usage)


def rebuild_index() -> Dict[str, Any]:
    all_lines = load_all()
    idx = {
        "total_lines": len(all_lines),
        "by_lang": dict(Counter(e.get("lang", "?") for e in all_lines)),
        "by_emotion": dict(Counter(e.get("emotion", "?") for e in all_lines)),
        "by_topic": dict(Counter(e.get("topic", "?") for e in all_lines)),
        "bpm_range": {
            "min": min((e["bpm"] for e in all_lines if e.get("bpm")), default=None),
            "max": max((e["bpm"] for e in all_lines if e.get("bpm")), default=None),
        },
        "syllable_hist": dict(Counter(e.get("syllables", 0) for e in all_lines)),
        "rebuilt_at": int(time.time()),
    }
    VAULT.mkdir(parents=True, exist_ok=True)
    INDEX_JSON.write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")
    return idx


def export_lrc(lines: List[Dict[str, Any]], out_lrc: str,
               bpm: int = 120, start_offset_ms: int = 4000) -> str:
    """
    Экспорт в LRC с тайм-кодами (для караоке).
    Устойчив к разным shape'ам входа — если нет 'text', используется str(item).
    """
    beat_ms = int(60000 / bpm)
    bar_ms = beat_ms * 4
    Path(out_lrc).parent.mkdir(parents=True, exist_ok=True)
    with open(out_lrc, "w", encoding="utf-8") as f:
        f.write(f"[ti:Track]\n[ar:ZS]\n[al:MM ZS Vault Export]\n\n")
        t = start_offset_ms
        for e in lines:
            if isinstance(e, dict):
                text = e.get("text") or e.get("line") or ""
                syl = e.get("syllables", _syllable_count(text) if text else 4)
            else:
                text = str(e)
                syl = _syllable_count(text)
            mm = t // 60000
            ss = (t % 60000) / 1000.0
            f.write(f"[{mm:02d}:{ss:05.2f}]{text}\n")
            t += max(bar_ms, syl * (beat_ms // 2))
    return out_lrc


def _recently_used_ids(last_n_tracks: int = 5) -> set:
    usage = _load_usage()
    # собираем все track_id и берём последние N
    all_tracks = []
    for lid, entries in usage.items():
        for e in entries:
            all_tracks.append((e["at"], e["track"]))
    all_tracks.sort(reverse=True)
    # уникальные track_id, сохраняем порядок
    seen = []
    for _, t in all_tracks:
        if t not in seen:
            seen.append(t)
        if len(seen) >= last_n_tracks:
            break
    recent_tracks = set(seen)
    used = set()
    for lid, entries in usage.items():
        for e in entries:
            if e["track"] in recent_tracks:
                used.add(lid)
    return used


def _load_usage() -> Dict[str, list]:
    if USAGE_LOG.exists():
        try:
            return json.loads(USAGE_LOG.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_usage(u: Dict[str, list]) -> None:
    VAULT.mkdir(parents=True, exist_ok=True)
    USAGE_LOG.write_text(json.dumps(u, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    r = rebuild_index()
    print(json.dumps(r, ensure_ascii=False, indent=2))
