# -*- coding: utf-8 -*-
"""`modules/presets.py`: пресеты и их влияние на рецепт.

Пресет — это «стиль для быстрого старта», и он реально управляет битом: BPM и
лад попадают в рецепт через `preset_style_vector`. Покрытия не было ни одного
процента, хотя `app/core/recipe.py` вызывает модуль на каждом прогоне с
пресетом. Тесты нашлись не зря: пользовательский пресет из `presets.json`
без полей `name`/`target_mode` ронял список в CLI (`KeyError`) и тихо лишал
рецепт стиля.

Файл пресетов подменяется на временный: настоящий `presets.json` в репозитории
не хранится и тесты его не создают.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from modules import presets


@pytest.fixture
def presets_file(tmp_path, monkeypatch) -> Path:
    target = tmp_path / "presets.json"
    monkeypatch.setattr(presets, "PRESETS_FILE", str(target))
    return target


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


# --------------------------------------------------------------------------- #
#  Встроенные пресеты
# --------------------------------------------------------------------------- #

def test_every_builtin_preset_is_complete() -> None:
    required = {
        "name", "description", "target_bpm", "target_mode", "vibe_tags",
        "groove", "sample_query", "prompt_hint", "themes",
    }
    for key, preset in presets.BUILTIN_PRESETS.items():
        missing = required - set(preset)
        assert not missing, f"пресет {key} неполный: {missing}"
        assert isinstance(preset["target_bpm"], int)
        assert preset["target_mode"] in {"minor", "major"}
        assert len(preset["groove"]["kick_pattern"]) == 16


def _gui_preset_keys() -> set[str]:
    """Ключи пресетов из GUI читаются по AST: PySide6 для этого не нужен."""
    import ast

    source = (Path(__file__).resolve().parents[1]
              / "app" / "gui" / "wizard" / "steps_material.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", "") == "PRESETS":
            keys = set()
            for item in node.value.elts:
                key_node = item.elts[1]
                if isinstance(key_node, ast.Constant) and key_node.value:
                    keys.add(key_node.value)
            return keys
    raise AssertionError("в steps_material.py не найден список PRESETS")


def test_builtin_preset_keys_match_gui_list() -> None:
    """GUI предлагает пресеты поимённо — ключи не должны разъезжаться."""
    gui_keys = _gui_preset_keys()

    assert gui_keys, "список пресетов в GUI пуст — тест ничего бы не проверил"
    assert gui_keys <= set(presets.BUILTIN_PRESETS), (
        f"GUI предлагает пресеты, которых нет в модуле: {gui_keys - set(presets.BUILTIN_PRESETS)}"
    )


def test_list_presets_without_user_file(presets_file) -> None:
    listed = presets.list_presets()

    assert len(listed) == len(presets.BUILTIN_PRESETS)
    entry = next(item for item in listed if item["key"] == "tamam_like")
    assert entry["bpm"] == 129
    assert entry["name"].startswith("TAMAM")
    assert "phonk/drift" in entry["tags"]


def test_get_preset_returns_builtin(presets_file) -> None:
    preset = presets.get_preset("trap_ru")

    assert preset["target_bpm"] == 140
    assert preset["name"].startswith("Russian trap")


def test_unknown_preset_is_reported_not_raised(presets_file) -> None:
    assert presets.get_preset("nope") == {"error": "пресет 'nope' не найден"}


def test_broken_user_file_falls_back_to_builtins(presets_file) -> None:
    presets_file.write_text("{ это не json", encoding="utf-8")

    assert len(presets.list_presets()) == len(presets.BUILTIN_PRESETS)


def test_user_preset_overrides_builtin(presets_file) -> None:
    full = dict(presets.BUILTIN_PRESETS["trap_ru"])
    full["target_bpm"] = 150
    _write(presets_file, {"trap_ru": full})

    assert presets.get_preset("trap_ru")["target_bpm"] == 150


# --------------------------------------------------------------------------- #
#  Пользовательский пресет без полей (дефект)
# --------------------------------------------------------------------------- #

def test_minimal_user_preset_is_listed_with_defaults(presets_file) -> None:
    """Пресет с одним лишь BPM не должен ронять список в CLI."""
    _write(presets_file, {"my_style": {"target_bpm": 120}})

    listed = {item["key"]: item for item in presets.list_presets()}

    assert "my_style" in listed
    entry = listed["my_style"]
    assert entry["bpm"] == 120
    assert entry["name"] == "my_style", "имя по умолчанию — сам ключ"
    assert entry["description"] == ""
    assert entry["tags"] == []


def test_preset_with_bpm_but_without_mode_is_refused(presets_file) -> None:
    """Половинка хуже отказа: лад по умолчанию подменил бы замысел автора."""
    _write(presets_file, {"my_style": {"target_bpm": 120}})

    vector = presets.preset_to_style_vector("my_style")

    assert "error" in vector and "target_mode" in vector["error"]


def test_complete_user_preset_yields_styled_vector(presets_file) -> None:
    """Дописанный автором лад — и стиль собирается целиком."""
    _write(presets_file, {"my_style": {"target_bpm": 120, "target_mode": "major"}})

    vector = presets.preset_to_style_vector("my_style")

    assert vector["preset_key"] == "my_style"
    assert vector["target_bpm"] == 120
    assert vector["target_mode"] == "major"
    assert vector["bpm_range"]["center"] == 120
    assert vector["bpm_range"]["range_low"] == 114
    assert vector["bpm_range"]["range_high"] == 128
    assert vector["vibe_tags"] == []
    assert vector["themes_hint"] == []
    assert vector["sample_query_hint"] == ""
    assert vector["prompt_hint"] == ""


# --------------------------------------------------------------------------- #
#  Стилевой вектор встроенного пресета
# --------------------------------------------------------------------------- #

def test_style_vector_of_builtin_preset(presets_file) -> None:
    vector = presets.preset_to_style_vector("tamam_like")

    assert vector["sources"] == ["preset:tamam_like"]
    assert vector["target_bpm"] == 129
    assert vector["target_mode"] == "minor"
    assert vector["target_bass_ratio"] == 1.5
    assert vector["target_centroid"] == 1500.0
    assert vector["bpm_range"] == {
        "center": 129,
        "range_low": 123,
        "range_high": 137,
        "modes": {"keep_groove": 129},
    }
    assert vector["individual"][0]["bpm"] == 129
    assert "Стамбул" in vector["themes_hint"]


def test_style_vector_of_unknown_preset_is_an_error(presets_file) -> None:
    assert "error" in presets.preset_to_style_vector("nope")


# --------------------------------------------------------------------------- #
#  Сохранение пользовательского пресета
# --------------------------------------------------------------------------- #

def test_save_user_preset_round_trip(presets_file) -> None:
    payload = dict(presets.BUILTIN_PRESETS["lofi_drift"])
    payload["target_bpm"] = 90

    result = presets.save_user_preset("мой_стиль", payload)

    assert result["ok"] is True and result["saved_to"] == str(presets_file)
    stored = json.loads(presets_file.read_text(encoding="utf-8"))
    assert stored["мой_стиль"]["target_bpm"] == 90
    # кириллица пишется как есть, а не \uXXXX — файл читает человек
    assert "мой_стиль" in presets_file.read_text(encoding="utf-8")
    assert presets.get_preset("мой_стиль")["target_bpm"] == 90


def test_save_user_preset_keeps_existing_ones(presets_file) -> None:
    _write(presets_file, {"first": {"target_bpm": 100}})

    presets.save_user_preset("second", {"target_bpm": 110})

    stored = json.loads(presets_file.read_text(encoding="utf-8"))
    assert set(stored) == {"first", "second"}


# --------------------------------------------------------------------------- #
#  Сквозная связка с рецептом
# --------------------------------------------------------------------------- #

def test_recipe_picks_up_preset_bpm(presets_file) -> None:
    """`build_recipe` обязан получить BPM пресета — это и есть «стиль»."""
    from app.core.recipe import build_recipe

    recipe = build_recipe({"preset": "hyperpop_edit", "theme": "хайп"})

    assert recipe["preset"] == "hyperpop_edit"
    assert recipe["preset_style_vector"]["target_bpm"] == 160
    assert recipe["preset_style_vector"]["prompt_hint"].startswith("hyperpop")


def test_recipe_survives_incomplete_user_preset(presets_file) -> None:
    """Пресет без BPM не даёт стиля — рецепт строится, но стиль честно пустой."""
    from app.core.recipe import build_recipe

    _write(presets_file, {"broken": {"description": "нет bpm"}})
    recipe = build_recipe({"preset": "broken"})

    assert recipe["preset_style_vector"] == {}
    assert recipe["genre"] == "broken"


def test_incomplete_preset_is_refused_with_reason(presets_file) -> None:
    """Без BPM стиль не собрать: отказ с причиной, а не нулевой темп."""
    _write(presets_file, {"broken": {"name": "Сломанный"}})

    result = presets.get_preset("broken")

    assert "error" in result
    assert "target_bpm" in result["error"]


def test_incomplete_preset_stays_visible_in_list(presets_file) -> None:
    """Из списка его не выкидываем молча — показываем, что он неполный."""
    _write(presets_file, {"broken": {"name": "Сломанный"}})

    listed = {item["key"]: item for item in presets.list_presets()}

    assert listed["broken"]["incomplete"] is True
    assert listed["broken"]["bpm"] is None
    assert listed["tamam_like"]["incomplete"] is False


def test_user_file_with_non_dict_payload_is_ignored(presets_file) -> None:
    """JSON-список вместо словаря — не повод падать."""
    presets_file.write_text("[1, 2, 3]", encoding="utf-8")

    assert len(presets.list_presets()) == len(presets.BUILTIN_PRESETS)


def test_non_dict_preset_entries_are_dropped(presets_file) -> None:
    _write(presets_file, {"good": {"target_bpm": 100, "target_mode": "minor"}, "bad": "строка"})

    keys = {item["key"] for item in presets.list_presets()}

    assert "good" in keys and "bad" not in keys


def test_save_over_broken_file_starts_from_scratch(presets_file) -> None:
    presets_file.write_text("{ испорчено", encoding="utf-8")

    presets.save_user_preset("fresh", {"target_bpm": 100, "target_mode": "minor"})

    stored = json.loads(presets_file.read_text(encoding="utf-8"))
    assert set(stored) == {"fresh"}
