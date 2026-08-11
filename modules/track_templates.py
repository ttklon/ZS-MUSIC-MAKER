"""
[v8] track_templates.py — сохранение и запуск «Шаблонов трека».

ТЗ 20.3: «Мастер должен позволять сохранить Шаблон трека (пресет + тема + длина)
и быстро его запускать повторно. История — последние 100 треков.»

Работает поверх recipe.json. Хранит в data/templates/*.json.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TPL_DIR = ROOT / "data" / "templates"
HIST_FILE = ROOT / "data" / "history.json"
# v22: ленивое создание (не при импорте)

# v22: ленивое создание (не при импорте)


def _load_history() -> list[dict]:
    if HIST_FILE.exists():
        try:
            return json.loads(HIST_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_history(items: list[dict]) -> None:
    HIST_FILE.write_text(
        json.dumps(items[-100:], ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ------------------------------------------------------- templates
def save_template(name: str, recipe: dict) -> str:
    tid = uuid.uuid4().hex[:10]
    data = {
        "id": tid,
        "name": name,
        "created_at": time.time(),
        "recipe": recipe,
    }
    (TPL_DIR / f"{tid}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return tid


def list_templates() -> list[dict]:
    out = []
    for f in TPL_DIR.glob("*.json"):
        try:
            out.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            continue
    out.sort(key=lambda d: d.get("created_at", 0), reverse=True)
    return out


def load_template(tid: str) -> dict | None:
    f = TPL_DIR / f"{tid}.json"
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return None


def delete_template(tid: str) -> bool:
    f = TPL_DIR / f"{tid}.json"
    if f.exists():
        f.unlink()
        return True
    return False


# ------------------------------------------------------- history
def push_history(track_meta: dict) -> None:
    hist = _load_history()
    entry = dict(track_meta)
    entry.setdefault("ts", time.time())
    entry.setdefault("id", uuid.uuid4().hex[:10])
    hist.append(entry)
    _save_history(hist)


def get_history(limit: int = 100) -> list[dict]:
    return _load_history()[-limit:]


def clear_history() -> None:
    _save_history([])
