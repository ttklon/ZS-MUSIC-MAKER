# grep-таблицы `modules/author_ref_lyrics.py`

## `import` — 11 совпадений
```
   21 | from __future__ import annotations
   23 | import hashlib
   24 | import json
   25 | import re
   26 | import time
   27 | from collections import Counter
   28 | from pathlib import Path
  147 |         import whisper
  243 |     import urllib.parse
  244 |     import urllib.request
  360 |     import sys
```

## `print` — 3 совпадений
```
  363 |         print(json.dumps(scan_library(), ensure_ascii=False, indent=2))
  365 |         print(
  369 |         print(json.dumps(list_authors(), ensure_ascii=False, indent=2))
```

## `except` — 4 совпадений
```
   94 |         except Exception:
  155 |     except Exception as e:
  229 |         except Exception:
  254 |     except Exception as e:
```

## `try` — 4 совпадений
```
   92 |         try:
  146 |     try:
  227 |         try:
  248 |     try:
```

## `def` — 14 совпадений
```
   82 | def _tokenize(text: str) -> list[str]:
   86 | def _syllables_ru(word: str) -> int:
   90 | def _load_index() -> dict:
   99 | def _save_index(idx: dict) -> None:
  106 | def ingest_lyrics_file(path: str | Path, author: str, title: str = "") -> dict:
  115 | def ingest_lyrics_text(text: str, author: str, title: str = "") -> dict:
  139 | def ingest_reference_audio(
  160 | def build_style_profile(author: str) -> dict:
  223 | def get_style_profile(author: str) -> dict | None:
  237 | def search_author_online(author: str, max_tracks: int = 20) -> list[dict]:
  274 | def fetch_and_ingest_author(author: str, max_tracks: int = 5) -> dict:
  298 | def build_style_prompt(
  326 | def scan_library(
  351 | def list_authors() -> list[dict]:
```

## `return` — 24 совпадений
```
   83 |     return [w.lower() for w in _WORD_RE.findall(text or "")]
   87 |     return max(1, sum(1 for ch in word.lower() if ch in "аеёиоуыэюяaeiouy"))
   93 |             return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
   95 |             return {}
   96 |     return {}
  110 |         return {"ok": False, "error": f"file not found: {path}"}
  112 |     return ingest_lyrics_text(text, author=author, title=title or path.stem)
  136 |     return {"ok": True, "author": author_slug, "id": fname}
  145 |         return {"ok": False, "error": "no audio"}
  153 |             return {"ok": False, "error": "empty transcription"}
  154 |         return ingest_lyrics_text(text, author=author, title=title or audio_path.stem)
  156 |         return {"ok": False, "error": f"whisper failed: {e}"}
  168 |         return {"ok": False, "error": f"нет корпуса для {author}"}
  176 |         return {"ok": False, "error": "слишком мало данных"}
  220 |     return {"ok": True, "profile": profile}
  228 |             return json.loads(f.read_text(encoding="utf-8"))
  230 |             return None
  233 |     return r.get("profile") if r.get("ok") else None
  255 |         return [{"error": str(e)}]
  271 |     return results
  294 |     return {"ok": kept > 0, "ingested": kept, "author": author}
  322 |     return "\n".join(p for p in parts if p)
  348 |     return {"ok": True, "audio_ingested": added_audio, "text_ingested": added_text}
  353 |     return [
```

## `if` — 21 совпадений
```
   91 |     if CACHE_FILE.exists():
  109 |     if not path.exists():
  144 |     if not audio_path.exists():
  152 |         if not text:
  167 |     if not author_dir.exists():
  175 |     if len(tokens) < 5:
  185 |         if a not in _STOPWORDS and b not in _STOPWORDS:
  194 |         if ws:
  202 |         if ws:
  226 |     if f.exists():
  267 |         if title and snip:
  269 |         if len(results) >= max_tracks:
  283 |         if "error" in h:
  286 |         if len(text) < 40:
  290 |         if kept >= max_tracks:
  292 |     if kept:
  340 |             if r.get("ok"):
  343 |         if "author_corpus" in str(f) or "slang" in f.name:
  346 |         if r.get("ok"):
  359 | if __name__ == "__main__":
  362 |     if len(sys.argv) > 1 and sys.argv[1] == "scan":
```

## `for` — 11 совпадений
```
   34 | for p in (CORPUS_DIR, STYLE_DIR):
  171 |     for f in author_dir.glob("*.txt"):
  183 |     for i in range(len(tokens) - 1):
  192 |     for line in lines[:400]:
  200 |     for line in lines[:200]:
  258 |     for m in re.finditer(
  282 |     for h in hits:
  336 |     for ext in ("*.mp3", "*.wav", "*.flac", "*.m4a"):
  337 |         for f in references_dir.rglob(ext):
  342 |     for f in vault_dir.rglob("*.txt"):
  355 |         for s, d in idx.items()
```

## `with` — 1 совпадений
```
  252 |         with urllib.request.urlopen(req, timeout=8) as r:
```
