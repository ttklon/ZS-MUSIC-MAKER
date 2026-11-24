"""Resource admission checks are measured guards, not inference evidence."""
from app.ai.profiles import preflight_resources
from app.core import hardware_preflight
from app.core.download_budget import RESERVE_BYTES

_GIB = 1024 ** 3


def _inventory(ram_gib=32, disk_gib=4, vram_gib=None):
    return {
        "kind": "inventory_only",
        "measurements": {
            "ram_available_gib": ram_gib,
            "ram_available_bytes": int(ram_gib * _GIB) if ram_gib is not None else None,
            "disk_free_gib": disk_gib,
            "disk_free_bytes": int(disk_gib * _GIB) if disk_gib is not None else None,
            "gpu": {
                "backend": "cuda" if vram_gib is not None else "cpu",
                "free_vram_gib": vram_gib,
                "free_vram_bytes": int(vram_gib * _GIB) if vram_gib is not None else None,
                "inference_verified": False,
            },
        },
        "errors": [],
        "inference_verified": False,
        "product_profile_accepted": False,
    }


def test_musicgen_requires_measured_budget_and_records_exact_pcm_disk_bound(monkeypatch, tmp_path):
    inventory = _inventory(ram_gib=15, disk_gib=2)
    monkeypatch.setattr(hardware_preflight, "measure_profile", lambda _path: inventory)
    report = hardware_preflight.preflight_recipe({
        "beat_engine": "musicgen", "musicgen_model": "small", "musicgen_device": "cpu",
        "duration_sec": 30,
    }, tmp_path)
    assert report["status"] == "allowed"
    assert report["request"]["model"] == "facebook/musicgen-small"
    assert report["request"]["required_ram_gib"] == 15
    assert report["request"]["required_disk_bytes"] == RESERVE_BYTES + 30 * 32_000 * 2 * 2 + 44
    assert report["request"]["checkpoint_cache_size_known"] is False
    assert "checkpoint/cache size is unknown" in report["scope_note"]
    assert report["inference_verified"] is False and report["product_profile_accepted"] is False


def test_musicgen_low_ram_or_unknown_measurement_is_denied(monkeypatch, tmp_path):
    inventory = _inventory(ram_gib=4, disk_gib=2)
    monkeypatch.setattr(hardware_preflight, "measure_profile", lambda _path: inventory)
    report = hardware_preflight.preflight_recipe({
        "beat_engine": "musicgen", "musicgen_device": "cpu", "duration_sec": 30,
    }, tmp_path)
    assert report["status"] == "blocked"
    assert report["checks"]["ram_available_gib"]["allowed"] is False
    assert report["reasons"]

    unknown = _inventory(ram_gib=None, disk_gib=2)
    monkeypatch.setattr(hardware_preflight, "measure_profile", lambda _path: unknown)
    report = hardware_preflight.preflight_recipe({"beat_engine": "musicgen"}, tmp_path)
    assert report["status"] == "blocked"
    assert report["checks"]["ram_available_gib"]["available_bytes"] is None

    invalid = _inventory(ram_gib=8, disk_gib=2)
    invalid["measurements"]["ram_available_gib"] = float("nan")
    invalid["measurements"]["ram_available_bytes"] = None
    monkeypatch.setattr(hardware_preflight, "measure_profile", lambda _path: invalid)
    report = hardware_preflight.preflight_recipe({"beat_engine": "musicgen"}, tmp_path)
    assert report["status"] == "blocked"
    assert report["measurements"]["ram_available_gib"] is None
    import json
    json.dumps(report, allow_nan=False)


def test_musicgen_disk_gate_enforces_reserve_and_pcm_bound_in_exact_bytes(monkeypatch, tmp_path):
    inventory = _inventory(ram_gib=16, disk_gib=2)
    required = RESERVE_BYTES + 30 * 32_000 * 2 * 2 + 44
    inventory["measurements"]["disk_free_bytes"] = required - 1
    inventory["measurements"]["disk_free_gib"] = 2  # stale display value cannot override exact bytes
    monkeypatch.setattr(hardware_preflight, "measure_profile", lambda _path: inventory)
    denied = hardware_preflight.preflight_recipe({
        "beat_engine": "musicgen", "musicgen_device": "cpu", "duration_sec": 30,
    }, tmp_path)
    assert denied["status"] == "blocked"
    assert denied["checks"]["disk_free_gib"]["required_bytes"] >= required
    assert denied["checks"]["disk_free_gib"]["available_bytes"] == required - 1

    inventory["measurements"]["disk_free_bytes"] = required
    admitted = hardware_preflight.preflight_recipe({
        "beat_engine": "musicgen", "musicgen_device": "cpu", "duration_sec": 30,
    }, tmp_path)
    assert admitted["status"] == "allowed"


def test_gpu_route_requires_free_vram_plus_reserve(monkeypatch, tmp_path):
    inventory = _inventory(ram_gib=32, disk_gib=2, vram_gib=11.5)
    monkeypatch.setattr(hardware_preflight, "measure_profile", lambda _path: inventory)
    report = hardware_preflight.preflight_recipe({
        "beat_engine": "musicgen", "musicgen_device": "cuda", "duration_sec": 30,
    }, tmp_path)
    assert report["status"] == "blocked"
    assert report["request"]["required_vram_gib"] == 12
    assert report["checks"]["gpu.free_vram_gib"]["allowed"] is False


def test_gpu_route_rejects_incompatible_or_unknown_backend_even_with_vram(monkeypatch, tmp_path):
    inventory = _inventory(ram_gib=32, disk_gib=2, vram_gib=16)
    inventory["measurements"]["gpu"]["backend"] = "directml"
    monkeypatch.setattr(hardware_preflight, "measure_profile", lambda _path: inventory)
    report = hardware_preflight.preflight_recipe({
        "beat_engine": "musicgen", "musicgen_device": "cuda", "duration_sec": 30,
    }, tmp_path)
    assert report["status"] == "blocked"
    assert report["checks"]["gpu.backend"]["allowed"] is False
    assert report["checks"]["gpu.free_vram_gib"]["allowed"] is True
    assert "incompatible" in report["reasons"][-1]


def test_gpu_route_accepts_only_a_measured_torch_cuda_or_rocm_backend(monkeypatch, tmp_path):
    inventory = _inventory(ram_gib=32, disk_gib=2, vram_gib=16)
    inventory["measurements"]["gpu"]["backend"] = "rocm"
    monkeypatch.setattr(hardware_preflight, "measure_profile", lambda _path: inventory)
    report = hardware_preflight.preflight_recipe({
        "beat_engine": "musicgen", "musicgen_device": "cuda", "duration_sec": 30,
    }, tmp_path)
    assert report["status"] == "allowed"
    assert report["checks"]["gpu.backend"]["allowed"] is True


def test_invalid_model_catalog_budgets_are_not_coerced_into_admission(monkeypatch, tmp_path):
    from app.ai import model_catalog

    inventory = _inventory(ram_gib=32, disk_gib=2)
    monkeypatch.setattr(hardware_preflight, "measure_profile", lambda _path: inventory)
    for invalid in ("14", True, float("nan"), float("inf"), 0, -1):
        monkeypatch.setattr(model_catalog, "MODEL_REGISTRY", {
            "music_generation": {"ram_est_gb": invalid, "vram_est_gb": 11},
        })
        report = hardware_preflight.preflight_recipe({"beat_engine": "musicgen"}, tmp_path)
        assert report["status"] == "blocked"
        assert "estimate unavailable" in report["reasons"][0]

        monkeypatch.setattr(model_catalog, "MODEL_REGISTRY", {
            "music_generation": {"ram_est_gb": 14, "vram_est_gb": invalid},
        })
        report = hardware_preflight.preflight_recipe({
            "beat_engine": "musicgen", "musicgen_device": "cuda",
        }, tmp_path)
        assert report["status"] == "blocked"
        assert "estimate unavailable" in report["reasons"][0]


def test_exact_byte_measurements_prevent_rounded_up_false_admission():
    inventory = _inventory(ram_gib=2, disk_gib=2)
    inventory["measurements"]["ram_available_gib"] = 8.0  # stale/display-only value
    inventory["measurements"]["ram_available_bytes"] = _GIB - 1
    result = preflight_resources(inventory, ram_gib=1, disk_gib=1)
    assert not result["allowed"]
    assert result["checks"]["ram_available_gib"]["available_bytes"] == _GIB - 1


def test_rounded_gib_compatibility_value_is_rounded_down_conservatively():
    profile = {"measurements": {"ram_available_gib": 1.0, "disk_free_gib": 1.0}}
    result = preflight_resources(profile, ram_gib=1, disk_gib=1)
    assert not result["allowed"]
    assert result["checks"]["ram_available_gib"]["available_bytes"] < _GIB

    # A legacy provider may include the new byte key as null while retaining a
    # real rounded measurement; non-null malformed exact data never falls back.
    profile["measurements"].update(ram_available_bytes=None, disk_free_bytes=None,
                                   ram_available_gib=8.0, disk_free_gib=8.0)
    assert preflight_resources(profile, ram_gib=1, disk_gib=1)["allowed"]
    profile["measurements"]["ram_available_bytes"] = True
    assert not preflight_resources(profile, ram_gib=1, disk_gib=1)["allowed"]


def test_procedural_and_unmeasured_external_routes_are_not_mislabeled_as_admitted(monkeypatch, tmp_path):
    inventory = _inventory()
    monkeypatch.setattr(hardware_preflight, "measure_profile", lambda _path: inventory)
    procedural = hardware_preflight.preflight_recipe({"beat_engine": "procedural"}, tmp_path)
    assert procedural["status"] == "not_required"
    assert procedural["inference_verified"] is False
    external = hardware_preflight.preflight_recipe({"beat_engine": "ace_step"}, tmp_path)
    assert external["status"] == "blocked"
    assert external["request"]["resource_profile"] == "external_unmeasured"
    assert "fail closed" in external["reasons"][0]
    assert external["inference_verified"] is False


def test_unknown_model_device_and_invalid_duration_fail_closed(monkeypatch, tmp_path):
    inventory = _inventory()
    monkeypatch.setattr(hardware_preflight, "measure_profile", lambda _path: inventory)
    for recipe in (
        {"beat_engine": "musicgen", "musicgen_model": "custom/unmeasured"},
        {"beat_engine": "musicgen", "musicgen_device": "directml"},
        {"beat_engine": "musicgen", "duration_sec": True},
        {"beat_engine": "musicgen", "duration_sec": False},
        {"beat_engine": "musicgen", "duration_sec": 0},
        {"beat_engine": "musicgen", "duration_sec": -1},
    ):
        assert hardware_preflight.preflight_recipe(recipe, tmp_path)["status"] == "blocked"
    assert hardware_preflight.preflight_recipe(
        {"beat_engine": "musicgen"}, tmp_path, dry_run=True)["status"] == "not_required"


def test_normalized_recipe_preserves_selected_values_and_does_not_hide_invalid_choices(monkeypatch, tmp_path):
    from app.core.recipe import build_recipe

    recipe = build_recipe({
        "beat_engine": "musicgen", "musicgen_model": "medium",
        "musicgen_device": "cuda",
    })
    assert recipe["musicgen_model"] == "facebook/musicgen-medium"
    assert recipe["musicgen_device"] == "cuda"

    inventory = _inventory()
    monkeypatch.setattr(hardware_preflight, "measure_profile", lambda _path: inventory)
    for state in (
        {"beat_engine": "musicgen", "musicgen_model": ""},
        {"beat_engine": "musicgen", "musicgen_device": ""},
        {"beat_engine": ""},
        {"beat_engine": "musicgen", "musicgen_model": 0},
        {"beat_engine": "musicgen", "duration_sec": True},
        {"beat_engine": "musicgen", "duration_sec": 30.0},
        {"beat_engine": "musicgen", "duration_sec": "30"},
    ):
        normalized = build_recipe(state)
        assert hardware_preflight.preflight_recipe(normalized, tmp_path)["status"] == "blocked"


def test_musicgen_stage_normalizes_artifact_path_and_dry_run_never_loads(monkeypatch, tmp_path):
    from app.core.stages import beat
    from modules import beat_gen_musicgen

    calls = []
    monkeypatch.setattr(beat_gen_musicgen, "render_musicgen_beat", lambda *args, **kwargs: (
        calls.append((args, kwargs)) or {"ok": True, "beat_path": str(tmp_path / "beat.wav")}
    ))
    recipe = {"beat_engine": "musicgen", "musicgen_model": "facebook/musicgen-small",
              "musicgen_device": "cpu", "genre": "house", "theme": "night"}
    result = beat._stage_ai_beat(recipe, {"duration_sec": 30}, tmp_path, {"target_bpm": 120})
    assert result["path"] == str(tmp_path / "beat.wav")
    assert len(calls) == 1
    dry = beat._stage_ai_beat(recipe, {}, tmp_path, {}, dry_run=True)
    assert dry["blocked"] is True and len(calls) == 1
