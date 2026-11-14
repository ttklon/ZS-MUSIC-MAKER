# -*- coding: utf-8 -*-
"""`agents/trend_scout.py`: сеть по умолчанию выключена (T15) и кэш трендов.

Модуль зовётся генерацией текста (`modules/lyrics/author.py`) и до этой правки
ходил в DuckDuckGo и Reddit напрямую: проверялся только флаг `offline_only`,
которого вызывающий код не передаёт. Правило проекта из `app/core/net_policy.py`
— «сеть выключена, пока пользователь явно не разрешил» — не выполнялось.

Проверяется наша логика: когда запрос уходит, когда нет, что попадает в кэш и
что попадает в отчёт. Реальные сетевые ответы здесь не получаются и не
имитируются как «live»: ответы подменены.
"""

from __future__ import annotations

import json
import time

import pytest

from agents import trend_scout


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    cache = tmp_path / "trends_cache.json"
    monkeypatch.setattr(trend_scout, "CACHE_FILE", cache)
    monkeypatch.setattr(trend_scout, "SLANG_FILE", tmp_path / "slang.txt")
    return cache


@pytest.fixture
def no_network(monkeypatch):
    """Сеть запрещена политикой — как на чистой машине без data/settings.json."""
    # как настоящая политика: явное allow_online=True снимает запрет
    monkeypatch.setattr(
        "app.core.net_policy.network_allowed",
        lambda allow_online=False, settings_path=None: allow_online is True,
    )
    return monkeypatch


@pytest.fixture
def network_on(monkeypatch):
    monkeypatch.setattr(
        "app.core.net_policy.network_allowed",
        lambda allow_online=False, settings_path=None: True,
    )
    return monkeypatch


def _spy(monkeypatch) -> list:
    calls: list = []
    monkeypatch.setattr(
        trend_scout, "_duckduckgo_search",
        lambda query, max_results=5: calls.append(("ddg", query)) or ["сниппет тренд"],
    )
    monkeypatch.setattr(
        trend_scout, "_reddit_hot",
        lambda subreddit, limit=5: calls.append(("reddit", subreddit)) or ["reddit пост"],
    )
    return calls


# --------------------------------------------------------------------------- #
#  Сеть по умолчанию выключена
# --------------------------------------------------------------------------- #

def test_scout_does_not_touch_network_without_permission(no_network) -> None:
    calls = _spy(no_network)

    report = trend_scout.scout("drift phonk")

    assert calls == [], "запрос в сеть ушёл без разрешения пользователя"
    assert report["external_snippets"] == []
    assert report["hype_words"], "офлайн-словарь обязан остаться"


def test_slang_for_prompt_works_offline(no_network) -> None:
    calls = _spy(no_network)

    words = trend_scout.actual_slang_for_prompt("drift phonk", n_words=5)

    assert calls == []
    assert words and all(isinstance(w, str) for w in words)


def test_offline_only_flag_still_works(network_on) -> None:
    calls = _spy(network_on)

    report = trend_scout.scout("drift phonk", offline_only=True)

    assert calls == []
    assert report["external_snippets"] == []


def test_network_is_used_when_allowed(network_on) -> None:
    calls = _spy(network_on)

    report = trend_scout.scout("drift phonk")

    assert any(kind == "ddg" for kind, _ in calls)
    assert any(kind == "reddit" for kind, _ in calls)
    assert "сниппет тренд" in report["external_snippets"]
    assert "reddit пост" in report["external_snippets"]


def test_explicit_allow_online_overrides_policy(no_network) -> None:
    calls = _spy(no_network)

    trend_scout.scout("drift phonk", allow_online=True)

    assert calls, "явное разрешение вызова обязано снимать запрет политики"


# --------------------------------------------------------------------------- #
#  Кэш и честность отчёта
# --------------------------------------------------------------------------- #

def test_report_marks_offline_run(no_network) -> None:
    report = trend_scout.scout("drift phonk")

    assert report["offline"] is True
    assert report["reason"]
    assert "сеть" in report["reason"].lower() or "offline" in report["reason"].lower()


def test_report_marks_online_run(network_on) -> None:
    report = trend_scout.scout("drift phonk")

    assert report["offline"] is False


def test_second_call_uses_cache_and_does_not_refetch(network_on) -> None:
    calls = _spy(network_on)
    trend_scout.scout("drift phonk")
    first = len(calls)

    trend_scout.scout("drift phonk")

    assert len(calls) == first, "кэш на 24 часа должен снимать повторные запросы"


def test_offline_result_is_cached_too(isolated_cache, no_network) -> None:
    trend_scout.scout("drift phonk")

    payload = json.loads(isolated_cache.read_text(encoding="utf-8"))
    assert payload
    stored = next(iter(payload.values()))
    assert stored["data"]["offline"] is True


def test_stale_cache_is_refetched(network_on) -> None:
    calls = _spy(network_on)
    trend_scout.scout("drift phonk")
    payload = json.loads(trend_scout.CACHE_FILE.read_text(encoding="utf-8"))
    for entry in payload.values():
        entry["ts"] = time.time() - 90_000  # старше суток
    trend_scout.CACHE_FILE.write_text(json.dumps(payload), encoding="utf-8")
    before = len(calls)

    trend_scout.scout("drift phonk")

    assert len(calls) > before


def test_broken_cache_is_not_fatal(isolated_cache, no_network) -> None:
    isolated_cache.write_text("{ битый", encoding="utf-8")

    report = trend_scout.scout("drift phonk")

    assert report["hype_words"]


def test_snippets_are_deduplicated(network_on) -> None:
    network_on.setattr(
        trend_scout, "_duckduckgo_search", lambda query, max_results=5: ["один и тот же"]
    )
    network_on.setattr(
        trend_scout, "_reddit_hot", lambda subreddit, limit=5: ["один и тот же"]
    )

    report = trend_scout.scout("drift phonk")

    assert report["external_snippets"] == ["один и тот же"]


def test_network_errors_do_not_break_scout(network_on) -> None:
    network_on.setattr(
        trend_scout, "_duckduckgo_search",
        lambda *a, **k: (_ for _ in ()).throw(OSError("нет маршрута")),
    )
    network_on.setattr(
        trend_scout, "_reddit_hot",
        lambda *a, **k: (_ for _ in ()).throw(OSError("нет маршрута")),
    )

    report = trend_scout.scout("drift phonk")

    assert report["external_snippets"] == []
    assert report["hype_words"], "офлайн-словарь не должен зависеть от сети"


# --------------------------------------------------------------------------- #
#  Поиск сэмплов: защита стоит в вызывающем коде — закрепляем её
# --------------------------------------------------------------------------- #

def test_sample_hunter_does_not_search_web_without_permission(monkeypatch) -> None:
    """`agents/sample_hunter/web.py` сам политику не спрашивает: её спрашивает
    `hunter.hunt`. Если эту проверку уберут, тест упадёт."""
    from agents.sample_hunter import hunter

    called: list = []
    monkeypatch.setattr(
        hunter, "_search_online_with_diagnostics",
        lambda *a, **k: called.append(a) or ([], {}),
    )
    monkeypatch.setattr(
        "app.core.net_policy.network_allowed",
        lambda allow_online=False, settings_path=None: allow_online is True,
    )
    monkeypatch.setattr(hunter, "list_local", lambda query: [])

    result = hunter.hunt("cowbell", allow_online=False)

    assert called == [], "онлайн-поиск сэмплов ушёл без разрешения"
    assert result.get("offline") is not False


def test_sample_hunter_searches_when_allowed(monkeypatch) -> None:
    from agents.sample_hunter import hunter

    called: list = []
    monkeypatch.setattr(
        hunter, "_search_online_with_diagnostics",
        lambda query, max_results, diagnostics: called.append(query)
        or ([{"license": "cc0", "title": "cowbell", "url": "u"}], {}),
    )
    monkeypatch.setattr(
        "app.core.net_policy.network_allowed",
        lambda allow_online=False, settings_path=None: allow_online is True,
    )
    monkeypatch.setattr(hunter, "list_local", lambda query: [])
    monkeypatch.setattr(hunter, "_license_gate", lambda items: items, raising=False)

    hunter.hunt("cowbell", allow_online=True)

    assert called == ["cowbell"]
