# -*- coding: utf-8 -*-
"""
tests/test_hit_factory.py — smoke тесты фабрики хитов (без тяжёлого аудио).

Проверяем логику выбора, мутаций и базовой интеграции, не рендеря 120с аудио.
Полный рендер тестируется в test_hit_factory_e2e (маркирован как slow).
"""
import random

def test_pick_genre_deterministic():
    from modules.hit_factory.themes import pick_genre
    rng = random.Random(42)
    g1 = pick_genre(rng)
    rng = random.Random(42)
    g2 = pick_genre(rng)
    assert g1 == g2
    assert isinstance(g1, str) and len(g1) > 0

def test_pick_theme_offline():
    from modules.hit_factory.themes import pick_theme
    rng = random.Random(1)
    t = pick_theme(rng, use_trends=False)
    assert isinstance(t, str) and len(t) >= 5
    # фиксированная тема возвращается как есть
    assert pick_theme(rng, base_theme="кастом тема") == "кастом тема"

def test_pick_bpm_in_range():
    from modules.hit_factory.themes import pick_bpm
    from modules.hit_factory.config import BPM_MAP
    for genre in ("trap", "drift_phonk", "house", "phonk"):
        bpm = pick_bpm(genre, random.Random(7))
        info = BPM_MAP.get(genre) or BPM_MAP["default"]
        lo, hi = info["range"]
        alt = info.get("alt")
        in_main = lo <= bpm <= hi
        in_alt = alt and alt[0] <= bpm <= alt[1] if alt else False
        assert in_main or in_alt, f"{genre} bpm {bpm} not in {(lo,hi)} alt {alt}"

def test_build_random_overrides_has_keys():
    from modules.hit_factory.themes import build_random_recipe_overrides
    ov = build_random_recipe_overrides(random.Random(123), genre="trap")
    for k in ("genre", "theme", "bpm_override", "aggression", "seed", "duration_sec"):
        assert k in ov
    assert ov["genre"] == "trap"
    assert 60 <= ov["bpm_override"] <= 180
    assert 0.3 <= ov["aggression"] <= 0.95

def test_mutate_changes_bpm_and_seed():
    from modules.hit_factory.evolver import mutate
    import random
    base = {"genre": "trap", "bpm_override": 140, "aggression": 0.7, "seed": 42, "theme": "test", "duration_sec": 90}
    nxt = mutate(base, None, random.Random(1))
    assert nxt["seed"] != 42
    assert nxt["bpm_override"] != 140 or nxt["aggression"] != 0.7  # хоть что-то поменялось

def test_select_best_picks_max():
    from modules.hit_factory.evolver import select_best
    attempts = [{"hit_score": 55, "project_id": "a"}, {"hit_score": 72, "project_id": "b"}, {"hit_score": 60, "project_id": "c"}]
    best = select_best(attempts)
    assert best["project_id"] == "b"

def test_should_evolve():
    from modules.hit_factory.evolver import should_evolve
    assert should_evolve(50, "needs_work", 68) is True
    assert should_evolve(72, "solid", 68) is False
    assert should_evolve(82, "chart_ready", 68) is False
    assert should_evolve(None, None, 68) is True

def test_hit_factory_import():
    from modules.hit_factory import HitFactory, quick_hit
    assert HitFactory is not None
    assert quick_hit is not None

def test_hit_factory_config_weights_sum():
    from modules.hit_factory.config import HIT_GENRE_WEIGHTS
    # все веса >0
    assert all(v > 0 for v in HIT_GENRE_WEIGHTS.values())
    assert "drift_phonk" in HIT_GENRE_WEIGHTS
    assert "trap" in HIT_GENRE_WEIGHTS

def test_humanizer_ensure_no_file():
    from modules.hit_factory.humanizer import ensure_human
    res = ensure_human("/tmp/does_not_exist_12345.wav")
    assert res["ok"] is False
