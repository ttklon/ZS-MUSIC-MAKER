"""T4: онлайн-поиск сэмплов действительно работает и честно сообщает о сбоях.

До доработки `agents/sample_hunter/web.py` использовал `re`, `json` и `os`
без импортов: каждый парсер падал с `NameError`, а `search_online()` глотал
исключение — онлайн-результат всегда был пустым при внешне рабочем коде.

Тесты работают на фикстурах: сеть не нужна, `_http_get` подменяется.
"""

from __future__ import annotations

import json

import pytest

from agents.sample_hunter import config, web
from agents.sample_hunter.hunter import hunt, search_online


FREESOUND_HTML = """
<a href="/people/demo/sounds/12345/">Vinyl kick 808</a>
<a href="/people/demo/sounds/67890/">Phonk cowbell</a>
"""

WIKIMEDIA_JSON = json.dumps(
    {
        "query": {
            "search": [
                {"title": "File:Kick drum.wav"},
                {"title": "File:Diagram.png"},
                {"title": "File:Snare.ogg"},
            ]
        }
    }
)

ARCHIVE_JSON = json.dumps(
    {
        "response": {
            "docs": [
                {"identifier": "demo_audio", "title": "Demo audio", "licenseurl": "https://creativecommons.org/publicdomain/zero/1.0/"},
                {"identifier": "no_license", "title": "Unknown", "licenseurl": ""},
            ]
        }
    }
)

PIXABAY_JSON = json.dumps(
    {"hits": [{"title": "Night loop", "audio": "https://cdn.example/night.mp3", "tags": "night,drive"}]}
)


@pytest.fixture
def fake_net(monkeypatch):
    """Подменить сеть: каждый источник отдаёт свой фиксированный ответ."""
    calls: list[str] = []

    def fake_get(url: str, timeout: float = 6.0):
        calls.append(url)
        if "freesound.org" in url:
            return FREESOUND_HTML
        if "commons.wikimedia.org" in url:
            return WIKIMEDIA_JSON
        if "archive.org" in url:
            return ARCHIVE_JSON
        if "pixabay.com" in url:
            return PIXABAY_JSON
        return None

    monkeypatch.setattr(web, "_http_get", fake_get)
    monkeypatch.setattr(web, "HAS_REQ", True)
    monkeypatch.setenv("PIXABAY_API_KEY", "test-key")
    return calls


# ------------------------------------------------------------------ парсеры
def test_freesound_parser_reads_html(fake_net) -> None:
    hits = web.search_freesound_web("kick")

    assert [hit["id"] for hit in hits] == ["12345", "67890"]
    assert hits[0]["license"] == "CC0"
    assert hits[0]["url"].startswith("https://freesound.org/people/")


def test_wikimedia_parser_filters_non_audio(fake_net) -> None:
    hits = web.search_wikimedia("kick")

    assert len(hits) == 2
    assert all(not hit["name"].endswith(".png") for hit in hits)


def test_archive_parser_reads_json(fake_net) -> None:
    hits = web.search_archive_org("kick")

    assert [hit["id"] for hit in hits] == ["demo_audio", "no_license"]


def test_pixabay_needs_a_key(monkeypatch) -> None:
    monkeypatch.delenv("PIXABAY_API_KEY", raising=False)

    assert web.search_pixabay("kick") == []


def test_pixabay_parser_reads_json(fake_net) -> None:
    hits = web.search_pixabay("kick")

    assert hits and hits[0]["name"] == "Night loop"


def test_broken_json_is_not_a_crash(monkeypatch) -> None:
    monkeypatch.setattr(web, "_http_get", lambda *a, **k: "<html>not json</html>")
    monkeypatch.setattr(web, "HAS_REQ", True)

    assert web.search_wikimedia("kick") == []
    assert web.search_archive_org("kick") == []


# ------------------------------------------------------------------ поиск
def test_search_online_returns_hits(fake_net) -> None:
    hits = search_online("kick", limit=5)

    assert hits, "онлайн-поиск вернул пустой список при рабочем источнике"
    assert {hit["source"] for hit in hits} >= {"freesound_cc0"}


def test_search_online_reports_failures(monkeypatch) -> None:
    """Сбой источника попадает в диагностику, а не исчезает молча."""
    def boom(*args, **kwargs):
        raise RuntimeError("DNS is down")

    monkeypatch.setattr(web, "search_freesound_web", boom)
    monkeypatch.setattr(web, "search_wikimedia", lambda *a, **k: [])
    monkeypatch.setattr(web, "search_archive_org", lambda *a, **k: [])
    monkeypatch.setattr(web, "search_pixabay", lambda *a, **k: [])

    diagnostics: dict = {}
    hits = search_online("kick", diagnostics_out=diagnostics)

    assert hits == []
    assert diagnostics["freesound_cc0"]["error"].startswith("RuntimeError: DNS is down")
    assert "wikimedia" not in diagnostics


def test_license_gate_blocks_nc_and_unknown() -> None:
    from agents.sample_hunter.license import _license_gate

    items = [
        {"source": "freesound_cc0", "license": "CC0"},
        {"source": "wikimedia", "license": "CC-BY-SA"},
        {"source": "archive.org", "license": "unknown"},
    ]

    passed = _license_gate(items)

    assert [item["license"] for item in passed] == ["CC0"]


# ------------------------------------------------------------------ API
def test_hunt_exposes_total(fake_net) -> None:
    result = hunt("kick", max_results=5)

    assert "total" in result, "hunt() не отдаёт total — потребитель получает KeyError"
    assert result["total"] == len(result["samples"])
    assert result["total"] >= len(result["online"])


def test_hunt_without_online_keeps_local_split(monkeypatch) -> None:
    monkeypatch.setattr("agents.sample_hunter.hunter.list_local", lambda *a, **k: [{"name": "local.wav"}])

    result = hunt("kick", allow_online=False)

    assert result["online"] == []
    assert result["total"] == 1


def test_audio_extensions_are_declared_once() -> None:
    import ast
    from pathlib import Path

    tree = ast.parse(Path(config.__file__).read_text(encoding="utf-8"))
    assignments = [
        node for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "AUDIO_EXT" for target in node.targets)
    ]

    assert len(assignments) == 1, "AUDIO_EXT объявлен дважды — второе объявление мёртвое"

# ------------------------------------------------------------------ лицензии
def test_pixabay_hit_is_not_blocked_by_own_gate(fake_net) -> None:
    """Парсер отдаёт "Royalty-Free (Pixabay)" — гейт обязан это пропустить.

    До исправления `license_manager.normalize` уходил в ветку «URL» из-за
    скобок и возвращал "unknown": единственный законный результат Pixabay
    блокировался собственным фильтром, источник был мёртвым по построению.
    """
    from agents.sample_hunter.license import _license_gate

    hits = web.search_pixabay("kick")

    assert hits, "парсер ничего не вернул"
    assert _license_gate(hits) == hits


def test_wikimedia_hits_are_reported_but_blocked_by_sa() -> None:
    """CC-BY-SA остаётся блокируемой: политика не «расширена» вместе с фиксом."""
    from agents.sample_hunter.license import _license_gate

    items = [{"source": "wikimedia", "license": "CC-BY-SA / PD"}]

    passed = _license_gate(items)

    assert passed == []
    assert items[0]["license_blocked"] is True
    assert items[0]["license_reason"].startswith("blocked by license gate")

def test_without_requests_library_every_source_is_empty(monkeypatch) -> None:
    """Без `requests` источники молчат, но не падают: поиск не должен ронять hunt."""
    monkeypatch.setattr(web, "HAS_REQ", False)

    assert web._http_get("https://example.invalid") is None
    assert web.search_freesound_web("kick") == []
    assert web.search_wikimedia("kick") == []
    assert web.search_archive_org("kick") == []
    assert web.search_pixabay("kick") == []


def test_non_200_is_treated_as_no_answer(monkeypatch) -> None:
    class _Resp:
        status_code = 503
        text = "<html>maintenance</html>"

    monkeypatch.setattr(web, "HAS_REQ", True)
    monkeypatch.setattr(web, "requests", type("R", (), {"get": staticmethod(lambda *a, **k: _Resp())}))

    assert web._http_get("https://example.invalid") is None


def test_request_exception_is_treated_as_no_answer(monkeypatch) -> None:
    def boom(*args, **kwargs):
        raise OSError("connection reset")

    monkeypatch.setattr(web, "HAS_REQ", True)
    monkeypatch.setattr(web, "requests", type("R", (), {"get": staticmethod(boom)}))

    assert web._http_get("https://example.invalid") is None
    assert web.search_freesound_web("kick") == []

def test_http_get_returns_body_on_200(monkeypatch) -> None:
    class _Resp:
        status_code = 200
        text = "ok-body"

    monkeypatch.setattr(web, "HAS_REQ", True)
    monkeypatch.setattr(web, "requests", type("R", (), {"get": staticmethod(lambda *a, **k: _Resp())}))

    assert web._http_get("https://example.invalid") == "ok-body"


def test_dead_network_makes_every_parser_empty(monkeypatch) -> None:
    """Сеть недоступна → источники пусты, а не исключение наверх."""
    monkeypatch.setattr(web, "HAS_REQ", True)
    monkeypatch.setattr(web, "_http_get", lambda *a, **k: None)

    assert web.search_freesound_web("kick") == []
    assert web.search_wikimedia("kick") == []
    assert web.search_archive_org("kick") == []
    assert web.search_pixabay("kick") == []


def test_pixabay_broken_json_is_not_a_crash(monkeypatch) -> None:
    monkeypatch.setenv("PIXABAY_API_KEY", "k")
    monkeypatch.setattr(web, "HAS_REQ", True)
    monkeypatch.setattr(web, "_http_get", lambda *a, **k: "<html>not json</html>")

    assert web.search_pixabay("kick") == []


def test_pixabay_with_key_but_no_answer_is_empty(monkeypatch) -> None:
    monkeypatch.setenv("PIXABAY_API_KEY", "k")
    monkeypatch.setattr(web, "HAS_REQ", True)
    monkeypatch.setattr(web, "_http_get", lambda *a, **k: None)

    assert web.search_pixabay("kick") == []

def test_archive_entry_without_identifier_is_skipped(monkeypatch) -> None:
    import json as _json

    payload = _json.dumps({"response": {"docs": [{"title": "без id"}, {"identifier": "ok"}]}})
    monkeypatch.setattr(web, "HAS_REQ", True)
    monkeypatch.setattr(web, "_http_get", lambda *a, **k: payload)

    hits = web.search_archive_org("kick")

    assert [hit["id"] for hit in hits] == ["ok"]
