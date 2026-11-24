"""Installed Windows artifact check for the shared recipe and model-stage worker.

The first run measures the actual host and exercises the shipped orchestrator,
but replaces the renderer with a refusal stub so no model is loaded. The second
run deterministically tests the same recipe across a RAM denial/retry, again
without inference. A model-backed stage then times out in the isolated worker;
its delayed side effect must never appear after cancellation.
"""
from __future__ import annotations

import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any

_GIB = 1024 ** 3


def _recipe() -> dict[str, Any]:
    return {
        "beat_engine": "musicgen",
        "musicgen_model": "facebook/musicgen-small",
        "musicgen_device": "cpu",
        "duration_sec": 30,
        "genre": "drift_phonk",
        "theme": "installed hardware preflight contract check",
        "voice_mode": "off",
        "use_texture": False,
        "export_stems": False,
    }


def _inventory(ram_gib: int) -> dict[str, Any]:
    return {
        "schema": 1,
        "kind": "inventory_only",
        "measurements": {
            "ram_available_gib": ram_gib,
            "ram_available_bytes": ram_gib * _GIB,
            "disk_free_gib": 2,
            "disk_free_bytes": 2 * _GIB,
            "gpu": {
                "backend": "cpu",
                "free_vram_gib": None,
                "free_vram_bytes": None,
                "inference_verified": False,
            },
        },
        "errors": [],
        "inference_verified": False,
        "product_profile_accepted": False,
    }


def _stage_status(report: dict[str, Any], name: str) -> str | None:
    for row in report.get("stages", []):
        if row.get("name") == name:
            return row.get("status")
    return None


def run(project_root: Path, workspace: Path) -> dict[str, Any]:
    project_root = project_root.resolve()
    workspace = workspace.resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(project_root))

    from app.ai.registry import registry
    from app.ai.sequential_runner import AIStage, SequentialAIRunner
    from app.core import hardware_preflight, orchestrator
    from modules import beat_gen_musicgen

    orchestrator._attach_agent_context = lambda _recipe: {}
    recipe = _recipe()
    recipe_before_retry = json.dumps(recipe, sort_keys=True)
    render_calls: list[dict[str, Any]] = []

    def inference_disabled(*args, **kwargs):
        render_calls.append({"args": list(args[:2]), "kwargs": dict(kwargs)})
        return {
            "ok": False,
            "reason": "installed artifact contract probe: model inference intentionally disabled",
            "inference_verified": False,
        }

    original_renderer = beat_gen_musicgen.render_musicgen_beat
    original_measure = hardware_preflight.measure_profile
    beat_gen_musicgen.render_musicgen_beat = inference_disabled
    try:
        # This is the real installed inventory and the production shared recipe
        # route. A blocked outcome is a genuine refusal; an allowed result reaches
        # only the refusal stub above, never MusicGen or its model loader.
        actual = orchestrator.run_full_pipeline(
            "installed-hardware-preflight-observation",
            recipe,
            out_root=workspace / "actual-measurement-run",
            only={"beat"},
        )
        actual_gate = actual.get("hardware_preflight") or {}
        if actual_gate.get("status") not in {"allowed", "blocked"}:
            raise AssertionError(f"installed shared-recipe path did not report a gate: {actual_gate}")
        if actual_gate.get("inference_verified") is not False or actual_gate.get("product_profile_accepted") is not False:
            raise AssertionError("resource admission must not promote inference or product acceptance")
        actual_call_count = len(render_calls)
        if actual_gate["status"] == "blocked" and actual_call_count:
            raise AssertionError("the real measured refusal entered the MusicGen renderer")
        if actual_gate["status"] == "allowed" and actual_call_count != 1:
            raise AssertionError("allowed admission did not reach the disabled renderer boundary")

        # Same recipe, project id and output directory; only measured RAM changes.
        retry_root = workspace / "same-recipe-deny-retry"
        retry_root.mkdir(parents=True, exist_ok=True)
        previous_wav = retry_root / "previous-master.wav"
        previous_bytes = b"prior user result must survive a hardware refusal and retry"
        previous_wav.write_bytes(previous_bytes)
        measured = [_inventory(4)]
        hardware_preflight.measure_profile = lambda _directory: measured[0]
        render_calls.clear()
        denied = orchestrator.run_full_pipeline(
            "installed-same-recipe-retry",
            recipe,
            out_root=retry_root,
            only={"beat"},
        )
        if denied["hardware_preflight"].get("status") != "blocked" or render_calls:
            raise AssertionError("low-RAM shared recipe was not denied before the renderer")
        if previous_wav.read_bytes() != previous_bytes:
            raise AssertionError("hardware refusal changed the prior result")

        measured[0] = _inventory(64)
        retried = orchestrator.run_full_pipeline(
            "installed-same-recipe-retry",
            recipe,
            out_root=retry_root,
            only={"beat"},
        )
        if retried["hardware_preflight"].get("status") != "allowed":
            raise AssertionError(f"same recipe did not recover at the renderer boundary: {retried['hardware_preflight']}")
        if denied["hardware_preflight"].get("request") != retried["hardware_preflight"].get("request"):
            raise AssertionError("retry changed the selected engine/model/device/budget")
        if json.dumps(recipe, sort_keys=True) != recipe_before_retry:
            raise AssertionError("the caller-owned recipe changed between denial and retry")
        if len(render_calls) != 1:
            raise AssertionError("recovered admission did not reach exactly one disabled renderer")
        if (render_calls[0].get("kwargs", {}).get("model_name") != "facebook/musicgen-small"
                or render_calls[0].get("kwargs", {}).get("device") != "cpu"):
            raise AssertionError(f"renderer boundary did not receive the reviewed model/device: {render_calls[0]}")
        if (retried["hardware_preflight"].get("inference_verified") is not False
                or retried["hardware_preflight"].get("product_profile_accepted") is not False):
            raise AssertionError("the recovery probe must not claim model inference or product acceptance")
        if retried.get("master_path") is not None or retried.get("outcome", {}).get("status") == "success":
            raise AssertionError("a renderer refusal stub must not become a generated master")
        if previous_wav.read_bytes() != previous_bytes:
            raise AssertionError("retry changed the prior result")

        # Exercise the same isolated model-stage worker used by neural stages.
        # This packaged core profile intentionally has no MusicGen dependency or
        # weights, so the optional model stage takes its deterministic callable
        # path. It starts, exceeds its deadline, and must be killed on Windows.
        if registry.is_available("music_generation"):
            raise AssertionError("clean core installer unexpectedly contains MusicGen; refusing to load a model")
        started = workspace / "model-worker-started.txt"
        late = workspace / "model-worker-late-side-effect.txt"

        def delayed_model_stage(_handle, _context):
            started.write_text("worker reached the model stage", encoding="utf-8")
            time.sleep(7.0)
            late.write_text("worker survived cancellation", encoding="utf-8")
            return {"ok": True}

        runner = SequentialAIRunner(vram_probe=lambda: 0.0)
        runner.add(AIStage(
            "music_generation",
            "music_generation",
            delayed_model_stage,
            optional=True,
            timeout_sec=5.0,
        ))
        cancellation = runner.run().to_dict()
        if not started.is_file():
            raise AssertionError("model-stage worker never reached its running state before timeout")
        if cancellation["stages"][0].get("ok") is not False or "exceeded" not in (cancellation["stages"][0].get("error") or ""):
            raise AssertionError(f"model-stage timeout was not reported: {cancellation}")
        # If termination had only marked the task but left its process alive, its
        # delayed side effect would now have happened.
        time.sleep(2.5)
        if late.exists():
            raise AssertionError("timed-out model-stage worker continued running after cancellation")

        clean_nsis_context = platform.system() == "Windows" and os.environ.get("ZSMM_NSIS_INSTALL_CHECK") == "1"
        result = {
            "schema": 1,
            "scope": ("installed-current-user-NSIS-bundled-core-shared-recipe-no-model-inference"
                      if clean_nsis_context else "rehearsal-only-not-installed-evidence"),
            "host_os": platform.system(),
            "clean_nsis_install_context": clean_nsis_context,
            "inference_verified": False,
            "product_profile_accepted": False,
            "song_verified": False,
            "actual_measurement": {
                "status": actual_gate.get("status"),
                "engine": actual_gate.get("engine"),
                "request": actual_gate.get("request"),
                "measurements": actual_gate.get("measurements"),
                "checks": actual_gate.get("checks"),
                "reasons": actual_gate.get("reasons"),
                "inventory_errors": actual_gate.get("inventory_errors"),
                "pipeline_outcome": actual.get("outcome"),
                "renderer_calls": actual_call_count,
                "inference_verified": actual_gate.get("inference_verified"),
                "product_profile_accepted": actual_gate.get("product_profile_accepted"),
            },
            "same_recipe_retry": {
                "recipe_unchanged": True,
                "request_unchanged": True,
                "request_before_retry": denied["hardware_preflight"].get("request"),
                "request_after_retry": retried["hardware_preflight"].get("request"),
                "deny_status": denied["hardware_preflight"].get("status"),
                "deny_renderer_calls": 0,
                "retry_status": retried["hardware_preflight"].get("status"),
                "retry_renderer_calls": len(render_calls),
                "retry_pipeline_outcome": retried.get("outcome"),
                "prior_result_preserved": previous_wav.read_bytes() == previous_bytes,
                "inference_verified": retried["hardware_preflight"].get("inference_verified"),
                "product_profile_accepted": retried["hardware_preflight"].get("product_profile_accepted"),
            },
            "model_worker_cancellation": {
                "model_role": "music_generation",
                "worker_started": started.is_file(),
                "status": cancellation["stages"][0].get("status"),
                "error": cancellation["stages"][0].get("error"),
                "late_side_effect_absent": not late.exists(),
                "inference_verified": False,
            },
            "limitations": [
                "The actual-host run measures resources but substitutes a refusal stub at the inference boundary.",
                "The RAM deny/retry uses deterministic measurements in the installed pipeline; no model weights are loaded.",
                "This does not establish inference success, audio quality, or CPU/CUDA/AMD product support.",
            ],
        }
        destination = workspace / "hardware-preflight-installed.json"
        destination.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(json.dumps({
            "report": str(destination),
            "actual_status": actual_gate.get("status"),
            "retry": result["same_recipe_retry"],
            "model_worker_cancellation": result["model_worker_cancellation"],
            "inference_verified": False,
            "product_profile_accepted": False,
        }, ensure_ascii=False, indent=2, allow_nan=False))
        return result
    finally:
        hardware_preflight.measure_profile = original_measure
        beat_gen_musicgen.render_musicgen_beat = original_renderer


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: windows_installed_hardware_preflight.py PROJECT_ROOT USER_WORKSPACE", file=sys.stderr)
        return 2
    run(Path(sys.argv[1]), Path(sys.argv[2]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
