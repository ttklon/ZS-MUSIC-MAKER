"""The agent/HitFactory shared recipe reaches a fail-closed gate before beat inference."""
import json
from pathlib import Path

from app.core import hardware_preflight, orchestrator

_GIB = 1024 ** 3


def _inventory(ram_gib):
    return {
        "kind": "inventory_only",
        "measurements": {
            "ram_available_gib": ram_gib,
            "ram_available_bytes": int(ram_gib * _GIB),
            "disk_free_gib": 2,
            "disk_free_bytes": 2 * _GIB,
            "gpu": {"backend": "cpu", "free_vram_gib": None, "free_vram_bytes": None,
                             "inference_verified": False},
        },
        "errors": [], "inference_verified": False, "product_profile_accepted": False,
    }


def test_same_musicgen_recipe_is_denied_then_retried_through_pipeline(tmp_path, monkeypatch):
    inventory = {"current": _inventory(4)}
    monkeypatch.setattr(hardware_preflight, "measure_profile", lambda _path: inventory["current"])
    monkeypatch.setattr(orchestrator, "_attach_agent_context", lambda _recipe: {})

    from modules import beat_gen_musicgen
    calls = []
    monkeypatch.setattr(beat_gen_musicgen, "render_musicgen_beat", lambda *args, **kwargs: (
        calls.append((args, kwargs)) or {
            "ok": True, "beat_path": str(tmp_path / "beat.wav"),
            "engine": "musicgen:fixture", "inference_verified": False,
        }
    ))

    request = {
        "beat_engine": "musicgen", "musicgen_model": "small",
        "musicgen_device": "cpu", "duration_sec": 30, "voice_mode": "off",
        "use_texture": False, "export_stems": False,
    }
    prior_root = tmp_path / "run"
    prior_root.mkdir()
    prior_master = prior_root / "previous-master.wav"
    prior_master.write_bytes(b"existing artifact must survive refusal and retry")
    prior_contents = prior_master.read_bytes()
    events = []
    denied = orchestrator.run_full_pipeline(
        "same-recipe", request, out_root=tmp_path / "run", only={"beat"},
        on_stage=lambda *row: events.append(row),
    )
    assert denied["hardware_preflight"]["status"] == "blocked"
    assert denied["outcome"]["status"] == "blocked"
    assert all(row["status"] == "BLOCKED" for row in denied["stages"])
    assert len(events) == len(orchestrator.STAGE_RECORDS)
    assert calls == []
    persisted = json.loads((tmp_path / "run" / "report.json").read_text(encoding="utf-8"))
    assert persisted["hardware_preflight"]["status"] == "blocked"
    assert prior_master.read_bytes() == prior_contents

    # No recipe, path or engine changes: only measured available RAM recovers.
    inventory["current"] = _inventory(16)
    accepted = orchestrator.run_full_pipeline(
        "same-recipe", request, out_root=tmp_path / "run", only={"beat"},
    )
    assert accepted["hardware_preflight"]["status"] == "allowed"
    beat = next(row for row in accepted["stages"] if row["name"] == "_stage_beat")
    assert beat["status"] == "OK"
    assert beat["output"]["path"] == str(tmp_path / "beat.wav")
    assert len(calls) == 1
    assert calls[0][1]["model_name"] == "facebook/musicgen-small"
    assert accepted["hardware_preflight"]["inference_verified"] is False
    assert prior_master.read_bytes() == prior_contents


def test_direct_hitfactory_make_one_reaches_the_shared_preflight(tmp_path, monkeypatch):
    from modules.hit_factory.generator import HitFactory
    from modules import beat_gen_musicgen

    monkeypatch.setattr(hardware_preflight, "measure_profile", lambda _path: _inventory(4))
    calls = []
    monkeypatch.setattr(beat_gen_musicgen, "render_musicgen_beat", lambda *a, **kw: (
        calls.append((a, kw)) or {"ok": False, "reason": "must be blocked earlier"}
    ))
    factory = HitFactory(output_root=tmp_path / "hits", adaptive=False, evolve=False,
                         duration_sec=30, verbose=False)
    hit = factory.make_one(recipe={
        "beat_engine": "musicgen", "musicgen_model": "facebook/musicgen-small",
        "musicgen_device": "cpu", "duration_sec": 30, "genre": "house",
        "theme": "night drive", "voice_mode": "off", "export_stems": False,
    })
    assert hit["report"]["hardware_preflight"]["status"] == "blocked"
    assert hit["report"]["outcome"]["status"] == "blocked"
    assert hit["master_path"] is None
    assert calls == []
    assert (Path(hit["out_root"]) / "report.json").is_file()


def test_agent_shared_recipe_refuses_before_lyrics_or_dossier_model_work(tmp_path, monkeypatch):
    from modules.agent_guide import runner
    from modules.hit_factory import adaptive

    monkeypatch.setattr(adaptive, "get_adaptive_config", lambda: {
        "use_musicgen": True, "musicgen_model": "facebook/musicgen-small", "musicgen_device": "cpu",
    })
    monkeypatch.setattr(runner, "_trend", lambda _theme: {"ok": True})
    monkeypatch.setattr(runner, "_references", lambda _paths: {"ok": True, "style_vector": {}})
    monkeypatch.setattr(hardware_preflight, "measure_profile", lambda _path: _inventory(4))
    for name in ("_dossier", "_samples", "_lyrics", "_voice", "_run_pipeline"):
        monkeypatch.setattr(runner, name, lambda *a, _name=name, **kw: (_ for _ in ()).throw(
            AssertionError(f"{_name} must not run after a preflight refusal")))

    report = runner.run_conversation_hit(
        {"mood": "night drive", "artist": "fixture"},
        output_root=str(tmp_path),
        preparation={"schema": 1, "ok": True, "blockers": [], "inference_verified": False},
    )
    assert report["plan"]["beat_engine"] == "musicgen"
    assert report["hardware_preflight"]["status"] == "blocked"
    assert report["preparation"]["ok"] is True
    assert report["blocked"][0]["stage"] == "hardware_preflight"
