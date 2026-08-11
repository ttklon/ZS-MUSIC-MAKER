# -*- coding: utf-8 -*-
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
import os, json, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE_FILE = ROOT / "data" / "user_profile.json"
# v22: ленивое создание (не при импорте)

DEFAULT_PROFILE = {
    "artist_name": "",
    "first_run": True,
    "quality_mode": "quality",           # fast | quality | max
    "last_settings": {},
    "favorite_themes": ["лето", "тачки", "деньги", "движ"],
    "favorite_presets": ["tamam_like", "brazilian_phonk"],
    "history": [],
    "voice_training_hours": 0.0,
    "voice_training_completed": False,
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
    PROFILE_FILE.write_text(json.dumps(p, ensure_ascii=False, indent=2),
                            encoding="utf-8")


def update(**kwargs) -> dict:
    p = get_profile()
    for k, v in kwargs.items():
        p[k] = v
    save_profile(p)
    return p


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
    p["history"] = p["history"][-100:]     # держим только последние 100
    save_profile(p)


def get_history(limit: int = 20) -> list:
    return list(reversed(get_profile().get("history", [])))[:limit]


def add_favorite_theme(theme: str) -> dict:
    if not theme: return {"error": "пусто"}
    p = get_profile()
    if theme not in p["favorite_themes"]:
        p["favorite_themes"].append(theme)
        p["favorite_themes"] = p["favorite_themes"][-30:]
        save_profile(p)
    return {"ok": True, "themes": p["favorite_themes"]}


def add_favorite_preset(preset_key: str) -> dict:
    if not preset_key: return {"error": "пусто"}
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
        return {"ok": True, "hours": p["voice_training_hours"],
                "ready": p["voice_training_completed"], "detail": v}
    except Exception as e:
        return {"error": str(e)}


def save_last_settings(settings: dict) -> None:
    update(last_settings=settings)


def get_last_settings() -> dict:
    return get_profile().get("last_settings", {})


if __name__ == "__main__":
    print(json.dumps(get_profile(), indent=2, ensure_ascii=False))
