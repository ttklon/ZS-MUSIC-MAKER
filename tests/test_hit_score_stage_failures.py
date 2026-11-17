"""Scoring failures must not become a successful synthetic hit rating."""
import numpy as np
import pytest

from app.core.stages.master import _stage_hit_score
from modules.dsp.wavio import write_wav


def test_missing_entry_point_does_not_invent_score(monkeypatch):
    from modules import hit_scorer

    for name in ("score_track", "score", "evaluate"):
        monkeypatch.setattr(hit_scorer, name, None, raising=False)
    result = _stage_hit_score("unused.wav")
    assert result["ok"] is False
    assert "no scoring entry" in result["reason"]
    assert "hit_score" not in result
    assert result.get("verdict") != "solid"


def test_silent_file_is_failed_stage(tmp_path):
    path = tmp_path / "silence.wav"
    write_wav(path, np.zeros((22050, 2), dtype=np.float32), 22050)
    result = _stage_hit_score(str(path))
    assert result["ok"] is False
    assert result["verdict"] == "invalid_audio"
    assert result["hit_score"] == 0
    assert result["reason"]


@pytest.mark.parametrize("response", [None, [], "solid", 60])
def test_bad_scorer_response_is_failure(monkeypatch, response):
    monkeypatch.setattr("modules.hit_scorer.score_track", lambda path: response)
    result = _stage_hit_score("unused.wav")
    assert result["ok"] is False
    assert "bad return type" in result["reason"]


def test_missing_audio_is_failed_stage(tmp_path):
    result = _stage_hit_score(str(tmp_path / "missing.wav"))
    assert result["ok"] is False
    assert "file not found" in result["reason"]
