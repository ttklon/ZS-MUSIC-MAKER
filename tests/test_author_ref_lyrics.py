# -*- coding: utf-8 -*-
"""`modules/author_ref_lyrics.py`: корпус автора, стилевой профиль, промт.

Модуль достижим — его зовёт `modules/lyrics/author.py` при генерации «в стиле
автора» — а покрыт был на 17 %. Работа с диском идёт во временном каталоге:
настоящий `lyric_vault/` тесты не трогают.

Whisper и поиск в сети подменяются. Реальное распознавание речи и реальные
запросы к DuckDuckGo здесь не проверяются; проверяется наша логика, включая
сетевую политику проекта (T15): без явного разрешения запрос уходить не должен.
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest

from modules import author_ref_lyrics as author_ref


@pytest.fixture(autouse=True)
def isolated_dirs(tmp_path, monkeypatch):
    """Все каталоги модуля — во временной папке; репозиторий не трогаем."""
    corpus = tmp_path / "corpus"
    styles = tmp_path / "styles"
    corpus.mkdir()
    styles.mkdir()
    monkeypatch.setattr(author_ref, "CORPUS_DIR", corpus)
    monkeypatch.setattr(author_ref, "STYLE_DIR", styles)
    monkeypatch.setattr(author_ref, "CACHE_FILE", tmp_path / "index.json")
    monkeypatch.setattr(author_ref, "ROOT", tmp_path)
    return tmp_path


TEXT = (
    "Ночь, тачка, движ\n"
    "мы летим в тишине\n"
    "огонь в глазах горит\n"
    "и город спит во сне\n"
    "Ночь, тачка, движ\n"
    "асфальт под колёсами\n"
    "мы дышим скоростью\n"
    "и небо над нами\n"
)


# --------------------------------------------------------------------------- #
#  Утилиты
# --------------------------------------------------------------------------- #

def test_tokenize_lowercases_and_drops_punctuation() -> None:
    assert author_ref._tokenize("Ночь, тачка! Движ-2024") == ["ночь", "тачка", "движ", "2024"]
    assert author_ref._tokenize("") == []
    assert author_ref._tokenize(None) == []


@pytest.mark.parametrize(
    "word,expected",
    [("ночь", 1), ("тачка", 2), ("движение", 4), ("!!!", 1), ("fly", 1)],
)
def test_syllables_are_never_zero(word, expected) -> None:
    assert author_ref._syllables_ru(word) == expected


# --------------------------------------------------------------------------- #
#  Индексация
# --------------------------------------------------------------------------- #

def test_ingest_text_creates_corpus_file_and_index() -> None:
    result = author_ref.ingest_lyrics_text(TEXT, author="Тест", title="Ночь")

    assert result["ok"] is True
    assert result["author"] == "тест"
    corpus_file = author_ref.CORPUS_DIR / "тест" / f"{result['id']}.txt"
    assert corpus_file.read_text(encoding="utf-8") == TEXT
    index = json.loads(author_ref.CACHE_FILE.read_text(encoding="utf-8"))
    assert index["тест"]["display_name"] == "Тест"
    assert index["тест"]["files"][0]["title"] == "Ночь"


def test_ingest_missing_file_is_refused(isolated_dirs) -> None:
    result = author_ref.ingest_lyrics_file(isolated_dirs / "nope.txt", author="Тест")

    assert result["ok"] is False
    assert "file not found" in result["error"]


def test_ingest_file_uses_stem_as_title(isolated_dirs) -> None:
    path = isolated_dirs / "Мой текст.txt"
    path.write_text(TEXT, encoding="utf-8")

    result = author_ref.ingest_lyrics_file(path, author="Автор")

    index = json.loads(author_ref.CACHE_FILE.read_text(encoding="utf-8"))
    assert index[result["author"]]["files"][0]["title"] == "Мой текст"


def test_repeated_ingest_does_not_duplicate_index_record() -> None:
    """Тот же текст дважды — один файл и одна запись, а не две.

    Файл дедуплицируется по хешу (`fname`), а запись раньше добавлялась каждый
    раз: `list_authors()` показывал «файлов: 2» при одном файле на диске.
    """
    first = author_ref.ingest_lyrics_text(TEXT, author="Тест", title="Ночь")
    second = author_ref.ingest_lyrics_text(TEXT, author="Тест", title="Ночь")

    assert first["id"] == second["id"]
    files = list((author_ref.CORPUS_DIR / "тест").glob("*.txt"))
    assert len(files) == 1
    index = json.loads(author_ref.CACHE_FILE.read_text(encoding="utf-8"))
    assert len(index["тест"]["files"]) == 1
    assert author_ref.list_authors() == [{"slug": "тест", "name": "Тест", "files": 1}]


def test_different_titles_are_separate_entries() -> None:
    author_ref.ingest_lyrics_text(TEXT, author="Тест", title="Ночь")
    author_ref.ingest_lyrics_text(TEXT + "\nдругая строка", author="Тест", title="Утро")

    assert author_ref.list_authors()[0]["files"] == 2


def test_broken_index_file_does_not_break_ingest() -> None:
    author_ref.CACHE_FILE.write_text("{ битый json", encoding="utf-8")

    result = author_ref.ingest_lyrics_text(TEXT, author="Тест", title="Ночь")

    assert result["ok"] is True
    index = json.loads(author_ref.CACHE_FILE.read_text(encoding="utf-8"))
    assert "тест" in index


def test_ingest_reference_audio_without_file_is_refused(isolated_dirs) -> None:
    result = author_ref.ingest_reference_audio(isolated_dirs / "gone.mp3")

    assert result["ok"] is False and result["error"] == "no audio"


def test_ingest_reference_audio_uses_transcription(isolated_dirs, monkeypatch) -> None:
    audio = isolated_dirs / "ref.mp3"
    audio.write_bytes(b"ID3" + b"\0" * 32)

    class Model:
        def transcribe(self, path, fp16=False):
            return {"text": "  распознанный текст песни  "}

    monkeypatch.setitem(sys.modules, "whisper", types.SimpleNamespace(
        load_model=lambda name: Model()))

    result = author_ref.ingest_reference_audio(audio, author="Автор", title="Трек")

    assert result["ok"] is True
    stored = (author_ref.CORPUS_DIR / "автор" / f"{result['id']}.txt").read_text(encoding="utf-8")
    assert stored == "распознанный текст песни"


def test_ingest_reference_audio_reports_empty_transcription(isolated_dirs, monkeypatch) -> None:
    audio = isolated_dirs / "ref.mp3"
    audio.write_bytes(b"ID3")
    monkeypatch.setitem(sys.modules, "whisper", types.SimpleNamespace(
        load_model=lambda name: types.SimpleNamespace(transcribe=lambda *a, **k: {"text": "   "})))

    result = author_ref.ingest_reference_audio(audio)

    assert result["ok"] is False and result["error"] == "empty transcription"


def test_ingest_reference_audio_reports_missing_whisper(isolated_dirs, monkeypatch) -> None:
    audio = isolated_dirs / "ref.mp3"
    audio.write_bytes(b"ID3")
    monkeypatch.setitem(sys.modules, "whisper", None)

    result = author_ref.ingest_reference_audio(audio)

    assert result["ok"] is False
    assert result["error"].startswith("whisper failed:")


# --------------------------------------------------------------------------- #
#  Стилевой профиль
# --------------------------------------------------------------------------- #

def test_profile_without_corpus_is_refused() -> None:
    result = author_ref.build_style_profile("Никого")

    assert result["ok"] is False
    assert "нет корпуса" in result["error"]


def test_profile_needs_more_than_five_tokens() -> None:
    author_ref.ingest_lyrics_text("ночь", author="Мало", title="x")

    result = author_ref.build_style_profile("Мало")

    assert result["ok"] is False and result["error"] == "слишком мало данных"


def test_profile_collects_words_bigrams_and_rhymes() -> None:
    author_ref.ingest_lyrics_text(TEXT, author="Тест", title="Ночь")

    result = author_ref.build_style_profile("Тест")

    profile = result["profile"]
    assert result["ok"] is True
    words = [item["w"] for item in profile["top_words"]]
    assert "ночь" in words and "тачка" in words
    assert "и" not in words, "стоп-слова не должны попадать в характерные"
    assert profile["avg_syll_per_line"] > 0
    assert profile["rhyme_endings"]
    # профиль склеивает файлы через "\n" — символ-разделитель тоже считается
    assert profile["corpus_size_chars"] == len(TEXT) + 1
    assert (author_ref.STYLE_DIR / "тест.json").is_file()


def test_profile_ignores_lines_without_words() -> None:
    author_ref.ingest_lyrics_text(TEXT + "\n!!!\n???\n", author="Тест", title="x")

    profile = author_ref.build_style_profile("Тест")["profile"]

    assert all(line.strip() for line in profile["sample_lines"])


def test_get_profile_builds_on_first_access() -> None:
    author_ref.ingest_lyrics_text(TEXT, author="Тест", title="Ночь")

    profile = author_ref.get_style_profile("Тест")

    assert profile is not None and profile["author_slug"] == "тест"


def test_get_profile_returns_none_for_unknown_author() -> None:
    assert author_ref.get_style_profile("Никого") is None


def test_get_profile_survives_broken_cache() -> None:
    author_ref.ingest_lyrics_text(TEXT, author="Тест", title="Ночь")
    (author_ref.STYLE_DIR / "тест.json").write_text("{ битый", encoding="utf-8")

    assert author_ref.get_style_profile("Тест") is None


# --------------------------------------------------------------------------- #
#  Промт
# --------------------------------------------------------------------------- #

def test_prompt_contains_theme_words_and_profile() -> None:
    author_ref.ingest_lyrics_text(TEXT, author="Тест", title="Ночь")

    prompt = author_ref.build_style_prompt(
        "Тест", theme="ночной драйв", user_words=["мерседес"], bpm=140, target_lines=12
    )

    assert "в стиле «Тест»" in prompt
    assert "мерседес" in prompt
    assert "BPM трека: 140" in prompt
    assert "12 строк" in prompt
    assert "[Куплет 1]" in prompt
    assert "ночь" in prompt


def test_prompt_for_unknown_author_has_no_fake_style() -> None:
    prompt = author_ref.build_style_prompt(
        "Никого", theme="тема", user_words=[], bpm=90
    )

    assert "(нет)" in prompt, "пустой список слов честно показан как «нет»"
    assert "Характерные слова" not in prompt
    assert "Характерные обороты" not in prompt


# --------------------------------------------------------------------------- #
#  Сеть (T15): по умолчанию запросов нет
# --------------------------------------------------------------------------- #

def test_online_search_is_refused_without_permission(monkeypatch) -> None:
    """Сеть выключена по умолчанию: без разрешения запрос не уходит."""
    called: list = []
    monkeypatch.setattr(
        "app.core.net_policy.network_allowed", lambda allow_online=False, settings_path=None: False
    )
    import urllib.request

    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: called.append(a))

    hits = author_ref.search_author_online("Кто-то")

    assert called == [], "запрос в сеть ушёл без разрешения пользователя"
    assert hits[0]["error"].startswith("offline")
    assert hits and "error" in hits[0]
    assert "offline" in hits[0]["error"].lower() or "сеть" in hits[0]["error"].lower()


def test_online_search_parses_results_when_allowed(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.core.net_policy.network_allowed", lambda allow_online=False, settings_path=None: True
    )
    html = (
        '<a class="result__a" href="https://example.com/1">Трек один</a>'
        '<a class="result__snippet">первый сниппет про ночь и тачку</a>'
        '<a class="result__a" href="https://example.com/2">Трек два</a>'
        '<a class="result__snippet">второй сниппет про город и огни</a>'
    )

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return html.encode("utf-8")

    import urllib.request

    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: Response())

    hits = author_ref.search_author_online("Кто-то", max_tracks=2)

    assert [h["title"] for h in hits] == ["Трек один", "Трек два"]
    assert hits[0]["url"] == "https://example.com/1"
    assert "сниппет" in hits[0]["snippet"]


def test_online_search_reports_network_error(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.core.net_policy.network_allowed", lambda allow_online=False, settings_path=None: True
    )
    import urllib.request

    def boom(*a, **k):
        raise OSError("нет маршрута")

    monkeypatch.setattr(urllib.request, "urlopen", boom)

    hits = author_ref.search_author_online("Кто-то")

    assert "error" in hits[0] and "нет маршрута" in hits[0]["error"]


def test_fetch_and_ingest_keeps_only_long_snippets(monkeypatch) -> None:
    monkeypatch.setattr(author_ref, "search_author_online", lambda author, max_tracks=20: [
        {"title": "короткий", "snippet": "мало", "url": "u1"},
        {"title": "нормальный", "snippet": "достаточно длинный сниппет для стиля автора", "url": "u2"},
        {"error": "нет сети"},
    ])

    result = author_ref.fetch_and_ingest_author("Тест", max_tracks=5)

    assert result["ok"] is True
    assert result["ingested"] == 1


def test_fetch_and_ingest_without_hits_is_honest(monkeypatch) -> None:
    monkeypatch.setattr(author_ref, "search_author_online", lambda *a, **k: [{"error": "offline"}])

    result = author_ref.fetch_and_ingest_author("Тест")

    assert result["ok"] is False and result["ingested"] == 0


# --------------------------------------------------------------------------- #
#  Обход библиотеки и список авторов
# --------------------------------------------------------------------------- #

def test_scan_library_collects_references_and_vault(isolated_dirs, monkeypatch) -> None:
    refs = isolated_dirs / "references"
    (refs / "Мой автор").mkdir(parents=True)
    (refs / "Мой автор" / "трек.mp3").write_bytes(b"ID3")
    vault = isolated_dirs / "lyric_vault"
    vault.mkdir()
    (vault / "стих.txt").write_text(TEXT, encoding="utf-8")
    (vault / "slang_ru.txt").write_text("сленг", encoding="utf-8")

    monkeypatch.setattr(author_ref, "ingest_reference_audio",
                        lambda path, author="", title="": {"ok": True})

    result = author_ref.scan_library(references_dir=refs, vault_dir=vault)

    assert result["audio_ingested"] == 1
    assert result["text_ingested"] == 1, "файл со сленгом пропускается, обычный — нет"


def test_scan_library_skips_author_corpus(isolated_dirs) -> None:
    vault = isolated_dirs / "lyric_vault"
    inside = author_ref.CORPUS_DIR / "тест"
    inside.mkdir(parents=True)
    (inside / "already.txt").write_text(TEXT, encoding="utf-8")
    vault.mkdir()

    result = author_ref.scan_library(references_dir=isolated_dirs / "none", vault_dir=author_ref.CORPUS_DIR)

    assert result["text_ingested"] == 0


def test_fetch_stops_at_max_tracks(monkeypatch) -> None:
    monkeypatch.setattr(author_ref, "search_author_online", lambda *a, **k: [
        {"title": f"t{i}", "snippet": "достаточно длинный сниппет для профиля автора номер " + str(i)}
        for i in range(5)
    ])

    result = author_ref.fetch_and_ingest_author("Тест", max_tracks=2)

    assert result["ingested"] == 2


# --------------------------------------------------------------------------- #
#  CLI модуля
# --------------------------------------------------------------------------- #

def _run_cli(capsys, argv: list[str]) -> dict | list:
    """CLI вызывается напрямую: `runpy` создал бы модуль заново с путями репозитория."""
    author_ref.main(argv)
    return json.loads(capsys.readouterr().out)


def test_cli_without_arguments_lists_authors(capsys) -> None:
    assert _run_cli(capsys, []) == []


def test_cli_profile_builds_and_prints(capsys) -> None:
    author_ref.ingest_lyrics_text(TEXT, author="Тест", title="Ночь")

    payload = _run_cli(capsys, ["profile", "Тест"])

    assert payload["ok"] is True
    assert payload["profile"]["author_slug"] == "тест"


def test_cli_with_profile_but_no_author_falls_back_to_list(capsys) -> None:
    assert _run_cli(capsys, ["profile"]) == []


def test_cli_scan_reports_counts(capsys, monkeypatch, isolated_dirs) -> None:
    (isolated_dirs / "references").mkdir()
    monkeypatch.setattr(author_ref, "scan_library",
                        lambda: {"ok": True, "audio_ingested": 0, "text_ingested": 0})

    payload = _run_cli(capsys, ["scan"])

    assert payload["ok"] is True


def test_module_main_returns_zero() -> None:
    assert author_ref.main(["scan"]) == 0


def test_script_entrypoint_runs(monkeypatch, capsys) -> None:
    """`python modules/author_ref_lyrics.py` — отдельная строка запуска."""
    import runpy

    monkeypatch.setattr(sys, "argv", ["author_ref_lyrics.py"])
    monkeypatch.delitem(sys.modules, "modules.author_ref_lyrics", raising=False)
    with pytest.raises(SystemExit) as exit_info:
        runpy.run_module("modules.author_ref_lyrics", run_name="__main__")

    assert exit_info.value.code == 0
