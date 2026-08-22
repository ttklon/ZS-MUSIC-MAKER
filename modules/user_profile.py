"""
[v7] user_profile.py — профиль пользователя.

Хранит:
  • artist_name — обязательно запрашивается при первом запуске (для ID3-тегов)
  • first_run — маркер первого запуска (для onboarding)
  • quality_mode — Быстрый / Качественный / Максимальный
  • last_settings — последние настройки Wizard
  • favorite_themes, favorite_presets
  • history — последние 100 треков
  • voice_training_hours — сколько всего часов обучения RVC
"""

import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE_FILE = ROOT / "data" / "user_profile.json"
# v22: ленивое создание (не при импорте)

DEFAULT_PROFILE = {
    "artist_name": "",
    "first_run": True,
    "quality_mode": "quality",  # fast | quality | max
    "last_settings": {},
    "favorite_themes": ["лето", "тачки", "деньги", "движ"],
    "favorite_presets": ["tamam_like", "brazilian_phonk"],
    "history": [],
    "voice_training_hours": 0.0,
    "voice_training_completed": False,
    "creative_preferences": {
        "genres": ["phonk"],
        "language": "ru",
        "text_style": "direct, vivid, concise",
        "default_beat": {"bpm": 130, "key": "A minor", "mood": "dark, energetic"},
    },
    "created_at": None,
    "updated_at": None,
}


def get_profile() -> dict:
    if not PROFILE_FILE.exists():
        p = dict(DEFAULT_PROFILE)
        p["created_at"] = time.time()
        p["updated_at"] = p["created_at"]
        save_profile(p)
        return p
    try:
        p = json.load(open(PROFILE_FILE, "r", encoding="utf-8"))
        # Мигрируем недостающие поля
        for k, v in DEFAULT_PROFILE.items():
            p.setdefault(k, v)
        return p
    except Exception:
        return dict(DEFAULT_PROFILE)


def save_profile(p: dict) -> None:
    p["updated_at"] = time.time()
    PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_FILE.write_text(
        json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def update(**kwargs) -> dict:
    p = get_profile()
    for k, v in kwargs.items():
        p[k] = v
    save_profile(p)
    return p


def _clean_text(value: object, max_length: int = 120) -> str:
    """Keep preference strings bounded and reject obvious direct identifiers."""
    text = " ".join(str(value or "").strip().split())[:max_length]
    lowered = text.lower()
    if "@" in text or "http://" in lowered or "https://" in lowered:
        return ""
    digits = sum(char.isdigit() for char in text)
    if len(text) >= 7 and digits >= 7:
        return ""
    return text


def get_creative_preferences() -> dict:
    """Return only non-PII fields permitted to influence generation prompts."""
    raw = get_profile().get("creative_preferences") or {}
    raw_genres = raw.get("genres", [])
    if not isinstance(raw_genres, list):
        raw_genres = []
    genres = [value for value in (_clean_text(item, 32).lower() for item in raw_genres) if value][:5]
    language = str(raw.get("language", "ru")).lower()
    if language not in {"ru", "en", "bilingual"}:
        language = "ru"
    beat = raw.get("default_beat") if isinstance(raw.get("default_beat"), dict) else {}
    try:
        bpm = max(40, min(int(beat.get("bpm", 130)), 240))
    except (TypeError, ValueError):
        bpm = 130
    return {
        "genres": genres or ["phonk"],
        "language": language,
        "text_style": _clean_text(raw.get("text_style"), 120) or "direct, vivid, concise",
        "default_beat": {
            "bpm": bpm,
            "key": _clean_text(beat.get("key"), 24) or "A minor",
            "mood": _clean_text(beat.get("mood"), 80) or "dark, energetic",
        },
    }


def set_creative_preferences(
    genres: list[str] | None = None,
    language: str | None = None,
    text_style: str | None = None,
    default_beat: dict | None = None,
) -> dict:
    """Persist validated non-PII preferences without copying artist/history fields."""
    preferences = get_creative_preferences()
    if genres is not None:
        preferences["genres"] = [value for value in (_clean_text(item, 32).lower() for item in genres) if value][:5] or preferences["genres"]
    if language is not None and str(language).lower() in {"ru", "en", "bilingual"}:
        preferences["language"] = str(language).lower()
    if text_style is not None:
        preferences["text_style"] = _clean_text(text_style, 120) or preferences["text_style"]
    if default_beat is not None and isinstance(default_beat, dict):
        merged = {**preferences["default_beat"], **default_beat}
        try:
            merged["bpm"] = max(40, min(int(merged["bpm"]), 240))
        except (TypeError, ValueError):
            merged["bpm"] = preferences["default_beat"]["bpm"]
        merged["key"] = _clean_text(merged.get("key"), 24) or preferences["default_beat"]["key"]
        merged["mood"] = _clean_text(merged.get("mood"), 80) or preferences["default_beat"]["mood"]
        preferences["default_beat"] = merged
    profile = get_profile()
    profile["creative_preferences"] = preferences
    save_profile(profile)
    return preferences


def prompt_preferences(profile: dict | None = None) -> dict:
    """Return a narrow prompt-safe projection without creating a profile artifact."""
    # Prompt construction is read-only: absence of a profile uses static defaults
    # rather than `get_profile()`, which would otherwise write data/user_profile.json.
    candidate = dict(DEFAULT_PROFILE)
    candidate["creative_preferences"] = (
        DEFAULT_PROFILE["creative_preferences"]
        if profile is None
        else profile.get("creative_preferences", {})
    )
    raw = candidate["creative_preferences"]
    raw_genres = raw.get("genres", []) if isinstance(raw, dict) else []
    return {
        "genres": [value for value in (_clean_text(item, 32).lower() for item in raw_genres if isinstance(raw_genres, list)) if value][:5] or ["phonk"],
        "language": str(raw.get("language", "ru")).lower() if isinstance(raw, dict) and str(raw.get("language", "ru")).lower() in {"ru", "en", "bilingual"} else "ru",
        "text_style": _clean_text(raw.get("text_style") if isinstance(raw, dict) else "", 120) or "direct, vivid, concise",
        "default_beat": {
            "bpm": max(40, min(int((raw.get("default_beat") or {}).get("bpm", 130)), 240)) if isinstance(raw, dict) and str((raw.get("default_beat") or {}).get("bpm", "")).isdigit() else 130,
            "key": _clean_text((raw.get("default_beat") or {}).get("key") if isinstance(raw, dict) else "", 24) or "A minor",
            "mood": _clean_text((raw.get("default_beat") or {}).get("mood") if isinstance(raw, dict) else "", 80) or "dark, energetic",
        },
    }


def is_first_run() -> bool:
    return get_profile().get("first_run", True)


def mark_onboarded() -> dict:
    return update(first_run=False)


def set_artist_name(name: str) -> dict:
    """Устанавливает имя артиста — пишется в ID3-теги всех треков."""
    name = (name or "").strip() or "ZSMM Artist"
    return update(artist_name=name)


def get_artist_name() -> str:
    return get_profile().get("artist_name") or "ZSMM Artist"


def set_quality_mode(mode: str) -> dict:
    """mode: fast | quality | max"""
    if mode not in ("fast", "quality", "max"):
        mode = "quality"
    return update(quality_mode=mode)


def add_to_history(entry: dict) -> None:
    p = get_profile()
    entry.setdefault("timestamp", time.time())
    p["history"].append(entry)
    p["history"] = p["history"][-100:]  # держим только последние 100
    save_profile(p)


def get_history(limit: int = 20) -> list:
    return list(reversed(get_profile().get("history", [])))[:limit]


def add_favorite_theme(theme: str) -> dict:
    if not theme:
        return {"error": "пусто"}
    p = get_profile()
    if theme not in p["favorite_themes"]:
        p["favorite_themes"].append(theme)
        p["favorite_themes"] = p["favorite_themes"][-30:]
        save_profile(p)
    return {"ok": True, "themes": p["favorite_themes"]}


def add_favorite_preset(preset_key: str) -> dict:
    if not preset_key:
        return {"error": "пусто"}
    p = get_profile()
    if preset_key not in p["favorite_presets"]:
        p["favorite_presets"].append(preset_key)
        p["favorite_presets"] = p["favorite_presets"][-20:]
        save_profile(p)
    return {"ok": True, "presets": p["favorite_presets"]}


def sync_voice_progress() -> dict:
    """Обновляет прогресс обучения голоса из voice_convert.vault_summary()."""
    try:
        from modules.voice_convert import vault_summary

        v = vault_summary()
        p = get_profile()
        p["voice_training_hours"] = round(v.get("total_minutes", 0) / 60, 2)
        p["voice_training_completed"] = v.get("ready_for_training", False)
        save_profile(p)
        return {
            "ok": True,
            "hours": p["voice_training_hours"],
            "ready": p["voice_training_completed"],
            "detail": v,
        }
    except Exception as e:
        return {"error": str(e)}


def save_last_settings(settings: dict) -> None:
    update(last_settings=settings)


def get_last_settings() -> dict:
    return get_profile().get("last_settings", {})


if __name__ == "__main__":
    print(json.dumps(get_profile(), indent=2, ensure_ascii=False))
