"""T12: число куплетов из визарда доезжает до шаблонного текста.

`_fallback_lyrics` всегда отдавала ровно `verse1` + `verse2`, игнорируя
`n_verses`: пользователь выбирал 1 или 4 куплета, а получал два. Шаблонный
текст — fallback, но и он обязан уважать явный выбор.
"""

from __future__ import annotations

import pytest

from app.core.stages.lyrics import _fallback_lyrics, _struct_to_text, _text_to_struct
from app.core.stages.lyrics_templates import LYRICS_TEMPLATES


@pytest.mark.parametrize("n_verses", [1, 2, 3, 4])
def test_fallback_produces_requested_number_of_verses(n_verses: int) -> None:
    result = _fallback_lyrics("ночной драйв", "drift_phonk", n_verses=n_verses)

    verses = [key for key in result if key.startswith("verse") and key[5:].isdigit()]
    assert verses == [f"verse{i}" for i in range(1, n_verses + 1)]
    assert all(result[key] for key in verses), "куплет не должен быть пустым"


def test_verses_beyond_the_template_are_not_literal_copies() -> None:
    """Куплеты за пределами шаблона не должны быть его сдвинутой копией.

    В шаблоне две строфы по 4 строки — всего 8 уникальных строк на 4 куплета,
    поэтому дословные повторы строк неизбежны, и требовать их отсутствия было
    бы неправдой. Реальное требование: ни один куплет не повторяет другой
    целиком и не является сдвигом предыдущего на одну строку (именно этот
    дефект и был: 3 строки из 4 совпадали с verse1).

    Прежняя версия теста заканчивалась на `... or True` и не проверяла ничего.
    """
    template = LYRICS_TEMPLATES["drift_phonk"]

    result = _fallback_lyrics("тема", "drift_phonk", n_verses=4)

    blocks = [tuple(result[f"verse{index}"]) for index in range(1, 5)]
    assert len(set(blocks)) == 4, "куплеты повторяются целиком"

    first = list(result["verse1"])
    rotated_by_one = first[1:] + first[:1]
    assert result["verse3"] != rotated_by_one, "3-й куплет — сдвиг 1-го на строку"
    # Строк в шаблоне 8 на 16 нужных: часть повторов неизбежна, но куплеты
    # не должны быть «тем же текстом с перестановкой».
    for later, base in (("verse3", "verse1"), ("verse4", "verse2")):
        overlap = len(set(result[later]) & set(result[base]))
        assert overlap <= 2, f"{later} совпадает с {base} на {overlap} строк из 4"
    assert len(result["verse1"]) == len(template["verse1"])
    assert result["verse3"] != result["verse4"]


def test_n_verses_is_clamped() -> None:
    low = _fallback_lyrics("тема", "drift_phonk", n_verses=0)
    high = _fallback_lyrics("тема", "drift_phonk", n_verses=99)

    numbered = lambda struct: [k for k in struct if k.startswith("verse") and k[5:].isdigit()]  # noqa: E731
    assert numbered(low) == ["verse1"]
    assert len(numbered(high)) == 4


def test_theme_still_reaches_the_first_line() -> None:
    result = _fallback_lyrics("полночный дрифт", "drift_phonk", n_verses=3)

    assert "полночный дрифт" in result["verse1"][0].lower()


def test_struct_to_text_renders_every_verse_in_order() -> None:
    struct = {
        "title": "Тест",
        "verse1": ["раз"],
        "verse2": ["два"],
        "verse3": ["три"],
        "chorus": ["хук"],
    }

    text = _struct_to_text(struct)

    assert text.index("[verse 1]") < text.index("[verse 2]") < text.index("[verse 3]")
    assert "[verse 3]" in text and "три" in text
    assert "[hook]" in text


def test_text_to_struct_keeps_legacy_keys_and_adds_list() -> None:
    raw = "[verse 1]\nпервая строка\nвторая строка\n[hook]\nприпев\n[verse 2]\nтретья строка"

    struct = _text_to_struct(raw, "drift_phonk")

    assert struct["verse1"] and struct["verse2"] and struct["chorus"]
    assert "verses" in struct, "новый рендер читает список куплетов"
    assert len(struct["verses"]) == 2


def test_fallback_text_round_trips_through_parser() -> None:
    fallback = _fallback_lyrics("тема", "drift_phonk", n_verses=3)

    text = _struct_to_text(fallback)
    reparsed = _text_to_struct(text, "drift_phonk")

    assert len(reparsed["verses"]) == 3, text
