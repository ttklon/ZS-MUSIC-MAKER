"""The wrapper must not run unused LLM and MusicGen generations before rendering."""
from copy import deepcopy

import pytest

from modules.hit_factory import breakthrough, generator


@pytest.fixture
def setup_wrapper(tmp_path, monkeypatch):
    monkeypatch.setattr(breakthrough, "analyze_references", lambda paths: {"ok": False})
    monkeypatch.setattr(breakthrough, "build_artist_dossier", lambda *a: {"hype_words": ["ночной город"]})
    monkeypatch.setattr(breakthrough, "prepare_voice", lambda *a, **kw: {"ok": False, "reason": "no recording"})
    monkeypatch.setattr(breakthrough, "_guard_memory", lambda: None)
    for function in ("generate_lyrics_in_style", "generate_beats_with_style"):
        monkeypatch.setattr(breakthrough, function,
                            lambda *a, **kw: pytest.fail("unused preliminary inference must not run"))
    calls = []
    result = {
        "master_path": None, "report": {"verdict": "PARTIAL", "stages": [
            {"name": "_stage_lyrics", "status": "OK", "output": {
                "ok": True, "text": "Текст выбранной попытки", "provider": "actual local model"}},
            {"name": "_stage_beat", "status": "FALLBACK", "reason": "procedural requested",
             "output": {"ok": True, "path": "selected-beat.wav", "engine": "procedural"}},
        ]},
    }

    class Factory:
        def __init__(self, **kwargs):
            pass

        def make_one(self, *args, **kwargs):
            calls.append((args, kwargs))
            return deepcopy(result)

    monkeypatch.setattr(generator, "HitFactory", Factory)
    return calls, result


def test_wrapper_uses_only_selected_pipeline_outputs(setup_wrapper):
    calls, hit = setup_wrapper
    result = breakthrough.full_orchestrate(artist="My artist", theme="Моя тема", breakthrough=False)
    assert len(calls) == 1
    assert calls[0][0][1] == "Моя тема"
    assert result["lyrics"]["text"] == "Текст выбранной попытки"
    assert result["lyrics"]["provider"] == "actual local model"
    assert result["beats"]["path"] == "selected-beat.wav"
    assert result["beats"]["stage_status"] == "FALLBACK"


def test_theme_from_dossier_does_not_require_extra_generation(setup_wrapper):
    calls, hit = setup_wrapper
    result = breakthrough.full_orchestrate(theme=None, breakthrough=False)
    assert result["theme"] == "ночной город"
    assert calls[0][0][1] == "ночной город"


@pytest.mark.parametrize("status", ["BLOCKED", "FAILED"])
def test_failed_stage_cannot_look_successful_in_outer_report(setup_wrapper, status):
    calls, hit = setup_wrapper
    hit["report"]["stages"][0].update(status=status, reason="local model unavailable")
    # Some BLOCKED stages carry legacy output.ok=True; status is authoritative.
    result = breakthrough.full_orchestrate(breakthrough=False)
    assert result["lyrics"]["ok"] is False
    assert result["lyrics"]["stage_status"] == status
    assert result["lyrics"]["stage_reason"] == "local model unavailable"
    assert result["ok"] is False


def test_absent_stage_has_no_fabricated_lyrics_or_beat(setup_wrapper):
    calls, hit = setup_wrapper
    hit["report"]["stages"] = []
    result = breakthrough.full_orchestrate(breakthrough=False)
    assert not result["lyrics"]["ok"] and not result["beats"]["ok"]
    assert "unavailable" in result["lyrics"]["reason"]
