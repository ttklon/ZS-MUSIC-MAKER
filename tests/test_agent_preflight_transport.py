"""The Electron task's terminal event preserves setup and resource refusal."""
import json
from types import SimpleNamespace


def test_setup_summary_cannot_promote_a_worker_probe_to_inference():
    from app.cli.agent_task import _preparation_summary

    summary = _preparation_summary({
        "ok": True, "blockers": [],
        "worker_protocol": {"ok": True, "profile": "core", "isolated": True,
                             "inference_verified": True},
    })
    assert summary["ok"] is True
    assert summary["inference_verified"] is False
    assert summary["worker_protocol"]["inference_verified"] is False


def test_agent_task_forwards_preparation_and_preflight_to_terminal_record(monkeypatch, capsys):
    from app.cli import agent_task
    import modules.agent_guide as guide

    preparation = {
        "ok": False,
        "blockers": ["optional engine unavailable"],
        "readiness_before": 40,
        "readiness_after": 41,
        "worker_protocol": {"ok": True, "profile": "core", "isolated": True,
                             "inference_verified": False},
    }
    preflight = {
        "schema": 1, "status": "blocked", "scope": "selected_beat_engine",
        "engine": "musicgen", "reasons": ["ram_available_gib: resource unknown or insufficient"],
        "inference_verified": False, "product_profile_accepted": False,
    }
    captured = {}
    monkeypatch.setattr("app.core.net_policy.network_allowed", lambda **_kwargs: False)
    monkeypatch.setattr(agent_task, "_prepare", lambda _online: preparation)
    def run(*args, **kwargs):
        captured.update(kwargs)
        return {"master_path": None, "blocked": [{"stage": "hardware_preflight", "reason": "not enough RAM"}],
                "hardware_preflight": preflight}
    monkeypatch.setattr(guide, "run_conversation_hit", run)
    monkeypatch.setattr(guide, "narrate", lambda _report: "preflight refused")

    assert agent_task.run_agent_hit(SimpleNamespace(online=False, agent_output="")) == 1
    assert captured["preparation"]["ok"] is False
    assert captured["preparation"]["readiness_after"] == 41
    assert captured["preparation"]["worker_protocol"]["inference_verified"] is False
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines() if line.startswith("{")]
    terminal = next(event for event in events if event["type"] == "done")
    assert terminal["report"]["preparation"]["ok"] is False
    assert terminal["report"]["hardware_preflight"]["status"] == "blocked"
    assert terminal["report"]["result"]["succeeded"] is False


def test_agent_cli_to_shared_recipe_stops_before_model_work_and_reports_refusal(monkeypatch, tmp_path, capsys):
    from app.cli import agent_task
    from app.core import hardware_preflight
    from modules.agent_guide import runner
    from modules.hit_factory import adaptive

    preparation = {
        "ok": False, "blockers": ["MusicGen package unavailable"],
        "readiness_before": 54, "readiness_after": 54,
        "worker_protocol": {"ok": True, "profile": "core", "isolated": True,
                             "inference_verified": False},
    }
    inventory = {
        "kind": "inventory_only",
        "measurements": {
            "ram_available_gib": 4, "ram_available_bytes": 4 * 1024 ** 3,
            "disk_free_gib": 2, "disk_free_bytes": 2 * 1024 ** 3,
            "gpu": {"backend": "cpu", "free_vram_gib": None, "free_vram_bytes": None,
                    "inference_verified": False},
        },
        "errors": [], "inference_verified": False, "product_profile_accepted": False,
    }
    monkeypatch.setattr("app.core.net_policy.network_allowed", lambda **_kwargs: False)
    monkeypatch.setattr(agent_task, "_prepare", lambda _online: preparation)
    monkeypatch.setattr(adaptive, "get_adaptive_config", lambda: {
        "use_musicgen": True, "musicgen_model": "facebook/musicgen-small", "musicgen_device": "cpu",
    })
    monkeypatch.setattr(runner, "_trend", lambda _theme: {"ok": True})
    monkeypatch.setattr(runner, "_references", lambda _paths: {"ok": True, "style_vector": {}})
    monkeypatch.setattr(hardware_preflight, "measure_profile", lambda _path: inventory)
    for name in ("_dossier", "_samples", "_lyrics", "_voice", "_run_pipeline"):
        monkeypatch.setattr(runner, name, lambda *a, _name=name, **kw: (_ for _ in ()).throw(
            AssertionError(f"{_name} must not run after a preflight refusal")))
    monkeypatch.setattr("modules.agent_guide.narrate", lambda _report: "hardware preflight blocked")

    assert agent_task.run_agent_hit(SimpleNamespace(
        online=False, agent_output=str(tmp_path), agent_mood="night drive", agent_artist="fixture",
        agent_refs="", agent_voice="",
    )) == 1
    records = [json.loads(line) for line in capsys.readouterr().out.splitlines() if line.startswith("{")]
    terminal = next(event for event in records if event["type"] == "done")
    assert terminal["ok"] is False
    assert terminal["report"]["preparation"]["blockers"] == ["MusicGen package unavailable"]
    assert terminal["report"]["hardware_preflight"]["status"] == "blocked"
    assert terminal["report"]["hardware_preflight"]["checks"]["ram_available_gib"]["allowed"] is False
    assert terminal["report"]["blocked"][0]["stage"] == "hardware_preflight"
