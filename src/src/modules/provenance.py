# -*- coding: utf-8 -*-
"""
[10] provenance.py — License / Provenance Manager v2 (НОВЫЙ)
Отслеживает происхождение каждого сэмпла, условия использования и предупреждения.
Важно для Freesound (разные CC-лицензии) и MusicRadar (royalty-free, но не redistribute).
"""
import os, json, time

VAULT = os.path.join(os.path.dirname(__file__), "..", "samples_cache", "provenance.json")
# v22: ленивое создание (не при импорте)

LICENSES = {
    "cc0": {"name": "CC0 — Public Domain", "commercial": True, "attribution": False,
            "note": "Свободное использование без ограничений"},
    "cc-by": {"name": "CC-BY — Attribution", "commercial": True, "attribution": True,
              "note": "Нужно указать автора"},
    "cc-by-nc": {"name": "CC-BY-NC — NonCommercial", "commercial": False, "attribution": True,
                 "note": "Только некоммерческое использование. Указать автора."},
    "cc-by-sa": {"name": "CC-BY-SA — ShareAlike", "commercial": True, "attribution": True,
                 "note": "Указать автора. Производные — на той же лицензии."},
    "cc-by-nc-sa": {"name": "CC-BY-NC-SA", "commercial": False, "attribution": True,
                    "note": "Некоммерческое. Указать автора. ShareAlike."},
    "royalty_free": {"name": "Royalty-Free", "commercial": True, "attribution": False,
                     "note": "Свободное использование в музыке. Не перераспространять как пак."},
    "unknown": {"name": "Unknown — проверить вручную", "commercial": False, "attribution": True,
                "note": "Лицензия не определена. Проверьте перед использованием."},
}


def _load():
    if os.path.exists(VAULT):
        try:
            return json.load(open(VAULT, encoding="utf-8"))
        except Exception:
            return []
    return []


def _save(data):
    json.dump(data, open(VAULT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def add_sample(name: str, path: str, source_url: str = "",
               license_key: str = "unknown", author: str = "",
               tags: list = None, bpm: float = None, key: str = "") -> dict:
    """Регистрирует сэмпл в provenance базе."""
    entry = {
        "name": name,
        "path": path,
        "source": source_url,
        "license": license_key,
        "license_info": LICENSES.get(license_key, LICENSES["unknown"]),
        "author": author,
        "tags": tags or [],
        "bpm": bpm,
        "key": key,
        "added": time.time(),
    }
    data = _load()
    data.append(entry)
    _save(data)
    return entry


def list_samples() -> list:
    return _load()


def check_commercial_safe() -> dict:
    """Проверяет все сэмплы на возможность коммерческого использования."""
    data = _load()
    safe = [s for s in data if s.get("license_info", {}).get("commercial", False)]
    unsafe = [s for s in data if not s.get("license_info", {}).get("commercial", False)]
    needs_attribution = [s for s in data if s.get("license_info", {}).get("attribution", False)]
    return {
        "total": len(data),
        "commercial_safe": len(safe),
        "non_commercial": len(unsafe),
        "needs_attribution": len(needs_attribution),
        "safe_samples": [s["name"] for s in safe],
        "unsafe_samples": [{"name": s["name"], "license": s.get("license")} for s in unsafe],
    }


def generate_attribution_text() -> str:
    """Генерирует текст атрибуции для всех сэмплов требующих указания автора."""
    data = _load()
    lines = ["=== Атрибуция сэмплов ===\n"]
    for s in data:
        info = s.get("license_info", {})
        if info.get("attribution"):
            lines.append(f"• {s['name']} — {s.get('author', 'unknown')} — {info['name']} — {s.get('source', '')}")
    return "\n".join(lines) if len(lines) > 1 else "Атрибуция не требуется."


if __name__ == "__main__":
    print(json.dumps(check_commercial_safe(), ensure_ascii=False, indent=2))
