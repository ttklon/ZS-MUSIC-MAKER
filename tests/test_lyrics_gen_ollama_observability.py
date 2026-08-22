"""Regression coverage for observable local Ollama lyric fallback."""

from modules import lyrics_gen


def test_ollama_reports_unavailable_service(monkeypatch):
    import requests

    monkeypatch.setattr(
        requests,
        "post",
        lambda *args, **kwargs: (_ for _ in ()).throw(requests.ConnectionError("offline")),
    )

    result = lyrics_gen._try_ollama_with_diagnostics("hook")

    assert result == {
        "text": None,
        "status": "unavailable",
        "error": "ConnectionError: offline",
    }
    assert lyrics_gen._try_ollama("hook") is None


def test_ollama_reports_real_nonempty_response(monkeypatch):
    import requests

    class _Response:
        status_code = 200

        @staticmethod
        def json():
            return {"response": "  generated hook  "}

    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: _Response())

    assert lyrics_gen._try_ollama_with_diagnostics("hook") == {
        "text": "generated hook",
        "status": "responded",
    }
