"""
[v9] arrangement_engine.py — планировщик аранжировки 1:30-3:30+.

По ТЗ 3.5 (Beat Constructor / Arrangement Engine):
  «Ритм и аранжировка строятся ЗАНОВО, а не копируются».

Модуль НЕ генерирует аудио — он создаёт ARRANGEMENT PLAN (JSON), который
скармливается beat_constructor.py и mixdown.py. Планов может быть несколько
на трек (варианты).

План описывает:
  • Общую длину и BPM.
  • Список секций: intro, verse1, prechorus, chorus1, verse2, prechorus, chorus2,
    bridge, chorus3, outro. Каждая секция — n bars, energy 0..1, elements.
  • Элементы: kick_pattern, snare_pattern, hihat_pattern, 808_note,
    lead_texture, pad_texture, fx, vocal_role.
  • Переходы: fill_before, silence_before_ms, riser, downlifter.
  • TikTok-hook window (25 sec) с моментальным входом.

Учитывает style_vector из reference_ingest.py и hit_scorer targets.
"""

from __future__ import annotations

import json
import random
import time
from pathlib import Path

# ---------------------------------------------------------- templates
# Каждый шаблон — базовая структура для жанра.
# Секции: (name, bars_default, energy, vocal_role)
GENRE_TEMPLATES = {
    "phonk / drift": [
        ("intro", 4, 0.35, "silence"),
        ("verse1", 8, 0.55, "rap"),
        ("prechorus", 4, 0.65, "rap"),
        ("chorus1", 8, 0.90, "hook_ru_en"),
        ("verse2", 8, 0.60, "rap"),
        ("prechorus", 4, 0.70, "rap"),
        ("chorus2", 8, 0.95, "hook_ru_en"),
        ("bridge", 4, 0.50, "adlib"),
        ("chorus3", 8, 1.00, "hook_ru_en_female"),
        ("outro", 4, 0.30, "adlib"),
    ],
    "dance / edm": [
        ("intro", 8, 0.30, "silence"),
        ("build1", 8, 0.55, "adlib"),
        ("drop1", 16, 0.95, "hook_en"),
        ("break", 8, 0.45, "sing"),
        ("build2", 8, 0.60, "adlib"),
        ("drop2", 16, 1.00, "hook_en"),
        ("outro", 8, 0.30, "silence"),
    ],
    "trap / hip-hop": [
        ("intro", 4, 0.40, "silence"),
        ("verse1", 16, 0.55, "rap"),
        ("chorus1", 8, 0.85, "hook_ru"),
        ("verse2", 16, 0.60, "rap"),
        ("chorus2", 8, 0.95, "hook_ru_en"),
        ("bridge", 8, 0.50, "adlib"),
        ("chorus3", 8, 1.00, "hook_ru_en_female"),
        ("outro", 4, 0.30, "silence"),
    ],
    "pop / r&b": [
        ("intro", 4, 0.35, "silence"),
        ("verse1", 8, 0.55, "sing"),
        ("prechorus", 4, 0.65, "sing"),
        ("chorus1", 8, 0.90, "hook_ru_en_female"),
        ("verse2", 8, 0.60, "sing"),
        ("prechorus", 4, 0.70, "sing"),
        ("chorus2", 8, 0.95, "hook_ru_en_female"),
        ("bridge", 8, 0.50, "sing"),
        ("chorus3", 8, 1.00, "hook_ru_en_female"),
        ("outro", 4, 0.30, "silence"),
    ],
    "hardstyle / techno": [
        ("intro", 16, 0.30, "silence"),
        ("build1", 8, 0.55, "adlib"),
        ("drop1", 16, 1.00, "shout"),
        ("break", 8, 0.40, "silence"),
        ("build2", 8, 0.60, "adlib"),
        ("drop2", 16, 1.00, "shout"),
        ("outro", 8, 0.30, "silence"),
    ],
    "generic hit": [
        ("intro", 4, 0.35, "silence"),
        ("verse1", 8, 0.55, "rap"),
        ("chorus1", 8, 0.90, "hook_ru_en"),
        ("verse2", 8, 0.60, "rap"),
        ("chorus2", 8, 0.95, "hook_ru_en"),
        ("bridge", 4, 0.50, "adlib"),
        ("chorus3", 8, 1.00, "hook_ru_en_female"),
        ("outro", 4, 0.30, "silence"),
    ],
}

# Паттерны ударных для разных energy-уровней (16 ступеней = 1 bar в 16-х)
KICK_PATTERNS = {
    "sparse": [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    "trap": [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
    "four_floor": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
    "phonk": [1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1],
    "hard": [1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1],
}
SNARE_PATTERNS = {
    "backbeat": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    "trap": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0],
    "clap": [0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0],
}
HIHAT_PATTERNS = {
    "eighth": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
    "sixteenth": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    "trap": [1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1],
    "phonk": [1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1],
}


# ============================================================ helpers
def _pick(rng, patterns_dict, keys):
    for k in keys:
        if k in patterns_dict:
            return k, patterns_dict[k]
    k = rng.choice(list(patterns_dict.keys()))
    return k, patterns_dict[k]


def _bars_to_seconds(bars: int, bpm: float, beats_per_bar: int = 4) -> float:
    return bars * beats_per_bar * (60.0 / max(bpm, 1e-3))


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


# ============================================================ main API
def build_arrangement(
    style_vector: dict,
    total_seconds: float = 150.0,
    seed: int | None = None,
    genre_override: str | None = None,
    hit_targets: dict | None = None,
    variant: int = 0,
) -> dict:
    """
    Основной API. Строит план аранжировки под style_vector.
      total_seconds: 90..300, default 150 (2:30)
      variant: 0 — safe, 1 — bolder, 2 — experimental
    Возвращает dict с ключом 'sections' (list) и 'meta'.
    """
    rng = random.Random(seed or int(time.time()))
    sv = style_vector or {}
    bpm = float(sv.get("bpm", 130.0))
    key = sv.get("key", "C")
    mode = sv.get("mode", "minor")
    genre = genre_override or sv.get("genre_hint") or _guess_genre(sv)
    mood = sv.get("mood", "energetic / driving")

    template = GENRE_TEMPLATES.get(genre, GENRE_TEMPLATES["generic hit"])

    # Подгоняем общую длину под total_seconds — масштабируем bars
    default_seconds = sum(_bars_to_seconds(b, bpm) for _, b, _, _ in template)
    scale = _clamp(total_seconds / max(default_seconds, 1e-3), 0.5, 2.0)

    # Выбор паттернов по жанру
    if "phonk" in genre:
        kick_key, kick = _pick(rng, KICK_PATTERNS, ["phonk", "trap"])
        snare_key, snare = _pick(rng, SNARE_PATTERNS, ["backbeat", "clap"])
        hh_key, hh = _pick(rng, HIHAT_PATTERNS, ["phonk", "trap"])
    elif "dance" in genre or "techno" in genre or "hard" in genre:
        kick_key, kick = _pick(rng, KICK_PATTERNS, ["four_floor", "hard"])
        snare_key, snare = _pick(rng, SNARE_PATTERNS, ["clap", "backbeat"])
        hh_key, hh = _pick(rng, HIHAT_PATTERNS, ["eighth", "sixteenth"])
    elif "trap" in genre or "hip-hop" in genre:
        kick_key, kick = _pick(rng, KICK_PATTERNS, ["trap", "sparse"])
        snare_key, snare = _pick(rng, SNARE_PATTERNS, ["trap", "clap"])
        hh_key, hh = _pick(rng, HIHAT_PATTERNS, ["trap", "sixteenth"])
    elif "pop" in genre or "r&b" in genre:
        kick_key, kick = _pick(rng, KICK_PATTERNS, ["sparse", "four_floor"])
        snare_key, snare = _pick(rng, SNARE_PATTERNS, ["backbeat", "clap"])
        hh_key, hh = _pick(rng, HIHAT_PATTERNS, ["eighth"])
    else:
        kick_key, kick = _pick(rng, KICK_PATTERNS, ["trap"])
        snare_key, snare = _pick(rng, SNARE_PATTERNS, ["backbeat"])
        hh_key, hh = _pick(rng, HIHAT_PATTERNS, ["eighth"])

    sections = []
    t_cursor = 0.0
    for i, (name, bars_def, energy, vrole) in enumerate(template):
        bars = max(2, int(round(bars_def * scale)))
        dur = _bars_to_seconds(bars, bpm)

        # Модификации по variant
        if variant >= 1 and "chorus" in name:
            energy = min(1.0, energy + 0.03)
        if variant >= 2 and name in ("verse1", "verse2"):
            energy = _clamp(energy + rng.uniform(-0.08, 0.08), 0.3, 0.85)

        # Элементы: chorus3 — female backing on top
        has_female = ("chorus3" in name) or (vrole.endswith("female"))
        has_808 = energy > 0.5 and (
            "phonk" in genre or "trap" in genre or "hip-hop" in genre
        )
        has_lead = energy > 0.5

        # FX
        fx = []
        prev_name = sections[-1]["name"] if sections else None
        if name.startswith(("chorus", "drop")) and (prev_name or "").startswith(
            ("prechorus", "build", "bridge", "verse")
        ):
            fx.append("riser")
            fx.append("silence_50ms_before_drop")
        if name.startswith(("outro", "break")):
            fx.append("downlifter")

        # Fill перед chorus/drop
        fill_before = name.startswith(("chorus", "drop"))

        # Плотность hi-hat
        hh_density_mul = 1.0 if energy > 0.7 else (0.6 if energy > 0.4 else 0.3)

        sections.append(
            {
                "index": i,
                "name": name,
                "bars": bars,
                "start_sec": round(t_cursor, 2),
                "end_sec": round(t_cursor + dur, 2),
                "duration_sec": round(dur, 2),
                "energy": round(float(energy), 3),
                "vocal_role": vrole,
                "kick_pattern": kick_key,
                "snare_pattern": snare_key,
                "hihat_pattern": hh_key,
                "hihat_density": round(hh_density_mul, 2),
                "has_808": has_808,
                "has_lead": has_lead,
                "has_pad": energy < 0.6,
                "has_female_backing": has_female,
                "fill_before": fill_before,
                "fx": fx,
            }
        )
        t_cursor += dur

    # TikTok hook = самая громкая chorus секция + 25 сек оттуда
    hot_sections = sorted(
        [s for s in sections if s["name"].startswith(("chorus", "drop"))],
        key=lambda s: s["energy"],
        reverse=True,
    )
    if hot_sections:
        target = hot_sections[0]
        tt_start = target["start_sec"]
        tt_end = min(t_cursor, tt_start + 25.0)
    else:
        tt_start, tt_end = 0.0, min(25.0, t_cursor)

    plan = {
        "ok": True,
        "bpm": round(bpm, 2),
        "key": key,
        "mode": mode,
        "genre": genre,
        "mood": mood,
        "total_sec": round(t_cursor, 2),
        "requested_sec": round(total_seconds, 2),
        "variant": variant,
        "sections": sections,
        "tiktok_hook": {
            "start_sec": round(tt_start, 2),
            "end_sec": round(tt_end, 2),
        },
        "drums": {
            "kick": {"pattern_key": kick_key, "steps": kick},
            "snare": {"pattern_key": snare_key, "steps": snare},
            "hihat": {"pattern_key": hh_key, "steps": hh},
        },
        "hit_targets": hit_targets
        or {
            "lufs": -9.0,
            "chorus_gain_db_over_verse": 3.0,
            "stereo_corr": 0.75,
        },
        "seed": seed,
        "ts": time.time(),
    }
    return plan


def _guess_genre(sv: dict) -> str:
    bpm = sv.get("bpm", 130.0)
    if 130 <= bpm <= 145:
        return "phonk / drift"
    if 120 <= bpm < 130:
        return "dance / edm"
    if 70 <= bpm <= 100:
        return "trap / hip-hop"
    if 95 <= bpm < 120:
        return "pop / r&b"
    if bpm > 150:
        return "hardstyle / techno"
    return "generic hit"


def save_plan(plan: dict, out_path: str) -> str:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(
        json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return out_path


# ============================================================ CLI
if __name__ == "__main__":
    sv = {
        "bpm": 132,
        "key": "F",
        "mode": "minor",
        "genre_hint": "phonk / drift",
        "mood": "energetic / driving",
    }
    p = build_arrangement(sv, total_seconds=180, seed=42, variant=1)
    print(json.dumps(p, ensure_ascii=False, indent=2)[:3000])
