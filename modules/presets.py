"""
[12] presets.py — Библиотека готовых пресетов (v5)
Готовые «стили» для быстрого старта, если пользователь не хочет анализировать референс.
"""

import json
import os

PRESETS_FILE = os.path.join(os.path.dirname(__file__), "..", "presets.json")

BUILTIN_PRESETS = {
    "tamam_like": {
        "name": "TAMAM-like (ethnic phonk drift)",
        "description": "Тёмный этник-фонк, дрифт, восточные лады, тяжёлый 808 — как TAMAM",
        "target_bpm": 129,
        "target_mode": "minor",
        "vibe_tags": ["phonk/drift", "bass-heavy", "dark", "aggressive", "underground"],
        "groove": {
            "kick_pattern": [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
            "snare_pattern": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            "hihat_density": 0.55,
            "swing": 0.12,
        },
        "sample_query": "phonk 808 memphis cowbell oriental saz",
        "prompt_hint": "dark ethnic drift phonk, distorted 808, memphis cowbell, oriental saz, aggressive",
        "themes": ["лето", "движ", "тачки", "деньги", "Стамбул", "чёрный мерс"],
    },
    "brazilian_phonk": {
        "name": "Brazilian phonk / funk",
        "description": "Быстрый бразильский фонк, кач как ХЛ, минорные атмосферы",
        "target_bpm": 140,
        "target_mode": "minor",
        "vibe_tags": ["trap/hype", "bass-heavy", "dark"],
        "groove": {
            "kick_pattern": [1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0],
            "snare_pattern": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            "hihat_density": 0.75,
            "swing": 0.05,
        },
        "sample_query": "brazilian phonk funk 140 bpm",
        "prompt_hint": "brazilian phonk, funk carioca, distorted kick, tuim",
        "themes": ["ночь", "движ", "клуб", "разрыв"],
    },
    "hyperpop_edit": {
        "name": "TikTok hyperpop / edit",
        "description": "Быстрый хайп для эдитов и коротких видео",
        "target_bpm": 160,
        "target_mode": "minor",
        "vibe_tags": ["hyper/hardstyle", "bright"],
        "groove": {
            "kick_pattern": [1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0],
            "snare_pattern": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            "hihat_density": 0.85,
            "swing": 0.02,
        },
        "sample_query": "hyperpop tiktok edit anime",
        "prompt_hint": "hyperpop, fast edit, pitched vocals, anime aesthetic",
        "themes": ["движ", "разрыв", "эдит", "хайп"],
    },
    "lofi_drift": {
        "name": "Lo-Fi drift / chill",
        "description": "Медленный ночной драйв, приглушённые барабаны",
        "target_bpm": 88,
        "target_mode": "minor",
        "vibe_tags": ["slow", "dark", "underground"],
        "groove": {
            "kick_pattern": [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
            "snare_pattern": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            "hihat_density": 0.4,
            "swing": 0.2,
        },
        "sample_query": "lo-fi drift chill night rain vinyl",
        "prompt_hint": "lo-fi, night drive, vinyl crackle, muted drums, jazzy chords",
        "themes": ["ночь", "тачка", "дождь", "мысли"],
    },
    "trap_ru": {
        "name": "Russian trap / уличка",
        "description": "Русский трэп, тяжёлый 808, читка",
        "target_bpm": 140,
        "target_mode": "minor",
        "vibe_tags": ["trap/hype", "bass-heavy", "aggressive", "underground"],
        "groove": {
            "kick_pattern": [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0],
            "snare_pattern": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            "hihat_density": 0.7,
            "swing": 0.08,
        },
        "sample_query": "trap 808 dark russian street",
        "prompt_hint": "russian street trap, dark 808, syncopated hats, minor keys",
        "themes": ["район", "движ", "бабки", "улица"],
    },
}


# Поля, без которых пресет не превращается в стилевой вектор.
REQUIRED_FIELDS = ("target_bpm", "target_mode")


def _load_all() -> dict:
    if os.path.exists(PRESETS_FILE):
        try:
            user = json.load(open(PRESETS_FILE, encoding="utf-8"))
        except Exception:
            user = {}
    else:
        user = {}
    if not isinstance(user, dict):
        user = {}
    merged = dict(BUILTIN_PRESETS)
    merged.update({k: v for k, v in user.items() if isinstance(v, dict)})
    return merged


def _missing_fields(preset: dict) -> list:
    """Чего не хватает пресету, чтобы стать стилем. Пустой список — всё есть."""
    return [field for field in REQUIRED_FIELDS if preset.get(field) in (None, "")]


def list_presets() -> list:
    """Список для CLI/GUI. Неполный пользовательский пресет остаётся видимым,
    но помечается `incomplete: True` — иначе он молча исчезает из интерфейса."""
    items = []
    for key, preset in _load_all().items():
        missing = _missing_fields(preset)
        items.append({
            "key": key,
            "name": preset.get("name") or key,
            "description": preset.get("description") or "",
            "bpm": preset.get("target_bpm"),
            "tags": list(preset.get("vibe_tags") or []),
            "incomplete": bool(missing),
        })
    return items


def get_preset(key: str) -> dict:
    preset = _load_all().get(key)
    if not preset:
        return {"error": f"пресет '{key}' не найден"}
    missing = _missing_fields(preset)
    if missing:
        return {"error": f"пресет '{key}' неполный: нет {', '.join(missing)}"}
    return preset


def save_user_preset(key: str, preset: dict) -> dict:
    user = {}
    if os.path.exists(PRESETS_FILE):
        try:
            user = json.load(open(PRESETS_FILE, encoding="utf-8"))
        except Exception:
            user = {}
    user[key] = preset
    json.dump(
        user, open(PRESETS_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2
    )
    return {"ok": True, "key": key, "saved_to": PRESETS_FILE}


def preset_to_style_vector(key: str) -> dict:
    p = get_preset(key)
    if "error" in p:
        return p
    return {
        "sources": [f"preset:{key}"],
        "target_bpm": p["target_bpm"],
        "target_mode": p["target_mode"],
        "vibe_tags": list(p.get("vibe_tags") or []),
        "target_bass_ratio": 1.5,
        "target_centroid": 1500.0,
        "bpm_range": {
            "center": p["target_bpm"],
            "range_low": p["target_bpm"] - 6,
            "range_high": p["target_bpm"] + 8,
            "modes": {"keep_groove": p["target_bpm"]},
        },
        "individual": [
            {
                "key_root": "A",
                "bpm": p["target_bpm"],
                "vibe_tags": list(p.get("vibe_tags") or []),
            }
        ],
        "preset_key": key,
        "themes_hint": p.get("themes", []),
        "sample_query_hint": p.get("sample_query", ""),
        "prompt_hint": p.get("prompt_hint", ""),
    }


if __name__ == "__main__":
    print(json.dumps(list_presets(), ensure_ascii=False, indent=2))
