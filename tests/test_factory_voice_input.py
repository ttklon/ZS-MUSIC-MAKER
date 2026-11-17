"""A supplied --hit-voice must reach the recipe, not be discarded before TTS."""
import copy

import numpy as np
import pytest

from modules.dsp.wavio import write_wav


@pytest.fixture
def voice(tmp_path):
    path = tmp_path / "my-vocal.wav"
    write_wav(path, np.sin(np.arange(8000) * .1).astype("float32") * .1, 8000)
    return str(path)


@pytest.fixture
def factory(tmp_path, monkeypatch):
    from modules.hit_factory import generator

    monkeypatch.setattr(generator, "_maybe_auto_genre", lambda genre, theme: genre)
    monkeypatch.setattr("modules.hit_factory.kpi.build_kpi", lambda *a, **kw: {})
    return generator.HitFactory(output_root=tmp_path, adaptive=False, evolve=False, verbose=False)


@pytest.mark.parametrize("evolve", [False, True])
def test_voice_and_conversion_choice_survive_recipe_and_snapshot(factory, voice, tmp_path, monkeypatch, evolve):
    from app.core.recipe import build_recipe
    from app.core.project_snapshot import snapshot_recipe, restore_recipe
    from app.core.stages import vocal_chain

    observed = {}
    attempts = []
    monkeypatch.setattr(vocal_chain, "_stage_voice_synth", lambda *a: pytest.fail("supplied recording must bypass TTS"))
    monkeypatch.setattr(vocal_chain, "_stage_rvc", lambda *a, **kw: pytest.fail("conversion disabled"))
    monkeypatch.setattr(vocal_chain, "_stage_vocal_fx", lambda path, *a, **kw: {"ok": True, "path": path})

    def render(project_id, state, rng):
        attempts.append(copy.deepcopy(state))
        observed.update(copy.deepcopy(state))
        restored = restore_recipe({"desktop_recipe_snapshot": snapshot_recipe(state)})
        recipe = build_recipe(restored)
        stages, vocal, warnings = vocal_chain._run_vocal_chain(recipe, "ignored lyrics", tmp_path)
        assert vocal == voice
        assert stages[0].output["engine"] == "user_recording"
        return {"project_id": project_id, "out_root": str(tmp_path), "master_path": vocal,
                "hit_score": 50, "verdict": "needs_work", "report": {"verdict": "PARTIAL"}}

    monkeypatch.setattr(factory, "_run_pipeline_once", render)
    factory.make_one(genre="trap", theme="test", seed=42, own_vocal_wav=voice,
                     use_rvc=False, artist="My artist", evolve=evolve)
    assert observed["own_vocal_wav"] == voice
    assert observed["use_rvc"] is False
    assert observed["artist"] == "My artist"
    assert len(attempts) == (factory.max_attempts if evolve else 1)
    assert all(state["own_vocal_wav"] == voice and state["use_rvc"] is False for state in attempts)


def test_missing_explicit_recording_is_not_replaced_with_tts(factory, tmp_path, monkeypatch):
    from app.core.recipe import build_recipe
    from app.core.stages import vocal_chain

    monkeypatch.setattr(vocal_chain, "_stage_voice_synth", lambda *a: pytest.fail("cannot silently replace supplied voice"))

    def render(project_id, state, rng):
        stages, path, warnings = vocal_chain._run_vocal_chain(build_recipe(state), "text", tmp_path)
        assert path is None and stages[0].status.value == "FAILED"
        return {"project_id": project_id, "out_root": str(tmp_path), "master_path": None,
                "hit_score": 0, "verdict": "flop_risk", "report": {"verdict": "PARTIAL"}}

    monkeypatch.setattr(factory, "_run_pipeline_once", render)
    result = factory.make_one(genre="trap", theme="test", own_vocal_wav=str(tmp_path / "missing.wav"))
    assert not result["readiness"]["ready"]


def test_breakthrough_forwards_raw_voice_and_artist_without_double_conversion(voice, tmp_path, monkeypatch):
    from modules.hit_factory import breakthrough, generator

    calls = {}
    monkeypatch.setattr(breakthrough, "analyze_references", lambda *a: {"ok": False})
    monkeypatch.setattr(breakthrough, "build_artist_dossier", lambda *a: {})
    monkeypatch.setattr(breakthrough, "generate_lyrics_in_style", lambda *a: {"theme": "test"})
    monkeypatch.setattr(breakthrough, "generate_beats_with_style", lambda *a: {})
    monkeypatch.setattr(breakthrough, "_guard_memory", lambda: None)

    def prepare(path, use_rvc):
        assert path == voice and use_rvc is False
        return {"ok": True, "path": path, "source": "raw"}

    class Factory:
        def __init__(self, **kwargs):
            pass

        def make_one(self, *args, **kwargs):
            calls.update(kwargs)
            return {"master_path": voice, "hit_score": 90, "verdict": "solid",
                    "report": {"verdict": "PARTIAL"}}

    monkeypatch.setattr(breakthrough, "prepare_voice", prepare)
    monkeypatch.setattr(generator, "HitFactory", Factory)
    result = breakthrough.full_orchestrate(artist="My artist", raw_voice_path=voice,
                                  output_root=str(tmp_path), breakthrough=False)
    assert calls["own_vocal_wav"] == voice
    assert calls["use_rvc"] is True
    assert calls["artist"] == "My artist"

    assert result["ok"] is False
    assert result["readiness"]["ready"] is False
    assert result["master_created"] is True


def test_blank_explicit_voice_is_rejected_instead_of_becoming_tts(factory):
    with pytest.raises(ValueError, match="must not be blank"):
        factory.make_one(genre="trap", theme="test", own_vocal_wav="   ")


@pytest.mark.parametrize("inputs", [
    {"hit_voice": "my-vocal.wav"}, {"hit_refs": "reference.wav"}, {"hit_artist": "My artist"},
])
def test_cli_failure_does_not_restart_without_explicit_inputs(monkeypatch, inputs):
    from types import SimpleNamespace
    from app.cli import hitfactory

    def fail(**kwargs):
        raise RuntimeError("preparation failed")

    monkeypatch.setattr("modules.hit_factory.breakthrough.full_orchestrate", fail)
    monkeypatch.setattr(hitfactory, "_run_standard_cli", lambda args: pytest.fail("would discard explicit inputs"))
    assert hitfactory.run_hit_factory(SimpleNamespace(hit_count=1, **inputs)) == 2


def test_plain_breakthrough_failure_may_still_use_standard_mode(monkeypatch):
    from types import SimpleNamespace
    from app.cli import hitfactory

    def fail(**kwargs):
        raise RuntimeError("preparation failed")

    monkeypatch.setattr("modules.hit_factory.breakthrough.full_orchestrate", fail)
    monkeypatch.setattr(hitfactory, "_run_standard_cli", lambda args: 0)
    assert hitfactory.run_hit_factory(SimpleNamespace(hit_count=1, hit_breakthrough=True)) == 0
