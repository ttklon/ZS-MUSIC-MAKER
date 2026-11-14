# -*- coding: utf-8 -*-
"""
modules.hit_factory.config — константы фабрики хитов.

Жанры взвешены по «вирусности» 2026 (phonk/trap/jersey — топ чартов TikTok/Rap).
BPM-карта — sweet spot'ы из hit_scorer._bpm_dance_fitness.
"""
from __future__ import annotations

# Веса хитовых жанров: чем выше, тем чаще выпадает при случайном выборе.
# Ключи — это слаги из data/genre_presets/*.json + genres_100
HIT_GENRE_WEIGHTS: dict[str, float] = {
    # tier S — абсолютные хитовые (phonk семейство доминирует в RU тиктоке)
    "drift_phonk": 1.0,
    "phonk": 0.95,
    "memphis_phonk": 0.9,
    "drift_phonk": 1.0,
    "trap": 1.0,
    "jersey_club": 0.9,
    "rage": 0.85,
    "plugg": 0.85,
    "hyperpop": 0.8,
    "drill": 0.85,
    "uk_drill": 0.8,
    "brazilian_phonk": 0.8,
    # tier A — стабильные чарты
    "afro_house": 0.75,
    "deep_house": 0.7,
    "house": 0.7,
    "tech_house": 0.7,
    "dancehall": 0.65,
    "reggaeton": 0.7,
    "amapiano": 0.65,
    "afrobeat": 0.65,
    "baile_funk": 0.65,
    "dnb": 0.6,
    "future_bass": 0.65,
    "edm": 0.6,
    "slap_house": 0.65,
    "2step": 0.6,
    "uk_garage": 0.6,
    # tier B — нишевые / атмосферные (реже в фабрике)
    "lofi": 0.35,
    "witch_house": 0.3,
    "ambient_trap": 0.4,
    "retrowave": 0.4,
    "synthwave": 0.4,
    "boom_bap": 0.35,
    "cloud_rap": 0.45,
    "dark_trap": 0.5,
    "dark_pop": 0.4,
    "cinematic": 0.25,
    "jazz": 0.2,
}

# BPM sweet spots (center, tolerance, alternate_trap_range)
# Используется для мутаций: если жанр trap — 140 тоже ок (double-time feel)
BPM_MAP: dict[str, dict] = {
    "drift_phonk": {"center": 140, "range": (134, 150), "alt": None},
    "phonk": {"center": 142, "range": (136, 150), "alt": None},
    "memphis_phonk": {"center": 140, "range": (134, 148), "alt": None},
    "brazilian_phonk": {"center": 144, "range": (138, 152), "alt": None},
    "trap": {"center": 144, "range": (138, 150), "alt": (70, 95)},  # half-time 72-86 == 144-172 double
    "drill": {"center": 142, "range": (138, 148), "alt": (71, 76)},
    "uk_drill": {"center": 144, "range": (138, 150), "alt": None},
    "jersey_club": {"center": 138, "range": (132, 142), "alt": None},
    "rage": {"center": 152, "range": (145, 162), "alt": None},
    "plugg": {"center": 146, "range": (138, 154), "alt": None},
    "hyperpop": {"center": 150, "range": (140, 160), "alt": None},
    "afro_house": {"center": 124, "range": (120, 128), "alt": None},
    "house": {"center": 126, "range": (122, 130), "alt": None},
    "deep_house": {"center": 122, "range": (118, 126), "alt": None},
    "tech_house": {"center": 128, "range": (124, 132), "alt": None},
    "dancehall": {"center": 96, "range": (88, 102), "alt": None},
    "reggaeton": {"center": 96, "range": (90, 102), "alt": None},
    "amapiano": {"center": 112, "range": (108, 118), "alt": None},
    "dnb": {"center": 174, "range": (170, 180), "alt": (87, 90)},
    "future_bass": {"center": 150, "range": (140, 160), "alt": None},
    "edm": {"center": 128, "range": (124, 140), "alt": None},
    "slap_house": {"center": 126, "range": (122, 130), "alt": None},
    "lofi": {"center": 85, "range": (75, 92), "alt": None},
    "boom_bap": {"center": 88, "range": (82, 95), "alt": None},
    "default": {"center": 128, "range": (120, 140), "alt": None},
}

# Пул тем 2026 — офлайнFallback + будет обогащаться trend_scout.live
THEME_POOL: list[str] = [
    "лето, тачки, движ, Стамбул",
    "ночь, неон, флекс, город спит",
    "деньги, успех, первый чек",
    "любовь, краш, разлука на границе",
    "тачка как второе имя, Supra, дрифт",
    "клуб, вечер, друзья, бас качает",
    "верность района, пацаны рядом",
    "турция, Босфор, чай, вайб",
    "трекера залетевший тикток, хук на повторе",
    "тёмный вайб, 808, агрессия",
    "летний драйв на юге, море, жара",
    "ночная гонка в неоне, скорость",
    "движ до утра, энергия прёт",
    "деньги — фон, я — сюжет",
    "город спит, а мой мотор рычит",
    "флекс, имба, вайб, на волне",
    "романтика, закат, тепло",
    "уличный стиль, свэг, стайл",
]

# Длительности для хитов: тикток-версия 60-90, полный 120
DURATION_PRESETS: dict[str, int] = {
    "tiktok": 65,
    "short": 90,
    "full": 120,
    "extended": 150,
}

# Пороги hit_scorer
HIT_THRESHOLDS = {
    "chart_ready": 82.0,
    "solid": 68.0,
    "needs_work": 50.0,
}

# Пресеты человечности: какой polish применять после мастеринга
HUMAN_PRESETS: dict[str, dict] = {
    "gentle": {"vocal": "gentle", "track": "light"},
    "standard": {"vocal": "standard", "track": "standard"},
    "aggressive": {"vocal": "aggressive", "track": "heavy"},
}

# Эволюция: на сколько мутировать при плохом hit_score
MUTATION_RANGES = {
    "bpm_delta": 5,          # ±5 BPM
    "aggression_delta": 0.15, # ±0.15
    "seed_step": 1,
    "duration_variants": [65, 90, 120],
}

# Какие жанры показывать в --help (топ-10)
TOP_GENRES_FOR_HELP = [
    "drift_phonk", "phonk", "trap", "jersey_club", "rage",
    "plugg", "hyperpop", "drill", "house", "afro_house",
]
